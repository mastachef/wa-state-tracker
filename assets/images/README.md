# Image Assets

## Generating PNG versions

The SVG files in this directory need PNG versions for social sharing cards. To generate them:

### Option 1: Use an online converter
1. Go to https://svgtopng.com/ or similar
2. Upload `og-image.svg` and export at 1200x630px
3. Upload `favicon.svg` and export at multiple sizes:
   - 16x16 → favicon-16x16.png
   - 32x32 → favicon-32x32.png
   - 180x180 → apple-touch-icon.png

### Option 2: Use command line (requires Inkscape or ImageMagick)
```bash
# With Inkscape
inkscape og-image.svg -w 1200 -h 630 -o og-image.png
inkscape favicon.svg -w 32 -h 32 -o favicon-32x32.png
inkscape favicon.svg -w 16 -h 16 -o favicon-16x16.png
inkscape favicon.svg -w 180 -h 180 -o apple-touch-icon.png

# With ImageMagick (rsvg-convert needed)
rsvg-convert -w 1200 -h 630 og-image.svg > og-image.png
```

### Option 3: Use a GitHub Action
Add a workflow that converts SVGs to PNGs on push.

## Current files
- `favicon.svg` - Main favicon (works in modern browsers)
- `og-image.svg` - Social sharing card template

## Required PNG files (generate from SVGs)
- `og-image.png` - 1200x630px for social cards
- `favicon-32x32.png` - 32x32px favicon
- `favicon-16x16.png` - 16x16px favicon
- `apple-touch-icon.png` - 180x180px for iOS
