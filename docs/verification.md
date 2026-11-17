# Verification

## Automated checks

Passed: 4 Node playback tests and 14 Python pipeline, server and provider tests. Tests use temporary fixtures and do not generate paid requests.

- Independent left/right playback and seeking; solo actions release sync without controlling the other player.
- Every explicit sync start restarts the selected source segment and generated result together.
- Native generated audio is isolated from the original soundtrack during comparison.
- One confirmation authorizes export of all completed segments; missing or active segments remain guarded.
- FFmpeg preparation, short silent video, timeline coverage and exact source-audio selection in previews and exports.
- Failed alignment preserves the prior playable result; successful alignment invalidates the old preview cache.
- Project summaries preserve original project IDs and expose progress, thumbnails and export status.
- Task-query errors retain the same task ID. Unknown submissions block new requests. Explicit remote terminal failure is distinguished from transport/parse errors.
- Credential storage is private and never returned by the API. Cross-origin mutations and private static-file access are rejected.
- The bundled provider's query path never submits a new task; output-audio generation can be disabled explicitly.

## Browser verification

Real browser checks used isolated copies of local footage, with model submission disabled in the fixture service. They exercised independent playback, current-segment sync restarts, advanced-option disclosure, malformed cue recovery, one-click export, and localized notifications. Desktop and mobile, Chinese and English, light and dark were inspected.

The original local project was hashed before work. Test operations did not replace its source, generated files, export or saved review state. Only normal preview/thumbnail caches may be added during normal app use.

## Live provider example

The owner supplied their public 15-second cloud-walk video. The first native-audio generation returned provider error `-5022: Output audio contains sensitive content`. This identifies output audio, not the original uploaded video. The provider did not supply a more specific trigger.

The owner explicitly authorized one retry with model-audio generation disabled. That retry uses the same source segment, creates a new task deliberately, preserves the failed attempt record, and continues to use the original soundtrack locally. The final outcome is recorded in the showcase notes; no automatic paid retry is performed.

Both segments completed with model audio disabled. One confirmation then exported the full 15-second video at 1280 × 720, with AAC audio sourced from the original. Original/export decoded mono audio correlation was 0.999415 at 8 kHz. This verifies the soundtrack source, not visual-event synchronization.

The actual model result reconstructs the scene and changes camera movement and event timing. Duration normalization does not prove precise semantic or lip synchronization. This landscape clip is not a validation of speech, numbers, text or lip sync.
