# Short2Wide

Local single-user video-reframing app. Keep the service loopback-only.

- Preserve existing projects and source/generated media during updates.
- Never commit API keys, credentials, private project records or development captures.
- Do not submit paid generation calls without user authorization. Persist task IDs; resume the same task after uncertain polling failures. Never automatically resubmit an ambiguous or failed paid task.
- Interface language must not rewrite user-entered prompts or source content.
- Source and generated players are independent; explicit sync playback restarts the active segment on both sides.
- Export is one explicit confirmation for all completed segments. Advanced cue alignment stays optional.
- Regression checks: `node --test test_playback.mjs` and `python3 -B -m unittest -q test_pipeline.py test_server.py test_provider.py`.
- For requested release work, each published commit in that batch must have a corresponding GitHub Release.
