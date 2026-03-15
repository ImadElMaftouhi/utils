# 🖼️ images

Utilities for image conversion, compression, and resizing.

## Scripts

| Script | Description |
|--------|-------------|
| `convert.py` | Convert between image formats (PNG, JPG, WEBP, etc.) |
| `compress.py` | Compress images while preserving quality |
| `resize.py` | Resize images by dimensions or percentage |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Convert format
python convert.py --input photo.png --output photo.webp

# Compress image
python compress.py --input photo.jpg --quality 80 --output photo_small.jpg

# Resize image
python resize.py --input photo.jpg --width 800 --output photo_resized.jpg
```

## Dependencies

```
Pillow>=10.0.0
```
