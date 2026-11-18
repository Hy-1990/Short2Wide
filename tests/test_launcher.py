"""Exercise the native Windows launcher without paid generation or user data."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from urllib.request import urlopen


@unittest.skipUnless(os.name == 'nt', 'Native Windows batch launcher')
class WindowsLauncherTests(unittest.TestCase):
    def test_launch_from_another_directory_with_unicode_and_spaces(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / '项目 with spaces'
            app.mkdir()
            for name in ('start.bat', 'server.py', 'pipeline.py', 'index.html'):
                shutil.copy2(root / name, app / name)
            with (Path(directory) / 'startup.log').open('w+', encoding='utf-8') as log:
                process = subprocess.Popen(
                    ['cmd.exe', '/d', '/c', 'call', str(app / 'start.bat'), '--port', '0'],
                    cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                    env={**os.environ, 'CI': 'true'},
                )
                try:
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline:
                        log.seek(0)
                        output = log.read()
                        match = re.search(r'http://127\.0\.0\.1:\d+/', output)
                        if match:
                            with urlopen(match.group(), timeout=5) as response:
                                self.assertEqual(response.status, 200)
                            self.assertIn('Ctrl+C', output)
                            self.assertFalse((app / '.venv').exists())
                            break
                        self.assertIsNone(process.poll(), output)
                        time.sleep(.1)
                    else:
                        self.fail('Launcher timed out: ' + output)
                finally:
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
                    process.wait(timeout=10)
