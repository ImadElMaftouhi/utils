# 🛠️ utils

> A personal collection of reusable utility scripts for images, PDFs, files, and more.

## 📁 Structure

```
utils/
├── images/     # Image conversion, compression, and resizing
├── pdf/        # PDF compression, merging, splitting, and extraction
├── files/      # General file manipulation and format conversion
└── data/       # JSON, CSV parsers and data transformation tools
```

## 🚀 Getting Started

Each subdirectory is self-contained with its own `README.md` and dependencies.
Navigate to the relevant folder and follow its setup instructions.

```bash
# Example: run an image utility
cd images/
pip install -r requirements.txt
python compress.py --input photo.jpg --output photo_small.jpg
```

## 📦 Requirements

- Python 3.8+
- Per-module dependencies listed in each subdirectory's `requirements.txt`

## 🗂️ Categories

| Folder  | Description                                      |
|---------|--------------------------------------------------|
| `images/` | Convert formats, compress, resize images       |
| `pdf/`    | Reduce size, merge, split, extract pages/text  |
| `files/`  | Rename, organize, convert file formats         |
| `data/`   | Parse and transform JSON, CSV, and other data  |

## 📝 Contributing (Personal Notes)

- Each script should work both as a **CLI tool** and as an **importable module**
- Add usage examples in the relevant subdirectory `README.md`
- Keep dependencies minimal and isolated per folder