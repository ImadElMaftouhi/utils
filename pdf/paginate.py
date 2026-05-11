#!/usr/bin/env python3
"""
pdf/paginate.py — Add page numbers to PDF pages
Stamps formatted page numbers (e.g. "Page 1 of 5") at a configurable position.
"""

import argparse
import io
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
except ImportError:
    print("pypdf is required: pip install pypdf", file=sys.stderr)
    sys.exit(1)

try:
    from reportlab.pdfgen import canvas
except ImportError:
    print("reportlab is required: pip install reportlab", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}

POSITIONS = {
    "top-left",
    "top-center",
    "top-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
}


def _position_xy(position: str, page_w: float, page_h: float, margin: float = 30) -> tuple[float, float, str]:
    """Return (x, y, alignment) for a named position. Alignment: left|center|right."""
    if position == "top-left":
        return margin, page_h - margin, "left"
    if position == "top-center":
        return page_w / 2, page_h - margin, "center"
    if position == "top-right":
        return page_w - margin, page_h - margin, "right"
    if position == "bottom-left":
        return margin, margin, "left"
    if position == "bottom-center":
        return page_w / 2, margin, "center"
    if position == "bottom-right":
        return page_w - margin, margin, "right"
    raise ValueError(f"Unknown position: {position}")


def _build_number_overlay(
    text: str,
    page_w: float,
    page_h: float,
    position: str,
    font_size: int,
) -> bytes:
    """Generate a one-page PDF with a page number positioned for stamping."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.setFont("Helvetica", font_size)
    x, y, align = _position_xy(position, page_w, page_h)
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)
    c.save()
    return buf.getvalue()


def add_page_numbers(
    src: Path,
    dest: Path,
    fmt: str,
    position: str,
    start: int,
    font_size: int,
) -> int:
    """Stamp formatted page numbers on every page. Returns count of pages stamped."""
    reader = PdfReader(str(src))
    writer = PdfWriter()
    total = len(reader.pages)

    for i, page in enumerate(reader.pages):
        text = fmt.format(n=start + i, total=total)
        box: RectangleObject = page.mediabox
        page_w = float(box.width)
        page_h = float(box.height)
        overlay_bytes = _build_number_overlay(text, page_w, page_h, position, font_size)
        overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
        page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(dest, "wb") as fh:
        writer.write(fh)

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Add formatted page numbers to PDF pages."
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
        help="Output directory for paginated PDFs.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="Page {n} of {total}",
        help='Format string with {n} and {total}. Default: "Page {n} of {total}".',
    )
    parser.add_argument(
        "--position",
        choices=sorted(POSITIONS),
        default="bottom-center",
        help="Anchor position (default: bottom-center).",
    )
    parser.add_argument(
        "--start", type=int, default=1, help="Starting page number (default: 1)."
    )
    parser.add_argument(
        "--font-size", type=int, default=10, help="Font size in points (default: 10)."
    )
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done.")

    args = parser.parse_args()

    if args.font_size < 1:
        parser.error("--font-size must be at least 1")

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

    total_stamped = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} → {dest} (format={args.fmt!r}, pos={args.position})")
            continue

        try:
            count = add_page_numbers(src, dest, args.fmt, args.position, args.start, args.font_size)
            total_stamped += count
            print(f"  {src.name}: numbered {count} page(s) → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(
            f"\nTotal: {total_stamped} page(s) numbered | "
            f"{len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
