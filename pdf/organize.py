#!/usr/bin/env python3
"""
pdf/organize.py — PDF page organizer
Reorders, deletes, or duplicates pages by an explicit order spec.
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


def parse_order_spec(spec: str, total: int) -> list[int]:
    """Parse "3,1,2,5-7" into a list of 0-based page indices in the requested order.

    Repetition is allowed; pages omitted from the spec are dropped from the output.
    """
    indices: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start < 1 or end > total or start > end:
                raise ValueError(f"Page range {part!r} is out of bounds (1–{total})")
            indices.extend(range(start - 1, end))
        else:
            page = int(part)
            if page < 1 or page > total:
                raise ValueError(f"Page {page} is out of bounds (1–{total})")
            indices.append(page - 1)
    if not indices:
        raise ValueError("Order spec produced no pages")
    return indices


def organize_pdf(src: Path, dest: Path, order_spec: str) -> int:
    """Rebuild src into dest using the given order spec. Returns output page count."""
    reader = PdfReader(str(src))
    total = len(reader.pages)
    order = parse_order_spec(order_spec, total)

    writer = PdfWriter()
    for i in order:
        writer.add_page(reader.pages[i])

    with open(dest, "wb") as fh:
        writer.write(fh)

    return len(order)


def main():
    parser = argparse.ArgumentParser(
        description="Reorder, delete, or duplicate pages in a PDF using an order spec."
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
        help="Output directory for rebuilt PDFs.",
    )
    parser.add_argument(
        "--order",
        required=True,
        metavar="SPEC",
        help='New page order, e.g. "3,1,2,5-7". Pages not listed are dropped.',
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

    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} → {dest} (order: {args.order})")
            continue

        try:
            count = organize_pdf(src, dest, args.order)
            print(f"  {src.name}: → {count} page(s) → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
