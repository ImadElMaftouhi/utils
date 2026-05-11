# 📄 pdf

Utilities for PDF compression, merging, splitting, extraction, and page operations.

## Scripts

| Script | Description |
|--------|-------------|
| `compress.py` | Reduce PDF file size |
| `merge.py` | Merge multiple PDFs into one |
| `split.py` | Split a PDF into individual pages or ranges |
| `extract.py` | Extract text or images from a PDF |
| `repair.py` | Recover data from corrupt PDFs by re-saving with pikepdf |
| `redact.py` | Visual redaction (overlay opaque rectangles) — see warning below |
| `images_to_pdf.py` | Combine images into a single PDF (one per page) |
| `protect.py` | Add AES-256 password protection |
| `unlock.py` | Remove password protection (requires current password) |
| `watermark.py` | Stamp text or image watermark on pages |
| `paginate.py` | Add formatted page numbers to pages |
| `rotate.py` | Rotate pages by 90, 180, or 270 degrees |
| `organize.py` | Reorder, delete, or duplicate pages by spec |
| `crop.py` | Crop page margins (in points) |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Compress PDF
python compress.py large.pdf -o out_dir/

# Merge PDFs
python merge.py a.pdf b.pdf c.pdf -o merged.pdf

# Split PDF (pages 1-3)
python split.py doc.pdf -o out_dir/ --pages 1-3

# Extract text
python extract.py --input doc.pdf --output text.txt

# Repair a corrupt PDF
python repair.py broken.pdf -o out_dir/

# Visually redact two regions on pages 1-3
python redact.py doc.pdf -o out_dir/ --region "100,200,150,20" --region "300,400,80,15" --pages 1-3
# Combine images into a single PDF
python images_to_pdf.py photo1.jpg photo2.jpg photo3.jpg -o album.pdf
# Encrypt a PDF
python protect.py doc.pdf -o out_dir/ --password mysecret --no-print

# Decrypt a PDF
python unlock.py locked.pdf -o out_dir/ --password mysecret
python extract.py doc.pdf -o text.txt

# Rotate pages 1-3 by 90°
python rotate.py doc.pdf -o out_dir/ --angle 90 --pages 1-3

# Reorder pages (3rd, 1st, 2nd; drop the rest)
python organize.py doc.pdf -o out_dir/ --order "3,1,2"

# Crop 36pt off all four margins
python crop.py doc.pdf -o out_dir/ --margin 36
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
