#!/usr/bin/env python3
"""
pdf/images_to_pdf.py — Combine images into a single PDF
Builds a PDF where each input image becomes one page, in the order given.
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# Page sizes in points (1 in = 72 pt)
PAGE_SIZES: dict[str, tuple[float, float]] = {
    "A4": (595.28, 841.89),
    "letter": (612.0, 792.0),
}


def _fit_image(img: Image.Image, page_w: float, page_h: float, margin: float) -> tuple[Image.Image, float, float, float, float]:
    """Resize img to fit within (page_w - 2*margin, page_h - 2*margin) preserving aspect.
    Returns (resized_image, x, y, draw_w, draw_h) in points relative to page origin."""
    avail_w = page_w - 2 * margin
    avail_h = page_h - 2 * margin
    iw, ih = img.size
    scale = min(avail_w / iw, avail_h / ih, 1.0)
    draw_w = iw * scale
    draw_h = ih * scale
    x = (page_w - draw_w) / 2
    y = (page_h - draw_h) / 2
    return img, x, y, draw_w, draw_h


def images_to_pdf(images: list[Path], dest: Path, page_size: str, margin: int) -> int:
    """Combine images into a single PDF (one image per page). Returns page count."""
    if not images:
        raise ValueError("No images provided")

    pil_pages: list[Image.Image] = []

    if page_size == "auto":
        for img_path in images:
            img = Image.open(img_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            pil_pages.append(img)
    else:
        if page_size not in PAGE_SIZES:
            raise ValueError(f"Unknown page size: {page_size}. Use one of: auto, {', '.join(PAGE_SIZES)}")
        page_w, page_h = PAGE_SIZES[page_size]
        # Pillow saves PDFs in points where 1 inch = 72 points; create canvases at correct size
        for img_path in images:
            src_img = Image.open(img_path)
            if src_img.mode in ("RGBA", "P"):
                src_img = src_img.convert("RGB")

            # Build a white-background page at the requested size (in pixels at 72 DPI)
            canvas = Image.new("RGB", (int(page_w), int(page_h)), color="white")
            _, x, y, draw_w, draw_h = _fit_image(src_img, page_w, page_h, margin)
            resized = src_img.resize((max(1, int(draw_w)), max(1, int(draw_h))), Image.LANCZOS)
            canvas.paste(resized, (int(x), int(page_h - y - draw_h)))
            pil_pages.append(canvas)

    if len(pil_pages) == 1:
        pil_pages[0].save(dest, "PDF", resolution=72.0)
    else:
        pil_pages[0].save(
            dest, "PDF", resolution=72.0, save_all=True, append_images=pil_pages[1:]
        )

    return len(pil_pages)


def main():
    parser = argparse.ArgumentParser(
        description="Combine images into a single PDF (one image per page)."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input image file(s) or director(ies). Order is preserved.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output PDF file path.",
    )
    parser.add_argument(
        "--page-size",
        choices=["auto"] + sorted(PAGE_SIZES),
        default="auto",
        help="Page size (default: auto = each page sized to its image).",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=0,
        metavar="N",
        help="Margin in points around each image (only used with fixed --page-size).",
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

    if args.margin < 0:
        parser.error("--margin must be 0 or greater")

    images: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*") if args.recursive else inp.glob("*")
            images.extend(sorted(f for f in glob if f.suffix.lower() in SUPPORTED_FORMATS))
        elif inp.is_file():
            if inp.suffix.lower() in SUPPORTED_FORMATS:
                images.append(inp)
            else:
                print(f"Skipping unsupported file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not images:
        print("No image files found.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] {len(images)} image(s) → {args.output} (page-size={args.page_size})")
        for img in images:
            print(f"  {img}")
        sys.exit(0)

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        page_count = images_to_pdf(images, args.output, args.page_size, args.margin)
        print(f"Created {args.output} ({page_count} page(s) from {len(images)} image(s))")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
