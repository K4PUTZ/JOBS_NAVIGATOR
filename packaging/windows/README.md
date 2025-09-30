Windows Packaging
=================

Build
- Open Windows PowerShell and run from the repository root:
  - pwsh -File packaging/windows/build.ps1
  - For a console build: pwsh -File packaging/windows/build.ps1 -Mode console

Outputs
- dist/Sofa Jobs Navigator/                # onedir folder with the .exe
- dist/README-FIRST.txt                    # quickstart
- dist/Sofa_Jobs_Navigator.zip             # zipped folder for sharing

Version metadata
- The executable embeds the app version from src/sofa_jobs_navigator/version.py
  (FileVersion/ProductVersion).

First run (OAuth client)
- Place credentials.json at %APPDATA%\sofa_jobs_navigator\credentials.json
  or set env var SJN_CREDENTIALS_FILE=C:\path\to\credentials.json

Notes
- PyInstaller bundles the Python runtime and dependencies (no separate Python install needed).
- Help assets and icons are included.
- Consider code signing for broader distribution.

