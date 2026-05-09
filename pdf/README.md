# 📄 pdf

Utilities for PDF compression, merging, splitting, and text extraction.

## Scripts

| Script | Description |
|--------|-------------|
| `compress.py` | Reduce PDF file size |
| `merge.py` | Merge multiple PDFs into one |
| `split.py` | Split a PDF into individual pages or ranges |
| `extract.py` | Extract text or images from a PDF |
| `ocr.py` | OCR scanned PDFs into searchable PDFs (opt-in deps) |
| `pdf_to_word.py` | Convert PDF to DOCX (opt-in dep, lossy) |
| `html_to_pdf.py` | Render static HTML/URL to PDF, no JavaScript (opt-in dep) |

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

# OCR a scanned PDF into searchable PDF (requires system tesseract + poppler)
pip install pytesseract pdf2image
python ocr.py scan.pdf -o out_dir/ --language eng --dpi 300

# Convert PDF to DOCX (best-effort fidelity)
pip install pdf2docx
python pdf_to_word.py report.pdf -o out_dir/

# Convert static HTML or URL to PDF (no JavaScript execution)
pip install weasyprint
python html_to_pdf.py page.html -o page.pdf
python html_to_pdf.py https://example.com -o example.pdf
```

## Dependencies

Core (always required):

```
pypdf>=4.0.0
pikepdf>=8.0.0
Pillow>=10.0.0
```

Opt-in (install only what you need):

| Script | Python deps | System deps |
|--------|-------------|-------------|
| `ocr.py` | `pytesseract`, `pdf2image` | `tesseract`, `poppler-utils` |
| `pdf_to_word.py` | `pdf2docx` | — |
| `html_to_pdf.py` | `weasyprint` | `pango`, `cairo`, `gdk-pixbuf` (Linux) |

## Future Web Integration

These features are deferred to a future browser-based companion app
because they require JavaScript execution, interactive UIs, cryptographic
certificates, or commercial conversion engines:

- Sign PDF, PDF Forms (interactive UI + crypto)
- Compare PDF, Edit PDF (visual UI)
- Scan to PDF (browser camera API)
- AI Summarizer, Translate PDF (LLM/translation APIs)
- PDF to PowerPoint/Excel, Office formats → PDF (commercial-quality engines)
- HTML → PDF with JavaScript rendering (headless browser like Playwright)
