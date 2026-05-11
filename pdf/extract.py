#!/usr/bin/env python3
"""
pdf/extract.py — PDF extraction script
Extracts text or embedded images from PDF files.
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf is required: pip install pypdf", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image

    _PIL_AVAILABLE = True
except ImportError:
    Image = None
    _PIL_AVAILABLE = False


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


def extract_text(src: Path, dest: Path, page_spec: str | None) -> tuple[int, int]:
    """Extract plain text from src into dest. Returns (pages_processed, chars_written)."""
    reader = PdfReader(str(src))
    total = len(reader.pages)
    page_indices = parse_page_ranges(page_spec, total) if page_spec else list(range(total))

    lines: list[str] = []
    for i in page_indices:
        text = reader.pages[i].extract_text() or ""
        lines.append(f"--- Page {i + 1} ---\n{text}\n")

    content = "\n".join(lines)
    dest.write_text(content, encoding="utf-8")
    return len(page_indices), len(content)


def extract_images(src: Path, output_dir: Path, page_spec: str | None, fmt: str) -> int:
    """Extract embedded images from src into output_dir. Returns image count."""
    reader = PdfReader(str(src))
    total = len(reader.pages)
    page_indices = parse_page_ranges(page_spec, total) if page_spec else list(range(total))

    count = 0
    for i in page_indices:
        for img_obj in reader.pages[i].images:
            stem = f"page{i + 1:04d}_img{count + 1:04d}"
            if _PIL_AVAILABLE:
                pil_img = Image.open(img_obj)
                out = output_dir / f"{stem}.{fmt}"
                pil_img.save(out, format=fmt.upper())
            else:
                out = output_dir / f"{stem}.raw"
                out.write_bytes(img_obj.data)
            count += 1

    return count


def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024**2:.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description="Extract text or embedded images from PDF files."
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
        help="Output file (text mode) or directory (images mode).",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--text",
        action="store_true",
        help="Extract text (default).",
    )
    mode.add_argument(
        "--images",
        action="store_true",
        help="Extract embedded images.",
    )

    parser.add_argument(
        "--pages",
        "-p",
        metavar="RANGE",
        help='Page range, e.g. "1-3,5" (1-based). Default: all pages.',
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        default="png",
        choices=["png", "jpeg", "webp"],
        help="Image output format (default: png). Only used with --images.",
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

    use_images = args.images
    use_text = args.text or not use_images

    if use_images and not _PIL_AVAILABLE:
        print(
            "Warning: Pillow not installed — images will be saved as raw bytes.",
            file=sys.stderr,
        )

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
        if use_images or len(files) > 1:
            args.output.mkdir(parents=True, exist_ok=True)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)

    errors = 0

    for src in files:
        if use_images:
            dest = args.output
        elif len(files) == 1:
            dest = args.output
        else:
            dest = args.output / f"{src.stem}.txt"

        if args.dry_run:
            mode_label = "images" if use_images else "text"
            print(f"[dry-run] {src} → {dest} ({mode_label})")
            continue

        try:
            if use_images:
                count = extract_images(src, dest, args.pages, args.fmt)
                print(f"  {src.name}: {count} image(s) → {dest}/")
            else:
                pages, chars = extract_text(src, dest, args.pages)
                print(f"  {src.name}: {pages} page(s), {format_bytes(chars)} text → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
