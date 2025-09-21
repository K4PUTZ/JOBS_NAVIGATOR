"""Reference data extracted from legacy operators.

All structures here are safe-to-share templates. Populate secrets (if any) via
external files at runtime; never store live credentials in the repository.
"""

from __future__ import annotations

# =================== CREDENTIAL TEMPLATES ===================
# Copy your Google OAuth client details into the structure below at runtime.
# The legacy DRIVE_OPERATOR kept a similar layout under ``CREDENTIALS_JSON``.
# ------------------------------------------------------------

CREDENTIALS_TEMPLATE = {
    "installed": {
        "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
        "project_id": "your-project-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uris": ["http://localhost"],
    }
}


# =================== SHARED DRIVE ROUTING ===================
# Mirrors the routing table found in the legacy tooling. Adjust as needed.
# ------------------------------------------------------------

SHARED_DRIVE_IDS = {
    "0-9": "0AJmknNqOWBvjUk9PVA",
    "A-F": "0ALFcGfxuw7zqUk9PVA",
    "G-N": "0AMvwxfXxfIqkUk9PVA",
    "O-S": "0AGrHdqem4gtCUk9PVA",
    "T-Z": "0ABuvdtBlCWzGUk9PVA",
}

DRIVE_BACKUP_NAMES = {
    "0-9": {"primary": "_JOBS_0-9", "backup": "z_PKG_BKP_0-9"},
    "A-F": {"primary": "_JOBS_A-F", "backup": "z_PKG_BKP_A-F"},
    "G-N": {"primary": "_JOBS_G-N", "backup": "z_PKG_BKP_G-N"},
    "O-S": {"primary": "_JOBS_O-S", "backup": "z_PKG_BKP_O-S"},
    "T-Z": {"primary": "_JOBS_T-Z", "backup": "z_PKG_BKP_T-Z"},
}


# =================== DEFAULT SHORTCUT PATHS ===================
# Seed favorites dialog with legacy Sofa Navigator paths. Users can override.
# --------------------------------------------------------------

DEFAULT_SHORTCUTS = [
    {"label": "AV_QC", "path": "", "notes": "Fixed shared drive folder"},
    {"label": "Trailer / Video IN", "path": "02-TRAILER/VIDEO IN"},
    {"label": "Artes", "path": "EXPORT/03- ARTES"},
    {"label": "Marketing / Social", "path": "EXPORT/03- ARTES/06- MARKETING/SOCIAL"},
    {"label": "Envio Direto", "path": "EXPORT/03- ARTES/03- ENVIO DIRETO PLATAFORMA"},
    {"label": "Legendas", "path": "EXPORT/02- LEGENDAS"},
    {"label": "Temp", "path": "TEMP"},
    {"label": "Entrega", "path": "EXPORT/04- ENTREGAS"},
]

# =================== END REFERENCE DATA ===================
