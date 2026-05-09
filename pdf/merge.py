#!/usr/bin/env python3
"""
pdf/merge.py — PDF merge script
Combines multiple PDF files into a single output PDF in the specified order.
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfWriter
except ImportError:
    print("pypdf is required: pip install pypdf", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}


def merge_pdfs(inputs: list[Path], dest: Path) -> int:
    """Merge PDFs in order into dest. Returns total page count written."""
    writer = PdfWriter()
    for src in inputs:
        writer.append(str(src))
    page_count = len(writer.pages)
    with open(dest, "wb") as fh:
        writer.write(fh)
    return page_count


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple PDF files into a single output PDF."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        metavar="INPUT",
        help="Input PDF files to merge, in order.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output PDF file path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    files: list[Path] = []
    for inp in args.input:
        if inp.is_file() and inp.suffix.lower() in SUPPORTED_FORMATS:
            files.append(inp)
        elif inp.is_file():
            print(f"Skipping unsupported file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] merging {len(files)} file(s) → {args.output}")
        for f in files:
            print(f"  {f}")
        sys.exit(0)

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        page_count = merge_pdfs(files, args.output)
        print(f"Merged {len(files)} file(s) ({page_count} pages) → {args.output}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
