"""Render bilingual 20s product films from owned footage and actual UI captures.

If demo-result.mp4 is supplied, the opening is an actual before/after comparison.
Otherwise the wide canvas remains explicitly empty and the film is a workflow tour.
Requires Pillow and FFmpeg; no generation requests are made by this script.
"""
import argparse,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--media',type=Path,default=ROOT/'.production');parser.add_argument('--output',type=Path,default=ROOT/'docs/assets');args=parser.parse_args();B=args.media;OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
STORY=json.loads((Path(__file__).with_name('promo-story.json')).read_text())
BG='#f6f7f2';INK='#292e2a';MUTED='#61685e';ACCENT='#68775a';DARK='#172018'
source=B/'demo-source.mp4';result=B/'demo-result.mp4';actual=result.is_file()
def font(size,lang='en'):
    return ImageFont.truetype(str(ROOT/'assets'/('promo-latin.ttf' if lang=='en' else 'promo-zh.ttf')),size)
def text(draw,xy,copy,size=44,color=INK,lang='en'):
    draw.multiline_text(xy,copy,font=font(size,lang),fill=color,spacing=10)
def canvas(lang,title):
    image=Image.new('RGB',(1080,1080),BG);draw=ImageDraw.Draw(image)
    draw.line((48,50,76,50,76,78,48,78,48,50),fill=ACCENT,width=2)
    text(draw,(92,43),'Short2Wide',27,INK,'en');text(draw,(48,120),title,60,INK,lang)
    footer=STORY[lang]['footer'] if actual else ('Workflow tour · Creator-supplied source · Model output not shown' if lang=='en' else '流程展示 · 创作者提供原片 · 未展示模型结果')
    text(draw,(48,1008),footer,18,MUTED,lang)
    return image,draw

def ffmpeg(args):
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error',*map(str,args)],check=True)
def segment(name,inputs,graph,duration):
    graph=graph.replace('format=yuv420p[v]','scale=in_range=auto:out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]')
    output=B/(name+'.mp4');cmd=[]
    for path,still in inputs:
        if still:cmd+=['-loop','1']
        cmd+=['-i',path]
    ffmpeg(cmd+['-filter_complex',graph,'-map','[v]','-an','-t',duration,'-r','30','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',output]);return output

def render(lang):
    s=STORY[lang];en=lang=='en';title=s['titles'][0] if actual else ('One clip.\nA new canvas.' if en else '一段视频，\n开启新的画幅。')
    image,draw=canvas(lang,title)
    text(draw,(48,300),s['labels'][0],21,MUTED,lang)
    text(draw,(358,300),s['labels'][1] if actual else ('TARGET CANVAS · 16:9' if en else '目标画布 · 16:9'),21,MUTED,lang)
    draw.rounded_rectangle((48,346,304,798),radius=12,fill='#e8ebe2')
    draw.rounded_rectangle((358,426,1034,808),radius=12,fill='#e8ebe2')
    if not actual:
        text(draw,(596,558),'16:9',70,ACCENT,'en')
        text(draw,(448,668),'Model output not shown' if en else '此处不展示模型结果',25,MUTED,lang)
    card=B/f'promo-{lang}-1.png';image.save(card)
    graph='[1:v]scale=252:448:force_original_aspect_ratio=decrease,pad=252:448:(ow-iw)/2:(oh-ih)/2:color=0xe8ebe2,setsar=1[a];[0:v][a]overlay=50:348'
    inputs=[(card,True),(source,False)]
    if actual:
        graph+='[tmp];[2:v]scale=672:378,setsar=1[b];[tmp][b]overlay=360:428'
        inputs.append((result,False))
    graph+=',format=yuv420p[v]'
    first=segment(f'{lang}-part1',inputs,graph,4)
    image,draw=canvas(lang,s['titles'][1]);text(draw,(48,850),s['workflow'],30,ACCENT,lang);text(draw,(48,914),s['waiting'],21,MUTED,lang)
    card=B/f'promo-{lang}-2.png';image.save(card)
    screen=B/f'workspace.{lang}.jpg'
    second=segment(f'{lang}-part2',[(card,True),(screen,True)],'[1:v]scale=984:-2,setsar=1[a];[0:v][a]overlay=48:320,format=yuv420p[v]',5)
    image,draw=canvas(lang,s['titles'][2]);text(draw,(48,930),s['result'] if actual else ('Original soundtrack is kept in exports' if en else '导出保留原片音轨，画面可逐段调整'),25,ACCENT,lang)
    if not actual:
        features=['Independent previews','Restart both in sync','Confirm once. Export.'] if en else ['左右独立播放','同步从头开始','一次确认导出']
        for y,line in zip([410,540,670],features):
            draw.line((430,y-20,1000,y-20),fill='#d9ded3',width=1)
            text(draw,(430,y),line,33,INK,lang)
    card=B/f'promo-{lang}-3.png';image.save(card)
    if actual:
        third=segment(f'{lang}-part3',[(card,True),(result,False)],'[1:v]scale=984:554,setsar=1[a];[0:v][a]overlay=48:330,format=yuv420p[v]',7)
    else:
        third=segment(f'{lang}-part3',[(card,True),(source,False)],'[1:v]scale=330:586,setsar=1[a];[0:v][a]overlay=48:316,format=yuv420p[v]',7)
        # The source is deliberately the only video; no faux generated footage.
    image=Image.new('RGB',(1080,1080),DARK);draw=ImageDraw.Draw(image)
    text(draw,(68,160),'Short2Wide',108,'#e7eedb','en');text(draw,(72,355),s['tagline'],48,'#fafbf7',lang)
    text(draw,(72,550),'github.com/Hy-1990/Short2Wide',33,'#d2dec4','en');text(draw,(72,690),s['open'],29,'#e8eee2',lang)
    text(draw,(72,900),'Make room for your next story.' if en else '为下一段故事，留出更多空间。',30,'#c5d4b4',lang)
    card=B/f'promo-{lang}-4.png';image.save(card)
    fourth=segment(f'{lang}-part4',[(card,True)],'[0:v]format=yuv420p[v]',4)
    manifest=B/f'promo-{lang}-concat.txt';manifest.write_text(''.join(f"file '{part}'\n" for part in [first,second,third,fourth]))
    silent=B/f'promo-{lang}-silent.mp4';ffmpeg(['-f','concat','-safe','0','-i',manifest,'-c','copy',silent])
    final=OUT/f'short2wide-{lang}.mp4'
    # The promotional edit retains the creator's audio, then fades into a silent tail.
    audio_inputs=['-i',silent,'-i',source]
    if actual:
        audio_inputs+=['-i',result]
        audio_graph='[1:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=out:st=3.7:d=0.3[a1];[2:a]atrim=0:7,asetpts=PTS-STARTPTS,afade=t=in:d=0.15,afade=t=out:st=6.6:d=0.4,adelay=9000:all=1[a2];[a1][a2]amix=inputs=2:normalize=0,apad=whole_dur=20[a]'
    else:
        audio_graph='[1:a]afade=t=in:d=0.3,afade=t=out:st=13:d=1.5,apad=whole_dur=20[a]'
    ffmpeg(audio_inputs+['-filter_complex',audio_graph,'-map','0:v','-map','[a]','-t','20','-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',final])
    print(final,flush=True)
for language in ['en','zh-CN']:render(language)
