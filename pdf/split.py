#!/usr/bin/env python3
"""
pdf/split.py — Split a PDF into individual pages or page ranges.
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("pypdf is required: pip install pypdf>=4.0.0", file=sys.stderr)
    sys.exit(1)


def parse_page_spec(spec: str, total_pages: int) -> list[int]:
    """Parse a page specification string into a sorted list of 0-based page indices.

    Accepts comma-separated values where each value is either a single page
    number or a range (e.g. "1,3-5,8" -> pages 1,3,4,5,8).
    Page numbers are 1-based in the spec, converted to 0-based internally.
    """
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bounds = part.split("-", 1)
            try:
                start = int(bounds[0])
                end = int(bounds[1])
            except ValueError:
                raise ValueError(f"invalid range: {part}")
            if start < 1 or end < 1:
                raise ValueError(f"page numbers must be >= 1, got: {part}")
            if start > total_pages or end > total_pages:
                raise ValueError(
                    f"page out of range: {part} (document has {total_pages} pages)"
                )
            pages.update(range(start - 1, end))
        else:
            try:
                n = int(part)
            except ValueError:
                raise ValueError(f"invalid page number: {part}")
            if n < 1 or n > total_pages:
                raise ValueError(
                    f"page out of range: {n} (document has {total_pages} pages)"
                )
            pages.add(n - 1)

    return sorted(pages)


def split_pdf(src: Path, dest: Path, page_indices: list[int]) -> int:
    """Extract the given pages from src and write them to dest.

    Returns the number of pages written.
    """
    reader = PdfReader(str(src))
    writer = PdfWriter()

    for idx in page_indices:
        writer.add_page(reader.pages[idx])

    with open(dest, "wb") as f:
        writer.write(f)

    return len(page_indices)


def split_all_pages(src: Path, output_dir: Path) -> int:
    reader = PdfReader(str(src))
    total = len(reader.pages)
    pad = len(str(total))

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        out_name = f"{src.stem}_{str(i + 1).zfill(pad)}.pdf"
        with open(output_dir / out_name, "wb") as f:
            writer.write(f)

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF into individual pages or extract page ranges."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input PDF file.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output file (with --pages) or directory (with --each-page).",
    )
    parser.add_argument(
        "--pages", "-p",
        type=str,
        default=None,
        help="Pages to extract, e.g. '1-3', '1,3,5-8'. 1-based.",
    )
    parser.add_argument(
        "--each-page",
        action="store_true",
        help="Split every page into its own file. --output is treated as a directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    if not args.pages and not args.each_page:
        parser.error("provide --pages or --each-page")
    if args.pages and args.each_page:
        parser.error("--pages and --each-page are mutually exclusive")

    if not args.input.is_file():
        print(f"Not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    reader = PdfReader(str(args.input))
    total_pages = len(reader.pages)

    if args.each_page:
        if args.dry_run:
            pad = len(str(total_pages))
            for i in range(total_pages):
                name = f"{args.input.stem}_{str(i + 1).zfill(pad)}.pdf"
                print(f"[dry-run] page {i + 1} -> {args.output / name}")
            print(f"\n{total_pages} pages would be written")
            return

        args.output.mkdir(parents=True, exist_ok=True)
        written = split_all_pages(args.input, args.output)
        print(f"Split {args.input.name} into {written} files in {args.output}")
    else:
        try:
            page_indices = parse_page_spec(args.pages, total_pages)
        except ValueError as e:
            parser.error(str(e))

        if not page_indices:
            parser.error("no pages selected")

        human_pages = [str(i + 1) for i in page_indices]

        if args.dry_run:
            print(f"[dry-run] {args.input} (pages {','.join(human_pages)}) -> {args.output}")
            return

        args.output.parent.mkdir(parents=True, exist_ok=True)
        written = split_pdf(args.input, args.output, page_indices)
        print(f"Extracted {written} page(s) ({','.join(human_pages)}) -> {args.output}")


if __name__ == "__main__":
    main()
