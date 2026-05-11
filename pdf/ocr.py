#!/usr/bin/env python3
"""
pdf/ocr.py — OCR scanned PDFs into searchable PDFs
Rasterizes pages with pdf2image, runs Tesseract OCR via pytesseract, and writes
a new PDF with a hidden text layer that makes the document searchable.

System dependencies (must be installed separately):
  - tesseract  (the OCR engine)
  - poppler-utils  (used by pdf2image to rasterize pages)
"""

import argparse
import sys
from pathlib import Path

try:
    import pytesseract
except ImportError:
    print("pytesseract is required: pip install pytesseract", file=sys.stderr)
    sys.exit(1)

try:
    from pdf2image import convert_from_path
except ImportError:
    print("pdf2image is required: pip install pdf2image", file=sys.stderr)
    sys.exit(1)

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("pypdf is required: pip install pypdf", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}


def ocr_pdf(src: Path, dest: Path, language: str, dpi: int) -> int:
    """OCR src and write a searchable PDF to dest. Returns page count processed."""
    images = convert_from_path(str(src), dpi=dpi)

    writer = PdfWriter()
    for img in images:
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            img, extension="pdf", lang=language
        )
        # Write each page bytes through pypdf to merge into a single output
        import io

        page_reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in page_reader.pages:
            writer.add_page(page)

    with open(dest, "wb") as fh:
        writer.write(fh)

    return len(images)


def main():
    parser = argparse.ArgumentParser(
        description="OCR scanned PDFs into searchable PDFs (requires system tesseract + poppler)."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input PDF file(s) or director(ies).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for OCR'd PDFs.",
    )
    parser.add_argument(
        "--language",
        default="eng",
        help="Tesseract language code (default: eng). Examples: eng, fra, deu, eng+fra.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Rasterization DPI for OCR (default: 300; higher = slower/better).",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recurse into subdirectories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    if args.dpi < 72:
        parser.error("--dpi must be at least 72")

    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*") if args.recursive else inp.glob("*")
            files.extend(f for f in glob if f.suffix.lower() in SUPPORTED_FORMATS)
        elif inp.is_file():
            if inp.suffix.lower() in SUPPORTED_FORMATS:
                files.append(inp)
            else:
                print(f"Skipping unsupported file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    total_pages = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} → {dest} (lang={args.language}, dpi={args.dpi})")
            continue

        try:
            pages = ocr_pdf(src, dest, args.language, args.dpi)
            total_pages += pages
            print(f"  {src.name}: {pages} page(s) OCR'd → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(
            f"\nTotal: {total_pages} page(s) OCR'd | "
            f"{len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
