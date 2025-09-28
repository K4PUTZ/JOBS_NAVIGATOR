# macOS Packaging — Sofa Jobs Navigator

Build a signed .app (unsigned by default) and optional .dmg using PyInstaller.

## Prerequisites
- Python 3.10+ with Tk (macOS python.org or Homebrew ok)
- Optional: `hdiutil` for DMG creation (preinstalled on macOS)
- Optional: `codesign` identity to sign the app after build

## Build Steps
1. Create/activate a venv and install runtime deps:
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -e .` from `JOBS NAVIGATOR` (or `pip install -r requirements.txt` at repo root)
2. Run the packaging script:
   - `bash "JOBS NAVIGATOR/packaging/macos/build_mac.sh"`
   - The script auto-generates `sofa_icon.icns` from `sofa_icon.png` if missing (uses `sips` + `iconutil`).
3. Outputs:
   - App bundle: `JOBS NAVIGATOR/dist/Sofa Jobs Navigator.app`
   - DMG (if `hdiutil` present): `JOBS NAVIGATOR/dist/Sofa Jobs Navigator.dmg`

## Notes
- Icons: The app sets icons at runtime (PNG/ICO) via Tk; `.icns` is optional.
- Google client libs: A custom hook is included to pull in `googleapiclient` resources.
- First‑run setup: Use Settings → Connect/Refresh to authenticate; tokens are stored under user config via `platformdirs`.
- Offline mode builds: set `SJN_OFFLINE=1` to avoid live Google calls during smoke tests.

## Distributing without an Apple Developer ID (ad-hoc)

- The packaging script produces a self-contained `.app` that embeds a Python.framework
   (so users don't need system Python). Because you don't have an Apple Developer ID,
   the produced .app/DMG will not be notarized. Gatekeeper will show a warning the
   first time users try to open the app.
- Recommended user guidance to include with downloads:

   1. Right-click (or Control-click) the app and select "Open" and then confirm "Open"
       in the dialog. This is the cleanest way to allow an unsigned app.
   2. If the app was blocked, go to System Settings → Privacy & Security → Open Anyway.
   3. Advanced: users can open the app from Terminal to see logs:

       ```bash
       open "./Sofa Jobs Navigator.app"
       # or run the launcher directly to see the app log written inside the bundle
       "./Sofa Jobs Navigator.app/Contents/MacOS/Sofa Jobs Navigator"
       ```

## Logs & Support

- The app writes a startup/log file to:
   `Sofa Jobs Navigator.app/Contents/Resources/sofa_jobs_navigator.log` — ask users to attach this file when reporting issues.

## Next steps / Developer-ID placeholders

- When you're ready to pay for an Apple Developer Program account you can plug
   Developer-ID signing and notarization into `build_mac.sh`. The script already
   contains the right insertion points; if you want I can add the explicit
   `codesign` and `notarytool` calls (as comments or active code guarded by env
   variables) so switching to official signing is a one-line change.

## Additional packaging helpers (new)

- `prune_framework.py` — Conservative pruning tool to reduce embedded Python.framework size. Dry-run by default; pass `--apply` to delete matches. Configure `SJN_PRUNE=1` in the build environment to run after assembly.
- `auto_update.sh` — Minimal SHA256-verified updater that downloads a DMG/ZIP and installs it to /Applications (requires user consent and curl/shasum/hdiutil).
- `homebrew-cask-template.rb` — A template Homebrew cask you can modify for distribution via Homebrew Cask (host the DMG at an HTTPS URL).
- `ci_smoke_test.sh` — CI-friendly smoke test to validate the embedded Python can import the package and create a tkinter.Tk instance (if a display is available). Use in GitHub Actions after the build step to sanity check artifacts.

Use these tools cautiously: pruning and auto-update involve file operations that may alter release artifacts or a user's /Applications folder. Always test on a disposable VM or in a separate user account.
