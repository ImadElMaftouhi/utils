#!/usr/bin/env python3
"""
pdf/compress.py — PDF compression script
Reduces PDF file size by recompressing streams, down-sampling images,
and removing duplicate objects. Uses pikepdf for lossless stream-level
optimisation and Pillow for optional lossy image recompression.
"""

import argparse
import sys
from pathlib import Path

try:
    import pikepdf
except ImportError:
    print("pikepdf is required: pip install pikepdf>=8.0.0", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    Image = None  # Pillow is optional — needed only for --image-quality


def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024 ** 2:.1f} MB"


def _recompress_images(pdf: pikepdf.Pdf, image_quality: int) -> int:
    """Re-encode raster images inside the PDF at *image_quality* (1-95).

    Returns the number of images recompressed.
    """
    if Image is None:
        print(
            "Pillow is required for --image-quality: pip install Pillow",
            file=sys.stderr,
        )
        sys.exit(1)

    import io

    count = 0
    for page in pdf.pages:
        try:
            resources = page.get("/Resources", {})
            xobjects = resources.get("/XObject", {})
        except Exception:
            continue

        for key in list(xobjects.keys()):
            obj = xobjects[key]
            if not isinstance(obj, pikepdf.Stream):
                continue
            if obj.get("/Subtype") != pikepdf.Name.Image:
                continue

            width = int(obj.get("/Width", 0))
            height = int(obj.get("/Height", 0))
            if width == 0 or height == 0:
                continue

            try:
                raw = obj.read_bytes()
            except Exception:
                continue

            # Determine colour mode from the PDF colour space
            cs = obj.get("/ColorSpace", pikepdf.Name.DeviceRGB)
            if cs == pikepdf.Name.DeviceGray:
                mode = "L"
            elif cs == pikepdf.Name.DeviceCMYK:
                mode = "CMYK"
            else:
                mode = "RGB"

            expected_bytes = width * height * len(mode)
            if len(raw) != expected_bytes:
                # Compressed/encoded in a way we cannot trivially decode
                continue

            try:
                pil_img = Image.frombytes(mode, (width, height), raw)
                if mode == "CMYK":
                    pil_img = pil_img.convert("RGB")
                    mode = "RGB"

                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=image_quality, optimize=True)
                jpeg_data = buf.getvalue()

                obj.write(jpeg_data, filter=pikepdf.Name.DCTDecode)
                obj["/ColorSpace"] = (
                    pikepdf.Name.DeviceGray if mode == "L" else pikepdf.Name.DeviceRGB
                )
                count += 1
            except Exception:
                continue

    return count


def compress_pdf(
    src: Path,
    dest: Path,
    image_quality: int | None,
) -> tuple[int, int]:
    """Compress a single PDF. Returns (original_size, compressed_size)."""
    original_size = src.stat().st_size

    with pikepdf.open(src) as pdf:
        if image_quality is not None:
            _recompress_images(pdf, image_quality)

        pdf.remove_unreferenced_resources()

        pdf.save(
            dest,
            compress_streams=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            recompress_flate=True,
        )

    compressed_size = dest.stat().st_size
    return original_size, compressed_size


def main():
    parser = argparse.ArgumentParser(
        description="Reduce PDF file size by recompressing streams and images."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input PDF file(s) or director(ies).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output directory for compressed PDFs.",
    )
    parser.add_argument(
        "--image-quality",
        type=int,
        default=None,
        metavar="1-95",
        help="Re-encode embedded images at this JPEG quality (1-95). "
             "Omit for lossless stream-only compression. Requires Pillow.",
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

    # Validate
    if args.image_quality is not None and not (1 <= args.image_quality <= 95):
        parser.error("--image-quality must be between 1 and 95")

    # Collect input files
    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*.pdf") if args.recursive else inp.glob("*.pdf")
            files.extend(glob)
        elif inp.is_file():
            if inp.suffix.lower() == ".pdf":
                files.append(inp)
            else:
                print(f"Skipping non-PDF file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    total_original = 0
    total_compressed = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} -> {dest}")
            continue

        try:
            orig, comp = compress_pdf(src, dest, args.image_quality)
            total_original += orig
            total_compressed += comp
            savings_pct = (1 - comp / orig) * 100 if orig else 0
            print(
                f"  {src.name}: {format_bytes(orig)} -> {format_bytes(comp)}"
                f" ({savings_pct:+.1f}%)"
            )
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        total_savings = (
            (1 - total_compressed / total_original) * 100
            if total_original else 0
        )
        print(
            f"\nTotal: {format_bytes(total_original)} -> {format_bytes(total_compressed)}"
            f" ({total_savings:+.1f}%) | {len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
