#!/usr/bin/env python3
"""
pdf/merge.py — Merge multiple PDFs into one.
Supports ordering via CLI; usable as a module.
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("pypdf is required: pip install pypdf", file=sys.stderr)
    sys.exit(1)


def merge_pdfs(input_paths: list[Path], output_path: Path) -> None:
    """Merge PDF files in order into a single output file."""
    writer = PdfWriter()
    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple PDFs into one file."
    )
    parser.add_argument(
        "--inputs", "-i",
        nargs="+",
        type=Path,
        required=True,
        help="Input PDF files (order preserved).",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Output merged PDF path.",
    )
    args = parser.parse_args()

    for p in args.inputs:
        if not p.suffix.lower() == ".pdf":
            parser.error(f"Expected PDF file: {p}")

    try:
        merge_pdfs(args.inputs, args.output)
        print(f"Merged {len(args.inputs)} file(s) → {args.output}")
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
