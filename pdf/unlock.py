#!/usr/bin/env python3
"""
pdf/unlock.py — PDF password removal script
Removes encryption from a password-protected PDF (requires the current password).
"""

import argparse
import sys
from pathlib import Path

try:
    import pikepdf
except ImportError:
    print("pikepdf is required: pip install pikepdf", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}


def unlock_pdf(src: Path, dest: Path, password: str) -> None:
    """Open src with the given password, save dest without encryption."""
    with pikepdf.open(src, password=password) as pdf:
        pdf.save(dest)


def main():
    parser = argparse.ArgumentParser(
        description="Remove password protection from PDF files (requires current password)."
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
        help="Output directory for unlocked PDFs.",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Current password used to decrypt the PDFs.",
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
            print(f"[dry-run] {src} → {dest} (decrypt and re-save)")
            continue

        try:
            unlock_pdf(src, dest, args.password)
            print(f"  {src.name}: decrypted → {dest}")
        except pikepdf.PasswordError:
            print(f"  ERROR {src.name}: incorrect password", file=sys.stderr)
            errors += 1
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
