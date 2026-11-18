"""Render smooth README previews from the finished bilingual product films."""
from pathlib import Path
import subprocess

ASSETS = Path(__file__).resolve().parents[1] / 'docs' / 'assets'

# GIF delays use hundredths of a second: 25 fps gives an exact 40 ms per frame.
# Keep the complete 30 fps MP4 as the full-quality playback/download option.
for language in ('en', 'zh-CN'):
    subprocess.run([
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-i', str(ASSETS / f'short2wide-{language}.mp4'), '-t', '4',
        '-filter_complex',
        '[0:v]fps=25,scale=540:540,split[a][b];'
        '[a]palettegen[p];[b][p]paletteuse',
        '-loop', '0', str(ASSETS / f'preview.{language}.gif'),
    ], check=True)
