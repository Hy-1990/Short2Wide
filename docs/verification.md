# Verification

## Automated checks

Suite: 4 Node playback tests and 15 Python tests, including a native Windows launcher smoke test (skipped on other platforms). Tests use temporary fixtures and do not generate paid requests.

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

## Installation and distribution checks

The Bash launcher was verified with the existing system Python, without creating an environment or installing packages during launch. Startup from outside the project directory returned HTTP 200 at the printed URL; Ctrl+C shutdown and occupied-port handling were checked. On the tested Homebrew Python, pip required explicit user-directory installation with `--user --break-system-packages`, as documented in both READMEs. The downloader runs through the same Python interpreter, so a user-site CLI directory does not need to be added to PATH.

Tests are grouped under `tests/`. Production-only movie rendering scripts/fonts and local agent instructions are excluded from the public distribution; the actual application assets, finished films, source/result examples and license notices remain.

## Windows compatibility

CI now runs on both Ubuntu and Windows. The Windows-only smoke test launches `start.bat` from another directory, using an application path containing spaces and Chinese characters, checks the printed URL with a real HTTP request, and cleans up the process tree. The real FFmpeg pipeline test also uses a Unicode/space-containing temporary path and project name. Windows does not use POSIX chmod semantics; the credential test still verifies secret redaction and API boundaries on both platforms.

Project JSON, FFmpeg manifests and provider subprocess streams explicitly use UTF-8. The batch launcher prefers a usable `python` command, falls back to `py -3`, checks FFmpeg and Python packages, and keeps double-click startup errors visible. Existing project/key paths are preserved under the user-profile directory.

## Home navigation and larger libraries

Browser verification used actual local projects plus an isolated, mutation-disabled layout fixture service. With twelve fixture entries, Projects rendered twelve cards across responsive rows; name search selected one match, the exported filter selected four, and Home retained six recent cards while navigation showed the full count. Search no-match/clear, empty library, failed-load/refresh recovery, the help route, import validation, and New reframe input focus were exercised in Chinese/English and light/dark. Layout widths 1280, 768 and 390 had no horizontal overflow. Fixture entries were never written into the user's project directory. Public README captures contain only the creator-owned actual completed cloud-walk project.

This UI update changes no generation, playback, cue alignment or export semantics. Original local project file hashes were verified separately; obsolete homepage-only media and type assets were moved out of the distribution.
