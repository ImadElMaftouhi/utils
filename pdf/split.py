#!/usr/bin/env python3
"""
pdf/split.py — PDF split script
Splits a PDF into individual pages, page ranges, or fixed-size chunks.
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
    """Parse a page range string into a sorted list of 0-based page indices.

    Spec format: "1-3,5,7-9" (1-based, inclusive). Raises ValueError on invalid input.
    """
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


def split_pdf(src: Path, output_dir: Path, pages: str | None, chunk: int | None) -> list[Path]:
    """Split src into output files in output_dir. Returns list of created paths."""
    reader = PdfReader(str(src))
    total = len(reader.pages)
    stem = src.stem
    created: list[Path] = []

    if chunk is not None:
        for part_num, start in enumerate(range(0, total, chunk), start=1):
            end = min(start + chunk, total)
            writer = PdfWriter()
            for i in range(start, end):
                writer.add_page(reader.pages[i])
            out = output_dir / f"{stem}_part{part_num:03d}.pdf"
            with open(out, "wb") as fh:
                writer.write(fh)
            created.append(out)
    elif pages is not None:
        indices = parse_page_ranges(pages, total)
        writer = PdfWriter()
        for i in indices:
            writer.add_page(reader.pages[i])
        out = output_dir / f"{stem}_pages.pdf"
        with open(out, "wb") as fh:
            writer.write(fh)
        created.append(out)
    else:
        for i in range(total):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            out = output_dir / f"{stem}_page{i + 1:04d}.pdf"
            with open(out, "wb") as fh:
                writer.write(fh)
            created.append(out)

    return created


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF into individual pages, page ranges, or chunks."
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
        help="Output directory for split PDF files.",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--pages",
        metavar="RANGE",
        help='Page range to extract, e.g. "1-3,5,7-9" (1-based).',
    )
    mode.add_argument(
        "--chunk",
        type=int,
        metavar="N",
        help="Split into chunks of N pages each.",
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

    if args.chunk is not None and args.chunk < 1:
        parser.error("--chunk must be at least 1")

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

    total_out = 0
    errors = 0

    for src in files:
        if args.dry_run:
            mode_desc = (
                f"pages={args.pages}" if args.pages
                else f"chunk={args.chunk}" if args.chunk
                else "each-page"
            )
            print(f"[dry-run] {src} → {args.output}/ ({mode_desc})")
            continue

        try:
            created = split_pdf(src, args.output, args.pages, args.chunk)
            total_out += len(created)
            print(f"  {src.name}: {len(created)} file(s) → {args.output}/")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {total_out} file(s) created | {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
