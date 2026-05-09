#!/usr/bin/env python3
"""
pdf/html_to_pdf.py — Convert static HTML or URLs to PDF
Uses WeasyPrint for HTML→PDF rendering. Supports local HTML files and http(s) URLs.

LIMITATION: WeasyPrint does NOT execute JavaScript. For JS-rendered pages,
a headless browser (Playwright, Puppeteer) is required — see the future web
integration plan.

System dependencies (Linux): pango, cairo, gdk-pixbuf, libffi.
"""

import argparse
import sys
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    print("weasyprint is required: pip install weasyprint", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".html", ".htm"}


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def html_to_pdf(src_or_url: str, dest: Path) -> None:
    """Render src (file path or URL) to dest PDF."""
    if _is_url(src_or_url):
        HTML(url=src_or_url).write_pdf(str(dest))
    else:
        HTML(filename=src_or_url).write_pdf(str(dest))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert static HTML files or URLs to PDF using WeasyPrint. "
            "JavaScript is NOT executed — for JS-rendered pages use a headless browser."
        )
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Input HTML file(s), director(ies), or http(s) URL(s).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output file (single input) or directory (multiple inputs).",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recurse into subdirectories (only applies to directory inputs).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    sources: list[str] = []
    for inp in args.input:
        if _is_url(inp):
            sources.append(inp)
            continue
        path = Path(inp)
        if path.is_dir():
            glob = path.rglob("*") if args.recursive else path.glob("*")
            for f in glob:
                if f.suffix.lower() in SUPPORTED_FORMATS:
                    sources.append(str(f))
        elif path.is_file():
            if path.suffix.lower() in SUPPORTED_FORMATS:
                sources.append(str(path))
            else:
                print(f"Skipping unsupported file: {path}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not sources:
        print("No HTML files or URLs found.", file=sys.stderr)
        sys.exit(1)

    multi = len(sources) > 1
    if not args.dry_run:
        if multi:
            args.output.mkdir(parents=True, exist_ok=True)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)

    errors = 0

    for src in sources:
        if multi:
            stem = Path(src.rsplit("/", 1)[-1]).stem if _is_url(src) else Path(src).stem
            dest = args.output / f"{stem or 'page'}.pdf"
        else:
            dest = args.output

        if args.dry_run:
            kind = "url" if _is_url(src) else "file"
            print(f"[dry-run] {src} ({kind}) → {dest}")
            continue

        try:
            html_to_pdf(src, dest)
            print(f"  {src} → {dest}")
        except Exception as e:
            print(f"  ERROR {src}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and sources:
        print(f"\nTotal: {len(sources) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
