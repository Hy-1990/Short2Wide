"""Local <5 minute video workflow. Model calls use the installed DreamAPI scripts."""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

DATA = Path.home() / '.local' / 'share' / 'reframe-studio' / 'projects'
SCRIPT = Path(__file__).resolve().parent / 'scripts' / 'dreamapi.py'
CONFIG = Path.home() / '.config' / 'reframe-studio' / 'dreamapi.json'
POOL = ThreadPoolExecutor(max_workers=2)
LOCK = threading.RLock()
PREVIEW_LOCK = threading.Lock()
ACTIVE = set()
MAX_BYTES = 512 * 1024 * 1024


class WorkflowError(Exception):
    pass


def run(args, timeout=300):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise WorkflowError('媒体处理失败：' + result.stderr[-600:])
    return result.stdout


def probe(path):
    data = json.loads(run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov,matroska,webm,avi,mpegts,mpeg,flv,ogg,gif,apng', '-show_format', '-show_streams', '-of', 'json', path]))
    video = next((s for s in data['streams'] if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic')), None)
    if not video:
        raise WorkflowError('文件中没有可读取的视频画面。')
    duration = float(video.get('duration') or data['format'].get('duration', 0))
    if not math.isfinite(duration) or duration <= 0:
        raise WorkflowError('无法读取视频时长。')
    return {'duration': duration, 'width': video['width'], 'height': video['height'], 'audio': any(s['codec_type'] == 'audio' for s in data['streams'])}


def folder(project_id):
    if not re.fullmatch(r'[0-9a-f]{32}', project_id):
        raise WorkflowError('项目不存在。')
    return DATA / project_id


def load(project_id):
    with LOCK:
        try:
            return json.loads((folder(project_id) / 'project.json').read_text())
        except FileNotFoundError:
            raise WorkflowError('项目不存在。')


def save(project):
    with LOCK:
        destination = folder(project['id']) / 'project.json'
        temp = destination.with_suffix('.tmp')
        temp.write_text(json.dumps(project, ensure_ascii=False, indent=2))
        temp.replace(destination)


def mutate(project_id, **values):
    with LOCK:
        project = load(project_id)
        project.update(values)
        save(project)
        return project


def shot_update(project_id, index, **values):
    with LOCK:
        project = load(project_id)
        project['shots'][index].update(values)
        # Any changed shot invalidates an earlier assembled export.
        project['export_ready'] = False
        save(project)
        return project


def public(project):
    result = dict(project)
    result['busy'] = project['id'] in ACTIVE
    result['configured'] = CONFIG.is_file()
    if result['status'] == 'importing' and not result['busy']:
        result.update(status='failed', error='导入已中断，请返回首页重新导入。')
    for shot in result.get('shots', []):
        if shot['status'] in ('generating', 'uploading', 'processing') and not result['busy']:
            shot['status'] = 'resumable' if shot.get('task_id') else 'interrupted'
    return result


def start(project_id, function, *args):
    with LOCK:
        if project_id in ACTIVE:
            raise WorkflowError('这个项目仍在处理，请等待当前步骤完成。')
        ACTIVE.add(project_id)
        mutate(project_id, error='', operation=function.__name__, operation_started=time.time())
    def worker():
        try:
            function(project_id, *args)
        except Exception as error:
            mutate(project_id, error=str(error)[:1000])
        finally:
            with LOCK:
                ACTIVE.discard(project_id)
    POOL.submit(worker)


def create(name, ratio):
    if ratio not in ('16:9', '9:16'):
        raise WorkflowError('请选择横屏或竖屏。')
    project_id = uuid.uuid4().hex
    directory = folder(project_id)
    directory.mkdir(parents=True, mode=0o700)
    project = {'id': project_id, 'name': Path(name).name[:180] or 'Video', 'ratio': ratio, 'status': 'importing', 'message': '导入视频…', 'shots': [], 'created': time.time(), 'error': '', 'export_ready': False}
    save(project)
    return project


def valid_link(value):
    try:
        u = urlsplit(value)
        return u.scheme == 'https' and not u.username and not u.password and u.port in (None, 443) and (u.hostname in ('youtu.be', 'youtube.com', 'tiktok.com') or (u.hostname or '').endswith(('.youtube.com', '.tiktok.com')))
    except ValueError:
        return False


def import_link(project_id, url):
    if not valid_link(url):
        raise WorkflowError('请使用 YouTube 或 TikTok 视频链接。')
    path = folder(project_id)
    try:
        mutate(project_id, message='下载视频…')
        run([sys.executable, '-m', 'yt_dlp', '--no-playlist', '--no-warnings', '--max-filesize', '512M', '--match-filter', 'duration < 300', '--no-write-info-json', '--no-write-thumbnail', '--merge-output-format', 'mp4', '-f', 'bv*[height<=1080]+ba/b[height<=1080]', '-o', str(path / 'download.%(ext)s'), '--', url], timeout=240)
        files = [f for f in path.glob('download.*') if f.suffix in ('.mp4', '.mkv', '.webm', '.mov')]
        if len(files) != 1:
            raise WorkflowError('下载未完成；视频可能受登录限制或不小于5分钟。可以改用本地文件。')
        files[0].rename(path / 'input.media')
        prepare(project_id)
    except Exception as error:
        mutate(project_id, status='failed', error=str(error)[:1000])


def plan_segments(duration, candidates, maximum=12, minimum=4):
    if not 0 < duration < 300:
        raise WorkflowError('请使用小于5分钟的视频。')
    if duration < 4:
        return [(0.0, duration)]
    points = [0.0]
    while duration - points[-1] > maximum:
        start = points[-1]
        upper = min(start + maximum, duration - minimum)
        available = [p for p in candidates if start + minimum <= p <= upper]
        target = start + 10
        cut = min(available, key=lambda p: abs(p - target)) if available else upper
        points.append(round(cut * 30) / 30)
    points.append(duration)
    return [(points[i], points[i + 1]) for i in range(len(points) - 1)]


def prepare(project_id):
    path = folder(project_id)
    try:
        metadata = probe(path / 'input.media')
        if metadata['duration'] >= 300:
            raise WorkflowError('视频必须小于5分钟，请先截取后再导入。')
        mutate(project_id, message='读取画面与音频…', **metadata)
        # Browser-compatible source, preserving the original file separately for final audio.
        run(['ffmpeg', '-y', '-v', 'error', '-i', path / 'input.media', '-map', '0:v:0', '-map', '0:a:0?', '-vf', "scale=1280:1280:force_original_aspect_ratio=decrease:force_divisible_by=2", '-c:v', 'libx264', '-preset', 'fast', '-crf', '21', '-c:a', 'aac', '-movflags', '+faststart', path / 'source.mp4'])
        mutate(project_id, message='按画面变化和停顿分段…')
        scene = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(path / 'source.mp4'), '-vf', "scale=320:-2,select='gt(scene,0.32)',showinfo", '-an', '-f', 'null', '-'], capture_output=True, text=True, timeout=180)
        candidates = [float(x) for x in re.findall(r'pts_time:([0-9.]+)', scene.stderr)]
        if metadata['audio']:
            silence = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(path / 'source.mp4'), '-af', 'silencedetect=noise=-32dB:d=0.25', '-vn', '-f', 'null', '-'], capture_output=True, text=True, timeout=90)
            candidates += [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', silence.stderr)]
        ranges = plan_segments(metadata['duration'], candidates)
        shots = []
        for index, (begin, end) in enumerate(ranges):
            prefix = f'shot-{index}'
            duration = end - begin
            width, height = (1280, 720) if metadata['width'] >= metadata['height'] else (720, 1280)
            # Normalize reference canvas and frame rate to the provider limits.
            run(['ffmpeg', '-y', '-v', 'error', '-ss', begin, '-i', path / 'source.mp4', '-t', duration, '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=4', '-t', max(4, duration), '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-c:a', 'aac', '-movflags', '+faststart', path / f'{prefix}-reference.mp4'])
            run(['ffmpeg', '-y', '-v', 'error', '-ss', begin, '-i', path / 'source.mp4', '-frames:v', '1', '-vf', 'scale=240:-2', path / f'{prefix}.jpg'])
            shots.append({'index': index, 'start': begin, 'end': end, 'duration': duration, 'status': 'ready', 'task_id': '', 'prompt': '', 'anchors': [], 'reviewed': False, 'error': ''})
            mutate(project_id, message=f'准备片段 {index + 1}/{len(ranges)}…')
        mutate(project_id, status='ready', message='可以先生成一个片段。', shots=shots, error='')
    except Exception as error:
        mutate(project_id, status='failed', error=str(error)[:1000])


def model_call(project_id, index, resume):
    project = load(project_id)
    shot = project['shots'][index]
    path = folder(project_id)
    started = False
    try:
        key = json.loads(CONFIG.read_text())['api_key']
        env = {**os.environ, 'DREAMAPI_API_KEY': key, 'PYTHONDONTWRITEBYTECODE': '1'}
        if resume:
            args = [sys.executable, str(SCRIPT), 'seedance-2.5', 'query', '--task-id', shot['task_id'], '--timeout', '900', '--json']
        else:
            prompt = f'将参考视频改编为{project["ratio"]}画幅。保留原片主体、镜头顺序和所有可见文字数字，按原时间点呈现动作、字幕与图形动效，不增加或删去事件。不要改写原有内容，保持原有时序。最终会使用原片音轨，请让画面动作与原音对应。' + shot['prompt']
            args = [sys.executable, str(SCRIPT), 'seedance-2.5', 'run', '--videos', str(path / f'shot-{index}-reference.mp4'), '--prompt', prompt[:1500], '--ratio', project['ratio'], '--resolution', '720p', '--duration', str(max(4, min(30, math.ceil(shot['duration'])))), '--timeout', '900', '--json']
            if shot.get('generate_audio', True):
                args.append('--generate-audio')
        args = [args[0], str(Path(__file__).with_name('dream_worker.py')), *args[1:]]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        started = True
        output = []
        reader = threading.Thread(target=lambda: output.append(process.stdout.read()), daemon=True)
        reader.start()
        errors = []; failure_kind = 'unknown'; failure_message = ''
        for line in process.stderr:
            errors.append(line)
            if line.startswith('REFRAME_EVENT '):
                try:
                    event = json.loads(line[len('REFRAME_EVENT '):]); failure_kind = event['kind']; failure_message = event.get('message', '')
                except (ValueError, KeyError): pass
            match = re.search(r'taskId:\s*(\S+)', line)
            if match:
                shot_update(project_id, index, task_id=match.group(1), status='generating')
        process.wait(); reader.join()
        process.stdout.close(); process.stderr.close()
        saved = load(project_id)['shots'][index]
        if process.returncode:
            diagnostic = (failure_message or ''.join(errors)[-700:]).replace(key, '[redacted]')
            if saved.get('task_id'):
                status = 'failed' if failure_kind == 'terminal_failed' else 'resumable'
            else:
                status = 'failed' if failure_kind in ('rejected', 'local_rejected') else 'interrupted'
            shot_update(project_id, index, status=status, error=diagnostic or '生成失败，请检查密钥或服务状态。')
            return
        data = json.loads(''.join(output))
        if data.get('task', {}).get('taskId'):
            shot_update(project_id, index, task_id=data['task']['taskId'])
        url = data.get('videos', [{}])[0].get('videoUrl')
        if not url or urlsplit(url).scheme != 'https':
            raise WorkflowError('模型未返回可下载的视频。')
        shot_update(project_id, index, status='processing', task_id=data.get('task', {}).get('taskId', saved.get('task_id', '')))
        with urlopen(url, timeout=120) as response, (path / f'shot-{index}-generated.mp4').open('wb') as stream:
            shutil.copyfileobj(response, stream)
        info = probe(path / f'shot-{index}-generated.mp4')
        shot_update(project_id, index, generated_duration=info['duration'], generated_audio=info['audio'])
        align(project_id, index, [])
    except Exception as error:
        saved = load(project_id)['shots'][index]
        shot_update(project_id, index, status='resumable' if saved.get('task_id') else 'interrupted' if started else 'failed', error=str(error)[:700])


def generate(project_id, index, prompt='', retry=False, generate_audio=True):
    if type(generate_audio) is not bool:
        raise WorkflowError('模型音频选项无效。')
    project = load(project_id)
    if project['status'] != 'ready' or not 0 <= index < len(project['shots']):
        raise WorkflowError('片段尚未准备好。')
    shot = project['shots'][index]
    if not CONFIG.is_file():
        raise WorkflowError('请先在右上角配置 DreamAPI 密钥。')
    if not SCRIPT.is_file():
        raise WorkflowError('找不到本机 DreamAPI skill，请先安装。')
    if shot['status'] == 'interrupted' or (shot['status'] in ('uploading', 'generating', 'processing') and not shot.get('task_id') and project_id not in ACTIVE):
        raise WorkflowError('上次提交结果不明。请先在 DreamAPI 控制台检查任务，避免重复计费。')
    resume = bool(shot.get('task_id')) and shot['status'] in ('resumable', 'uploading', 'generating', 'processing')
    if resume:
        prompt = shot.get('prompt', '')
        generate_audio = shot.get('generate_audio', True)
    if shot['status'] in ('review', 'failed') and not retry and not resume:
        raise WorkflowError('重新生成会创建新的计费任务，请明确选择重新生成。')
    if not isinstance(prompt, str) or len(prompt) > 1000:
        raise WorkflowError('画面要求请控制在1000字以内。')
    if project_id in ACTIVE:
        raise WorkflowError('当前项目仍在处理中。')
    history = shot.get('attempts', [])
    if not resume and shot.get('task_id'):
        history = [*history, {k:shot.get(k) for k in ('task_id','status','error','generate_audio')}]
    shot_update(project_id, index, status='generating' if resume else 'uploading', prompt=prompt, generate_audio=generate_audio, attempts=history, reviewed=False, error='', **({} if resume else {'task_id': ''}))
    start(project_id, model_call, index, resume)


def align(project_id, index, anchors):
    project = load(project_id); shot = project['shots'][index]; path = folder(project_id)
    source_duration = shot['duration']; generated_duration = shot['generated_duration']
    if len(anchors) not in (0, 2):
        raise WorkflowError('请提供两组对应时间点。')
    scale = source_duration / generated_duration; offset = 0
    if anchors:
        (s1, g1), (s2, g2) = anchors
        if not all(math.isfinite(v) for pair in anchors for v in pair) or not (0 <= s1 < s2 <= source_duration and 0 <= g1 < g2 <= generated_duration):
            raise WorkflowError('时间点须递增，并在各自片段时长以内。')
        scale = (s2 - s1) / (g2 - g1); offset = s1 - g1 * scale
        if not .25 <= scale <= 4:
            raise WorkflowError('这两组节点需要过大的变速，请重新选择或重新生成片段。')
    width, height = (1280, 720) if project['ratio'] == '16:9' else (720, 1280)
    video_filter = f'setpts={scale}*(PTS-STARTPTS),scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1'
    if offset < 0:
        video_filter += f',trim=start={-offset},setpts=PTS-STARTPTS'
    elif offset > 0:
        video_filter += f',tpad=start_mode=clone:start_duration={offset}'
    video_filter += ',tpad=stop_mode=clone:stop_duration=300,fps=30'
    shot_update(project_id, index, status='processing')
    output = path / f'shot-{index}-aligned.mp4'
    temporary = path / f'shot-{index}-aligned-new.mp4'
    try:
        run(['ffmpeg', '-y', '-v', 'error', '-i', path / f'shot-{index}-generated.mp4', '-an', '-vf', video_filter, '-t', source_duration, '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-movflags', '+faststart', temporary])
        with PREVIEW_LOCK:
            temporary.replace(output)
            (path / f'shot-{index}-preview.mp4').unlink(missing_ok=True)
    except Exception as error:
        temporary.unlink(missing_ok=True)
        shot_update(project_id, index, status='review' if output.is_file() else 'resumable' if shot.get('task_id') else 'failed', error=str(error)[:700])
        raise
    shot_update(project_id, index, status='review', anchors=anchors, scale=scale, offset=offset, version=time.time(), reviewed=False, error='')
    mutate(project_id, error='')


def review(project_id, index, approved):
    project = load(project_id)
    if project_id in ACTIVE or not 0 <= index < len(project['shots']) or project['shots'][index]['status'] != 'review':
        raise WorkflowError('请等待片段处理完成后再确认。')
    shot_update(project_id, index, reviewed=bool(approved))
    mutate(project_id, error='')




def build_preview(project_id, index):
    project = load(project_id)
    if not 0 <= index < len(project['shots']):
        raise WorkflowError('请选择有效片段。')
    shot = project['shots'][index]
    root = folder(project_id)
    aligned = root / f'shot-{index}-aligned.mp4'
    output = root / f'shot-{index}-preview.mp4'
    temporary = root / f'shot-{index}-preview-new.mp4'
    with PREVIEW_LOCK:
        if not aligned.is_file():
            raise WorkflowError('请先生成这个片段。')
        if output.is_file() and output.stat().st_mtime_ns >= aligned.stat().st_mtime_ns:
            return output
        try:
            run(['ffmpeg', '-y', '-v', 'error', '-i', aligned, '-ss', shot['start'], '-i', root / 'input.media', '-map', '0:v:0', '-map', '1:a:0?', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', shot['duration'], '-movflags', '+faststart', temporary])
            temporary.replace(output)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return output


def confirm_all(project_id):
    with LOCK:
        project = load(project_id)
        if project_id in ACTIVE:
            raise WorkflowError('当前项目仍在处理中。')
        if not project['shots'] or not all(s['status'] == 'review' and (folder(project_id) / f"shot-{s['index']}-aligned.mp4").is_file() for s in project['shots']):
            raise WorkflowError('请先生成全部片段。')
        for shot in project['shots']:
            shot['reviewed'] = True
        project.update(error='', export_ready=False)
        save(project)



def build_cover(project_id):
    project = load(project_id)
    root = folder(project_id)
    candidates = ([root / 'export.mp4'] if project.get('export_ready') else []) + [root / 'shot-0-aligned.mp4', root / 'source.mp4']
    media = next((path for path in candidates if path.is_file()), None)
    if media is None:
        raise WorkflowError('项目尚未准备好。')
    output = root / 'cover.jpg'
    with PREVIEW_LOCK:
        if not output.exists() or output.stat().st_mtime_ns < media.stat().st_mtime_ns:
            temporary = root / 'cover-new.jpg'
            try:
                run(['ffmpeg', '-y', '-v', 'error', '-i', media, '-frames:v', '1', '-vf', 'scale=640:360:force_original_aspect_ratio=decrease', temporary])
                temporary.replace(output)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
    return output


def project_summaries():
    projects = []
    unreadable = 0
    for record in DATA.glob('*/project.json'):
        try:
            project = json.loads(record.read_text())
            shots = project.get('shots', [])
            projects.append({
                **{k: project[k] for k in ('id', 'name', 'status', 'created')},
                'updated': record.stat().st_mtime,
                'duration': project.get('duration', 0), 'ratio': project['ratio'],
                'segment_count': len(shots),
                'generated_count': sum(s['status'] == 'review' for s in shots),
                'failed_count': sum(s['status'] in ('failed', 'resumable', 'interrupted') for s in shots),
                'export_ready': project.get('export_ready', False),
                'busy': project['id'] in ACTIVE,
                'thumbnail': f"/media/{project['id']}/cover.jpg?v={record.stat().st_mtime_ns}" if (record.parent / 'source.mp4').is_file() else None
            })
        except (ValueError, KeyError, OSError):
            unreadable += 1
    return {'projects': sorted(projects, key=lambda p:p['updated'], reverse=True), 'unreadable': unreadable}


def export(project_id):
    project = load(project_id); path = folder(project_id)
    if not project['shots'] or not all(s['status'] == 'review' and s['reviewed'] for s in project['shots']):
        raise WorkflowError('请先生成并确认所有片段。')
    mutate(project_id, message='合成画面并保留完整原音轨…', error='')
    manifest = path / 'concat.txt'
    manifest.write_text(''.join(f"file 'shot-{s['index']}-aligned.mp4'\n" for s in project['shots']))
    # Encode once across segment boundaries for a continuous timeline; audio always comes from the input.
    args = ['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '1', '-i', manifest, '-i', path / 'input.media', '-map', '0:v:0', '-map', '1:a:0?', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-c:a', 'aac', '-b:a', '192k', '-t', project['duration'], '-movflags', '+faststart', path / 'export-new.mp4']
    try:
        run(args)
        (path / 'export-new.mp4').replace(path / 'export.mp4')
    except Exception:
        (path / 'export-new.mp4').unlink(missing_ok=True)
        raise
    mutate(project_id, export_ready=True, message='已导出，音频取自原始素材。')
