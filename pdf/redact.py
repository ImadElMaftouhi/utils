#!/usr/bin/env python3
"""
pdf/redact.py — Visual PDF redaction script
Overlays opaque rectangles on specified regions to hide content.

WARNING: This is *visual* redaction only. The underlying text remains in the
content stream and may be recoverable. For true text-removing redaction,
specialized tools that rewrite the content stream are required.
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


def parse_page_ranges(spec: str, total: int) -> list[int]:
    """Parse "1-3,5,7-9" → sorted list of 0-based page indices."""
    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start < 1 or end > total or start > end:
                raise ValueError(f"Page range {part!r} is out of bounds (1–{total})")
            indices.update(range(start - 1, end))
        else:
            page = int(part)
            if page < 1 or page > total:
                raise ValueError(f"Page {page} is out of bounds (1–{total})")
            indices.add(page - 1)
    return sorted(indices)


def parse_region(spec: str) -> tuple[float, float, float, float]:
    """Parse "x,y,w,h" into a tuple of floats (in points)."""
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Region must be 'x,y,w,h', got: {spec!r}")
    try:
        x, y, w, h = (float(p) for p in parts)
    except ValueError as exc:
        raise ValueError(f"Region values must be numeric: {spec!r}") from exc
    if w <= 0 or h <= 0:
        raise ValueError(f"Region width/height must be positive: {spec!r}")
    return x, y, w, h


def _build_redaction_overlay(
    page_w: float, page_h: float, regions: list[tuple[float, float, float, float]]
) -> bytes:
    """Generate a one-page PDF with black rectangles at the given regions."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    for x, y, w, h in regions:
        c.rect(x, y, w, h, fill=1, stroke=0)
    c.save()
    return buf.getvalue()


def redact_pdf(
    src: Path,
    dest: Path,
    regions: list[tuple[float, float, float, float]],
    pages_spec: str | None,
) -> int:
    """Stamp black rectangles on selected pages. Returns count of redacted pages."""
    if not regions:
        raise ValueError("At least one region is required")

    reader = PdfReader(str(src))
    writer = PdfWriter()
    total = len(reader.pages)
    targets = set(parse_page_ranges(pages_spec, total)) if pages_spec else set(range(total))

    redacted = 0
    for i, page in enumerate(reader.pages):
        if i in targets:
            box: RectangleObject = page.mediabox
            page_w = float(box.width)
            page_h = float(box.height)
            overlay_bytes = _build_redaction_overlay(page_w, page_h, regions)
            overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
            redacted += 1
        writer.add_page(page)

    with open(dest, "wb") as fh:
        writer.write(fh)

    return redacted


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Apply visual redaction (opaque rectangles) to PDF pages. "
            "WARNING: text remains in the content stream — see README."
        )
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
        help="Output directory for redacted PDFs.",
    )
    parser.add_argument(
        "--region",
        action="append",
        required=True,
        metavar="X,Y,W,H",
        help='Rectangle in points: "x,y,w,h". Repeatable for multiple regions.',
    )
    parser.add_argument(
        "--pages",
        metavar="RANGE",
        help='Page range, e.g. "1-3,5". Default: all pages.',
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

    try:
        regions = [parse_region(r) for r in args.region]
    except ValueError as e:
        parser.error(str(e))

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

    total_redacted = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            scope = f"pages={args.pages}" if args.pages else "all pages"
            print(f"[dry-run] {src} → {dest} ({len(regions)} region(s), {scope})")
            continue

        try:
            count = redact_pdf(src, dest, regions, args.pages)
            total_redacted += count
            print(f"  {src.name}: redacted {count} page(s) → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(
            f"\nTotal: {total_redacted} page(s) redacted | "
            f"{len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
