#!/usr/bin/env python3
"""
images/convert.py — Image format conversion script
Converts between JPEG, PNG, WebP, and AVIF via CLI arguments.
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, features
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)


SUPPORTED_INPUT_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

# Maps CLI format name → (output extension, Pillow format string)
FORMAT_MAP = {
    "jpeg": (".jpg", "JPEG"),
    "jpg":  (".jpg", "JPEG"),
    "png":  (".png", "PNG"),
    "webp": (".webp", "WEBP"),
    "avif": (".avif", "AVIF"),
}


def prepare_for_jpeg(img: Image.Image) -> Image.Image:
    """Flatten alpha channel onto a white background for JPEG output."""
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def convert_image(src: Path, dest: Path, pillow_format: str) -> None:
    """Convert a single image to the target format."""
    with Image.open(src) as img:
        exif = img.info.get("exif", b"")

        if pillow_format == "JPEG":
            img = prepare_for_jpeg(img)
            img.save(dest, format="JPEG", exif=exif)
        else:
            img.save(dest, format=pillow_format)


def main():
    parser = argparse.ArgumentParser(
        description="Convert JPEG, PNG, WebP, and AVIF images to a target format."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input image file(s) or director(ies).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output directory for converted images.",
    )
    parser.add_argument(
        "--format", "-f",
        required=True,
        choices=list(FORMAT_MAP.keys()),
        metavar="FORMAT",
        help=f"Target format: {', '.join(FORMAT_MAP.keys())}.",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recurse into subdirectories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    ext, pillow_format = FORMAT_MAP[args.format]

    # Check AVIF support early
    if pillow_format == "AVIF" and not features.check("avif"):
        print(
            "Error: AVIF is not supported by your Pillow installation.\n"
            "Install a Pillow build with AVIF support, or install the pillow-avif-plugin package:\n"
            "  pip install pillow-avif-plugin",
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect input files
    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*") if args.recursive else inp.glob("*")
            files.extend(f for f in glob if f.suffix.lower() in SUPPORTED_INPUT_FORMATS)
        elif inp.is_file():
            if inp.suffix.lower() in SUPPORTED_INPUT_FORMATS:
                files.append(inp)
            else:
                print(f"Skipping unsupported file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No supported image files found.", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    errors = 0

    for src in files:
        dest = args.output / (src.stem + ext)

        if args.dry_run:
            print(f"[dry-run] {src} → {dest}")
            continue

        try:
            convert_image(src, dest, pillow_format)
            print(f"  {src.name} → {dest.name}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        ok = len(files) - errors
        print(f"\nTotal: {ok} ok, {errors} errors")


if __name__ == "__main__":
    main()
