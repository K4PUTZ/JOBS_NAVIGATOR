Help images for WelcomeWindow

Expected filenames (1-based page indexes):

- Help1.png or Help1.webp  # Page 1: Intro
- Help2.png or Help2.webp  # Page 2: Working Folder
- Help3.png or Help3.webp  # Page 3: Authentication
- Help4.png or Help4.webp  # Page 4: Favorites
- Help5.png or Help5.webp  # Page 5: Recents

Notes:
- PNG loads natively via Tk. WebP requires Pillow (PIL).
- You can override the folder at runtime by passing `image_dir=` to `WelcomeWindow`.
- Recommended canvas size ~400x280 for best fit.
