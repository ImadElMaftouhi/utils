# 📄 pdf

Utilities for PDF compression, merging, splitting, and text extraction.

## Scripts

| Script | Description |
|--------|-------------|
| `compress.py` | Reduce PDF file size |
| `merge.py` | Merge multiple PDFs into one |
| `split.py` | Split a PDF into individual pages or ranges |
| `extract.py` | Extract text or images from a PDF |
| `repair.py` | Recover data from corrupt PDFs by re-saving with pikepdf |
| `redact.py` | Visual redaction (overlay opaque rectangles) — see warning below |

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

# Repair a corrupt PDF
python repair.py broken.pdf -o out_dir/

# Visually redact two regions on pages 1-3
python redact.py doc.pdf -o out_dir/ --region "100,200,150,20" --region "300,400,80,15" --pages 1-3
```

## Dependencies

```
pypdf>=4.0.0
pikepdf>=8.0.0
Pillow>=10.0.0
reportlab>=4.0.0
```

## ⚠️ Redaction warning

`redact.py` performs **visual** redaction only — it stamps an opaque rectangle
over the specified region. The underlying text remains in the PDF's content
stream and can be recovered by anyone who opens the file with the right tools.

For true text-removing redaction (rewriting the content stream), use
specialized tools designed for that purpose.
