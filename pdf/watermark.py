#!/usr/bin/env python3
"""
pdf/watermark.py — PDF watermark script
Stamps text or image watermarks across pages with configurable opacity, angle, and position.
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
    from reportlab.lib.colors import Color
    from reportlab.pdfgen import canvas
except ImportError:
    print("reportlab is required: pip install reportlab", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}
IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}

POSITIONS = {"center", "top-left", "top-right", "bottom-left", "bottom-right"}


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


def _position_xy(position: str, page_w: float, page_h: float, margin: float = 36) -> tuple[float, float]:
    """Return (x, y) in points for a named position on a page."""
    if position == "center":
        return page_w / 2, page_h / 2
    if position == "top-left":
        return margin, page_h - margin
    if position == "top-right":
        return page_w - margin, page_h - margin
    if position == "bottom-left":
        return margin, margin
    if position == "bottom-right":
        return page_w - margin, margin
    raise ValueError(f"Unknown position: {position}")


def _build_text_overlay(
    text: str,
    page_w: float,
    page_h: float,
    opacity: float,
    angle: float,
    position: str,
    font_size: int,
) -> bytes:
    """Generate a one-page PDF with text positioned for stamping."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=opacity))
    c.setFont("Helvetica-Bold", font_size)
    x, y = _position_xy(position, page_w, page_h)
    c.saveState()
    c.translate(x, y)
    c.rotate(angle)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()
    return buf.getvalue()


def _build_image_overlay(
    img_path: Path,
    page_w: float,
    page_h: float,
    opacity: float,
    position: str,
) -> bytes:
    """Generate a one-page PDF with an image positioned for stamping."""
    from reportlab.lib.utils import ImageReader

    img = ImageReader(str(img_path))
    iw, ih = img.getSize()

    max_w = page_w * 0.5
    max_h = page_h * 0.5
    scale = min(max_w / iw, max_h / ih, 1.0)
    draw_w, draw_h = iw * scale, ih * scale

    cx, cy = _position_xy(position, page_w, page_h)
    x = cx - draw_w / 2
    y = cy - draw_h / 2

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.setFillAlpha(opacity)
    c.drawImage(img, x, y, width=draw_w, height=draw_h, mask="auto")
    c.save()
    return buf.getvalue()


def _stamp_pages(
    src: Path,
    dest: Path,
    overlay_factory,
    pages_spec: str | None,
) -> int:
    """Apply overlay (built per page) to selected pages. Returns stamped count."""
    reader = PdfReader(str(src))
    writer = PdfWriter()
    total = len(reader.pages)
    targets = set(parse_page_ranges(pages_spec, total)) if pages_spec else set(range(total))

    stamped = 0
    for i, page in enumerate(reader.pages):
        if i in targets:
            box: RectangleObject = page.mediabox
            page_w = float(box.width)
            page_h = float(box.height)
            overlay_bytes = overlay_factory(page_w, page_h)
            overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
            stamped += 1
        writer.add_page(page)

    with open(dest, "wb") as fh:
        writer.write(fh)

    return stamped


def watermark_text(
    src: Path,
    dest: Path,
    text: str,
    opacity: float,
    angle: float,
    position: str,
    font_size: int,
    pages_spec: str | None,
) -> int:
    """Stamp text watermark on selected pages. Returns stamped count."""
    def factory(w: float, h: float) -> bytes:
        return _build_text_overlay(text, w, h, opacity, angle, position, font_size)

    return _stamp_pages(src, dest, factory, pages_spec)


def watermark_image(
    src: Path,
    dest: Path,
    img_path: Path,
    opacity: float,
    position: str,
    pages_spec: str | None,
) -> int:
    """Stamp image watermark on selected pages. Returns stamped count."""
    def factory(w: float, h: float) -> bytes:
        return _build_image_overlay(img_path, w, h, opacity, position)

    return _stamp_pages(src, dest, factory, pages_spec)


def main():
    parser = argparse.ArgumentParser(
        description="Stamp text or image watermarks on PDF pages."
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
        help="Output directory for watermarked PDFs.",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--text", help="Text to stamp (e.g. 'DRAFT').")
    mode.add_argument("--image", type=Path, help="Image file to stamp.")

    parser.add_argument(
        "--opacity", type=float, default=0.3, help="Opacity 0.0–1.0 (default: 0.3)."
    )
    parser.add_argument(
        "--angle", type=float, default=45, help="Rotation angle in degrees (text only, default: 45)."
    )
    parser.add_argument(
        "--position",
        choices=sorted(POSITIONS),
        default="center",
        help="Anchor position (default: center).",
    )
    parser.add_argument(
        "--font-size", type=int, default=72, help="Font size in points (text only, default: 72)."
    )
    parser.add_argument(
        "--pages",
        metavar="RANGE",
        help='Page range, e.g. "1-3,5". Default: all pages.',
    )
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done.")

    args = parser.parse_args()

    if not (0.0 <= args.opacity <= 1.0):
        parser.error("--opacity must be between 0.0 and 1.0")
    if args.image is not None:
        if not args.image.is_file():
            parser.error(f"Image not found: {args.image}")
        if args.image.suffix.lower() not in IMAGE_FORMATS:
            parser.error(f"Unsupported image format: {args.image.suffix}")

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
            mode_label = f"text={args.text!r}" if args.text else f"image={args.image}"
            print(f"[dry-run] {src} → {dest} ({mode_label}, {args.position}, opacity={args.opacity})")
            continue

        try:
            if args.text:
                count = watermark_text(
                    src, dest, args.text, args.opacity, args.angle, args.position, args.font_size, args.pages
                )
            else:
                count = watermark_image(src, dest, args.image, args.opacity, args.position, args.pages)
            total_stamped += count
            print(f"  {src.name}: stamped {count} page(s) → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(
            f"\nTotal: {total_stamped} page(s) stamped | "
            f"{len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
