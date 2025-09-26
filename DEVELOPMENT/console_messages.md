# Console Messages Reference

This document lists all possible console messages that can appear in the Sofa Jobs Navigator application.

## Console System Overview

The console now uses **plain white text only** - all color functionality and symbols have been removed.

### Console Methods Available:
- `append_console(message)` - Plain text message
- `console_success(message)` - Plain text success message
- `console_warning(message)` - Plain text warning message  
- `console_error(message)` - Plain text error message
- `console_sku_detected(sku)` - Plain text SKU detection message
- `console_hint(message)` - Plain text hint message
- `append_console_highlight(message, highlight, ...)` - Now just plain text (highlighting removed)

## All Console Messages Organized by Category

Please verify if each message is in the correct category:

### ERRORS (Red - 5 messages)
1. `Auth failed: {error}`
2. `Auth failed: {exc}` (variant)
3. `{error}` (general navigation/operation errors)
4. `Create local folder failed: {exc}`
5. `Failed to clear recent SKUs: {e}`

### WARNINGS (Gold Yellow - 8 messages)
1. `No SKU context yet. Press F12 after copying a SKU.`
2. `No SKU found in clipboard.`
3. `No SKU set. Press F12 after copying a SKU.`
4. `Working Folder is not set. Open Settings and choose a local folder.`
5. `No SKU found.`
6. `Not connected. Press F11 to connect to Google Drive.`
7. `No SKU found in clipboard after connect.`
8. `No additional SKUs to load into Recents.`

### NEUTRALS (White - 16 messages)
1. `Recent SKUs cleared.`
2. `--- Clipboard SKU scan ---`
3. `SKU: {sku}  @[{start}:{end}]  context='{context}'` (SKU in cyan)
4. `SKU detected: {sku}` (SKU in cyan)
5. `Cleared stored credentials.`
6. `Checking clipboard for SKU… (F9)`
7. `Create SKU folder invoked (no handler wired).`
8. `Copied SKU: {full}` (SKU in cyan)
9. `No additional unique SKUs beyond the first detected.`
10. `Load additional found SKUs into Recents?`
11. `Other detected SKUs: {first_few_text}` (SKUs in cyan)
12. `Other detected SKUs: {sku_list}` (SKUs in cyan)
13. `Resolved path '{path}' -> {folder_id}`
14. `Opening SKU root in browser: {url}`
15. `Loaded {loaded_count} SKUs into Recents (of {total_candidates} available).`
16. `Loaded {loaded_count} SKUs into Recents.`

### HINTS (Pink - 3 messages)
1. `Copy a SKU (Vendor-ID) to the memory and click search or press F12.`
2. `Search SKU: copy a SKU and press F12 (toolbar will invoke when wired).`
3. `Choose a Favorite on the right (or press F1–F8).`

### SUCCESS (Light Green - 5 messages)
1. `Connected to Google Drive.`
2. `Opening in browser: {url}`
3. `Created local folder: {path}`
4. `Auto-connected to Google Drive`
5. `Connected to Google Drive.` (variant from startup detection)

## TOTAL: 37 possible console messages

**REMOVED MESSAGES:**
- ❌ `About dialog is under development.` - Removed fallback message
- ❌ `Help is under development.` - Removed fallback message

**COLOR SCHEME:**
- **Errors:** Red (#dc3545)
- **Warnings:** Gold Yellow (#ffc107)  
- **Neutrals:** White (default)
- **Hints:** Pink (#ff69b4)
- **Success:** Light Green (#90ee90)
- **SKU Values:** Cyan (#0dcaf0) - Applied to any SKU value regardless of message category