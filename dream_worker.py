"""Run the bundled DreamAPI adapter and report structured failure classification."""
import json
import runpy
import sys

script = sys.argv[1]
sys.argv = sys.argv[1:]
try:
    runpy.run_path(script, run_name='__main__')
except SystemExit as error:
    if error.code:
        print('REFRAME_EVENT ' + json.dumps({'kind': 'local_rejected', 'message': str(error)}), file=sys.stderr)
    raise
except Exception as error:
    # DreamAPI's client attaches task_id only for a definitive remote task failure.
    kind = 'unknown'
    if type(error).__name__ == 'DreamAPIError':
        kind = 'terminal_failed' if getattr(error, 'task_id', '') else ('rejected' if getattr(error, 'code', -1) != -1 else 'unknown')
    print('REFRAME_EVENT ' + json.dumps({'kind': kind, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
