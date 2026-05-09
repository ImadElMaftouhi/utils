#!/usr/bin/env python3
"""
pdf/pdf_to_word.py — Convert PDF to DOCX
Uses pdf2docx for layout-aware conversion. Fidelity varies with source layout —
complex tables, multi-column layouts, and embedded fonts may not survive perfectly.
"""

import argparse
import sys
from pathlib import Path

try:
    from pdf2docx import Converter
except ImportError:
    print("pdf2docx is required: pip install pdf2docx", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}


def pdf_to_word(src: Path, dest: Path) -> None:
    """Convert src PDF into dest DOCX."""
    cv = Converter(str(src))
    try:
        cv.convert(str(dest))
    finally:
        cv.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert PDF files to DOCX. Best-effort fidelity — "
            "complex layouts may not convert perfectly."
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
        help="Output directory for DOCX files.",
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
        dest = args.output / f"{src.stem}.docx"

        if args.dry_run:
            print(f"[dry-run] {src} → {dest}")
            continue

        try:
            pdf_to_word(src, dest)
            print(f"  {src.name} → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
