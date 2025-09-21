# Packaging Notes

## PyInstaller skeleton

```bash
pyinstaller \
  --name "SofaJobsNavigator" \
  --windowed \
  --add-data "src/sofa_jobs_navigator/config/reference_data.py:sofa_jobs_navigator/config" \
  src/sofa_jobs_navigator/app.py
```

- Set `SJN_OFFLINE=1` for smoke builds when Drive credentials are not available.
- To include platform sounds on Linux, bundle the referenced `~/sounds/*.wav` files or adjust `_play` fallbacks.

## Distributable Archives
- Source wheel / sdist via `python -m build`.
- Share zipped `dist/` output inside the internal network; credentials are supplied by end users via `reference_data.py`.

## Pre-release Checklist
1. Run `pytest` with `SJN_VERBOSE=1` to ensure extra logging does not break.
2. Launch app on macOS, Windows, and Linux to verify keyboard shortcuts and sounds.
3. Confirm `DEVELOPMENT/` is excluded from distributables.

- Ensure google-auth and google-auth-oauthlib are included in the packaged environment.
