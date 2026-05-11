#!/usr/bin/env python3
"""
pdf/protect.py — PDF password protection script
Encrypts PDFs with a password and configurable permission flags.
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


def protect_pdf(
    src: Path,
    dest: Path,
    user_password: str,
    owner_password: str | None,
    allow_print: bool,
    allow_copy: bool,
) -> None:
    """Encrypt src with the given password(s) and permissions, write to dest."""
    permissions = pikepdf.Permissions(
        extract=allow_copy,
        modify_annotation=False,
        modify_assembly=False,
        modify_form=False,
        modify_other=False,
        print_lowres=allow_print,
        print_highres=allow_print,
    )
    encryption = pikepdf.Encryption(
        user=user_password,
        owner=owner_password or user_password,
        R=6,  # AES-256
        allow=permissions,
    )

    with pikepdf.open(src) as pdf:
        pdf.save(dest, encryption=encryption)


def main():
    parser = argparse.ArgumentParser(
        description="Add password protection (AES-256) to PDF files."
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
        help="Output directory for protected PDFs.",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="User password (required to open the PDF).",
    )
    parser.add_argument(
        "--owner-password",
        help="Owner password (defaults to user password if omitted).",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Disallow printing.",
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Disallow text/image extraction.",
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

    if not args.password:
        parser.error("--password cannot be empty")

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
            perms = []
            if args.no_print:
                perms.append("no-print")
            if args.no_copy:
                perms.append("no-copy")
            perm_label = ", ".join(perms) if perms else "default perms"
            print(f"[dry-run] {src} → {dest} (encrypt AES-256, {perm_label})")
            continue

        try:
            protect_pdf(
                src,
                dest,
                args.password,
                args.owner_password,
                allow_print=not args.no_print,
                allow_copy=not args.no_copy,
            )
            print(f"  {src.name}: encrypted → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
