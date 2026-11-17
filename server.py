"""Loopback-only prototype server; credentials live outside the public directory."""
import argparse
import json
import os
import re
import shutil
import pipeline
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent
CONFIG = Path.home() / '.config' / 'reframe-studio' / 'dreamapi.json'
PUBLIC_FILES = {'index.html', 'styles.css', 'home.css', 'home.js', 'settings.js', 'settings.css', 'i18n.js', 'preferences.js', 'project.html', 'project.js', 'project.css', 'ui-feedback.js'}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, config=CONFIG, **kwargs):
        self.config = config
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        return host in allowed and (origin is None or origin == f'http://{host}')

    def reply(self, status, value):
        payload = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(payload)

    def do_GET(self):
        if not self.local_request():
            return self.reply(403, {'error': 'origin'})
        path = urlsplit(self.path).path
        if path == '/workspace.html':
            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if path == '/api/settings/dreamapi':
            return self.reply(200, {'configured': self.config.is_file(), 'verified': False})
        if path == '/api/projects':
            return self.reply(200, pipeline.project_summaries())
        match = re.fullmatch(r'/api/projects/([0-9a-f]{32})', path)
        if match:
            try:
                return self.reply(200, pipeline.public(pipeline.load(match[1])))
            except pipeline.WorkflowError as error:
                return self.reply(404, {'error': str(error)})
        match = re.fullmatch(r'/media/([0-9a-f]{32})/([^/]+)', path)
        if match:
            return self.media(match[1], match[2])
        relative = path.lstrip('/') or 'index.html'
        asset = relative.startswith('assets/') and '..' not in relative.split('/') and (ROOT / relative).resolve().is_relative_to(ROOT / 'assets') and (ROOT / relative).is_file()
        if relative not in PUBLIC_FILES and not asset:
            return self.reply(404, {'error': 'not_found'})
        if self.command == 'HEAD':
            super().do_HEAD()
        else:
            super().do_GET()

    def do_HEAD(self):
        # No static directory listings or source/config exposure through HEAD either.
        self.do_GET()

    def do_POST(self):
        if not self.local_request():
            return self.reply(403, {'error': 'origin'})
        if self.path.startswith('/api/projects/'):
            return self.workflow_post()
        if self.path != '/api/settings/dreamapi':
            return self.reply(404, {'error': 'not_found'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply(415, {'error': 'content_type'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                return self.reply(400, {'error': 'invalid_key'})
            value = json.loads(self.rfile.read(length))
            key = value.get('key') if isinstance(value, dict) else None
            if not isinstance(key, str) or not 8 <= len(key) <= 4096 or any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in key):
                return self.reply(400, {'error': 'invalid_key'})
            self.config.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            temp = self.config.with_suffix('.tmp')
            descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(descriptor, 'w') as stream:
                os.chmod(temp, 0o600)
                json.dump({'api_key': key}, stream)
            temp.replace(self.config)
        except (ValueError, UnicodeDecodeError):
            return self.reply(400, {'error': 'invalid_key'})
        except OSError:
            return self.reply(500, {'error': 'save_failed'})
        self.reply(200, {'configured': True, 'verified': False})

    def json_body(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise pipeline.WorkflowError('请求格式不正确。')
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 < size <= 16384:
            raise pipeline.WorkflowError('请求内容过长或为空。')
        result = json.loads(self.rfile.read(size))
        if not isinstance(result, dict):
            raise pipeline.WorkflowError('请求格式不正确。')
        return result

    def workflow_post(self):
        parts = urlsplit(self.path)
        route = parts.path
        try:
            if route == '/api/projects/upload':
                query = parse_qs(parts.query)
                name = query.get('name', ['video.mp4'])[0]
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= pipeline.MAX_BYTES:
                    return self.reply(413, {'error': '请使用小于512MB的视频文件。'})
                project = pipeline.create(name, query.get('ratio', ['16:9'])[0])
                self.connection.settimeout(120)
                try:
                    with (pipeline.folder(project['id']) / 'input.media').open('wb') as stream:
                        remaining = size
                        while remaining:
                            chunk = self.rfile.read(min(1024 * 1024, remaining))
                            if not chunk:
                                raise pipeline.WorkflowError('上传中断，请重新选择文件。')
                            stream.write(chunk); remaining -= len(chunk)
                except Exception:
                    shutil.rmtree(pipeline.folder(project['id']))
                    raise
                pipeline.start(project['id'], pipeline.prepare)
                return self.reply(202, {'id': project['id']})
            data = self.json_body()
            if route == '/api/projects/import':
                url = data.get('url', '')
                if not isinstance(url, str) or not pipeline.valid_link(url):
                    raise pipeline.WorkflowError('请使用有效的 YouTube 或 TikTok 视频链接。')
                project = pipeline.create('Link import', data.get('ratio', '16:9'))
                pipeline.start(project['id'], pipeline.import_link, url)
                return self.reply(202, {'id': project['id']})
            match = re.fullmatch(r'/api/projects/([0-9a-f]{32})/(generate|align|review|export)', route)
            if not match:
                return self.reply(404, {'error': 'not_found'})
            project_id, action = match.groups()
            with pipeline.LOCK:
                project = pipeline.load(project_id)
                if action == 'export':
                    if data.get('confirm_all') is not True:
                        raise pipeline.WorkflowError('请点击确认全部并导出。')
                    pipeline.confirm_all(project_id)
                    pipeline.start(project_id, pipeline.export)
                else:
                    index = data.get('index')
                    if type(index) is not int or not 0 <= index < len(project['shots']):
                        raise pipeline.WorkflowError('请选择有效片段。')
                    if action == 'generate':
                        pipeline.generate(project_id, index, data.get('prompt', ''), data.get('retry') is True, data.get('generate_audio', True))
                    elif action == 'review':
                        pipeline.review(project_id, index, data.get('approved') is True)
                    else:
                        anchors = data.get('anchors', [])
                        if not isinstance(anchors, list) or len(anchors) not in (0, 2) or any(not isinstance(pair, list) or len(pair) != 2 or any(type(v) not in (int, float) for v in pair) for pair in anchors):
                            raise pipeline.WorkflowError('请填写两组有效时间点。')
                        if not (pipeline.folder(project_id) / f'shot-{index}-generated.mp4').is_file():
                            raise pipeline.WorkflowError('请先生成这个片段。')
                        pipeline.start(project_id, pipeline.align, index, anchors)
            return self.reply(202, {'id': project_id})
        except (pipeline.WorkflowError, ValueError, TypeError, KeyError) as error:
            return self.reply(400, {'error': str(error)})
        except Exception:
            return self.reply(500, {'error': '本机处理失败，请重试。'})

    def media(self, project_id, name):
        if not re.fullmatch(r'(source|export)\.mp4|cover\.jpg|shot-\d+(-reference\.mp4|-generated\.mp4|-aligned\.mp4|-preview\.mp4|\.jpg)', name):
            return self.reply(404, {'error': 'not_found'})
        path = pipeline.folder(project_id) / name
        if name == 'cover.jpg':
            try:
                path = pipeline.build_cover(project_id)
            except pipeline.WorkflowError as error:
                return self.reply(400, {'error': str(error)})
        preview = re.fullmatch(r'shot-(\d+)-preview\.mp4', name)
        if preview:
            try:
                path = pipeline.build_preview(project_id, int(preview[1]))
            except (pipeline.WorkflowError, ValueError) as error:
                return self.reply(400, {'error': str(error)})
        if not path.is_file():
            return self.reply(404, {'error': 'not_found'})
        size = path.stat().st_size
        begin, end = 0, size - 1
        range_header = self.headers.get('Range')
        if range_header:
            match = re.fullmatch(r'bytes=(\d+)-(\d*)', range_header)
            if not match:
                return self.reply(416, {'error': 'range'})
            begin = int(match[1]); end = min(int(match[2]), size - 1) if match[2] else size - 1
            if begin > end or begin >= size:
                return self.reply(416, {'error': 'range'})
        self.send_response(206 if range_header else 200)
        self.send_header('Content-Type', 'video/mp4' if name.endswith('.mp4') else 'image/jpeg')
        self.send_header('Content-Length', str(end - begin + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-store')
        if range_header:
            self.send_header('Content-Range', f'bytes {begin}-{end}/{size}')
        if name == 'export.mp4':
            self.send_header('Content-Disposition', 'attachment; filename="reframed.mp4"')
        self.end_headers()
        if self.command == 'HEAD':
            return
        try:
            with path.open('rb') as stream:
                stream.seek(begin); remaining = end - begin + 1
                while remaining:
                    chunk = stream.read(min(1024 * 1024, remaining))
                    if not chunk: break
                    self.wfile.write(chunk); remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_DELETE(self):
        if not self.local_request():
            return self.reply(403, {'error': 'origin'})
        if self.path != '/api/settings/dreamapi':
            return self.reply(404, {'error': 'not_found'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply(415, {'error': 'content_type'})
        try:
            self.config.unlink(missing_ok=True)
        except OSError:
            return self.reply(500, {'error': 'save_failed'})
        self.reply(200, {'configured': False, 'verified': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4178)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Reframe Studio: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
