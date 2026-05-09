# 📄 pdf

Utilities for PDF compression, merging, splitting, and text extraction.

## Scripts

| Script | Description |
|--------|-------------|
| `compress.py` | Reduce PDF file size |
| `merge.py` | Merge multiple PDFs into one |
| `split.py` | Split a PDF into individual pages or ranges |
| `extract.py` | Extract text or images from a PDF |
| `protect.py` | Add AES-256 password protection |
| `unlock.py` | Remove password protection (requires current password) |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Compress PDF
python compress.py --input large.pdf --output small.pdf

# Merge PDFs
python merge.py --inputs a.pdf b.pdf c.pdf --output merged.pdf

# Split PDF (pages 1-3)
python split.py --input doc.pdf --pages 1-3 --output part.pdf

# Extract text
python extract.py --input doc.pdf --output text.txt

# Encrypt a PDF
python protect.py doc.pdf -o out_dir/ --password mysecret --no-print

# Decrypt a PDF
python unlock.py locked.pdf -o out_dir/ --password mysecret
```

## Dependencies

```
pypdf>=4.0.0
pikepdf>=8.0.0
```
