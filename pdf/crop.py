#!/usr/bin/env python3
"""
pdf/crop.py — PDF page cropping script
Trims page margins by adjusting the cropbox.
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("pypdf is required: pip install pypdf", file=sys.stderr)
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


def crop_pdf(
    src: Path,
    dest: Path,
    top: int,
    right: int,
    bottom: int,
    left: int,
    pages_spec: str | None,
) -> int:
    """Crop margins on selected pages and write to dest. Returns count of cropped pages."""
    reader = PdfReader(str(src))
    writer = PdfWriter()
    total = len(reader.pages)
    targets = set(parse_page_ranges(pages_spec, total)) if pages_spec else set(range(total))

    cropped = 0
    for i, page in enumerate(reader.pages):
        if i in targets and (top or right or bottom or left):
            box = page.cropbox
            new_lower_left_x = float(box.lower_left[0]) + left
            new_lower_left_y = float(box.lower_left[1]) + bottom
            new_upper_right_x = float(box.upper_right[0]) - right
            new_upper_right_y = float(box.upper_right[1]) - top

            if new_upper_right_x <= new_lower_left_x or new_upper_right_y <= new_lower_left_y:
                raise ValueError(
                    f"Page {i + 1}: crop margins exceed page size"
                )

            page.cropbox.lower_left = (new_lower_left_x, new_lower_left_y)
            page.cropbox.upper_right = (new_upper_right_x, new_upper_right_y)
            cropped += 1
        writer.add_page(page)

    with open(dest, "wb") as fh:
        writer.write(fh)

    return cropped


def main():
    parser = argparse.ArgumentParser(
        description="Crop PDF page margins (in points; 72 pt = 1 in)."
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
        help="Output directory for cropped PDFs.",
    )
    parser.add_argument("--top", type=int, default=0, help="Top margin to crop (points).")
    parser.add_argument("--right", type=int, default=0, help="Right margin to crop (points).")
    parser.add_argument("--bottom", type=int, default=0, help="Bottom margin to crop (points).")
    parser.add_argument("--left", type=int, default=0, help="Left margin to crop (points).")
    parser.add_argument(
        "--margin",
        type=int,
        metavar="N",
        help="Uniform margin to crop on all four sides (overrides individual flags).",
    )
    parser.add_argument(
        "--pages",
        metavar="RANGE",
        help='Page range to crop, e.g. "1-3,5". Default: all pages.',
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

    if args.margin is not None:
        if args.margin < 0:
            parser.error("--margin must be 0 or greater")
        top = right = bottom = left = args.margin
    else:
        top, right, bottom, left = args.top, args.right, args.bottom, args.left

    if not (top or right or bottom or left):
        parser.error("Specify at least one of --top/--right/--bottom/--left or --margin")

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

    total_cropped = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            margins = f"T{top} R{right} B{bottom} L{left}"
            scope = f"pages={args.pages}" if args.pages else "all pages"
            print(f"[dry-run] {src} → {dest} (crop {margins}, {scope})")
            continue

        try:
            count = crop_pdf(src, dest, top, right, bottom, left, args.pages)
            total_cropped += count
            print(f"  {src.name}: cropped {count} page(s) → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(
            f"\nTotal: {total_cropped} page(s) cropped | "
            f"{len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
