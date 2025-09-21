# Sofa Jobs Navigator — Master Plan

This roadmap tracks every major task required to deliver a lightweight, cross-platform SKU navigation tool. Update the checklist as phases complete so the next contributor (human or AI) can jump in without context loss.

---

## Phase 0 — Foundations *(current)*
- [x] Create project workspace at `JOBS NAVIGATOR/`
- [x] Capture **baseline journal entry** (`DEVELOPMENT/journal.json`) describing objectives and environment
- [x] Document the high-level scope here in the master plan
- [x] Copy reference dictionaries/credentials from `DRIVE_OPERATOR.py` into a holding module for later reuse
- [x] Define global **diagnostic flags** (env vars or config toggles) for verbose logging, Drive API stubbing, and UI debug overlays
- [x] Stand up a `tests/` skeleton (e.g., `pytest`) with placeholder suites for utilities and services

## Phase 1 — Core Library Modules
- [x] `utils/sku.py`: reusable SKU extractor with first-match scanning across arbitrary text *(include DEBUG flag to dump parsing steps when enabled)*
- [x] `services/drive_client.py`: Google Drive wrapper (auth, shared-drive routing, folder traversal cache) *(support OFFLINE_MODE flag to short-circuit API calls during tests)*
- [x] `config/settings.py`: cross-platform JSON config persistence with defaults seeded from reference data *(add CONFIG_DRY_RUN option for no-write testing)*
- [x] `logging/event_log.py`: simple structured logger + rotating file handler *(respect VERBOSE_LOGGING flag)*

## Phase 2 — Application Shell
- [x] `app.py`: glue layer that boots config, services, and UI *(reads debug flags and propagates to subsystems)*
- [x] `ui/main_window.py`: main Tk window (console, favorites, recents, SKU controls) *(include UI_DEBUG flag to highlight widget bounds when troubleshooting)*
- [x] `ui/settings_dialog.py`: editable favorites table, auth reset, platform toggles *(records when tests update favorites)*
- [x] Hotkey manager (`controls/hotkeys.py`) to map `F12` launch + per-favorite bindings *(expose TEST_HOTKEY override)*

## Phase 3 — User Experience Enhancements
- [x] Modal shortcut picker invoked by hotkey (numbered buttons + keypress handling)
- [x] Sound feedback module with platform-aware fallbacks *(mute automatically when MUTE_SOUNDS flag is set)*
- [x] Clipboard monitor utility with robust error messages when no SKU is found *(support MOCK_CLIPBOARD input for automated testing)*
- [x] Recent SKU list management with optional persistence toggle *(ensure clear hooks for unit tests)*

## Phase 4 — Packaging & Documentation
- [x] `README.md`: setup, runtime instructions, packaging tips for macOS/Linux/Windows (document debug flags & test harness)
- [x] `pyproject.toml` (or equivalent) enumerating dependencies *(include `extras_require` section for `test` tools)*
- [x] Build/packaging notes (e.g., PyInstaller recipe skeleton) *(cover enabling/disabling debug flags during build)*
- [ ] Final QA checklist + update to `MASTER_PLAN.md` marking completion *(record test run results)

## Ongoing Tasks
- [ ] Maintain `DEVELOPMENT/journal.json` — append entries whenever meaningful progress is made
- [ ] Keep UI text using the term **SKU** (only exception: “Copy a SKU (Vendor-ID) to the memory and press F12.”)
- [ ] Ensure each module contains clear ASCII separators and inline usage documentation
- [ ] Keep **debug/test flag definitions** centralized (e.g., `config/flags.py`) so new modules stay consistent
- [x] Run automated tests (`pytest tests/`) before marking phases complete; log results in the journal

---

**Next Action**: perform manual smoke checks and draft final QA summary before handoff.
