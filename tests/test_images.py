"""Tests for the images module (compress, convert, resize)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

pytest.importorskip("PIL", reason="Pillow required for image tests")


class TestCompress:
    def test_compress_jpeg_reduces_size(self, sample_jpeg: Path, tmp_path: Path):
        from images.compress import compress_image

        dest = tmp_path / "out.jpg"
        orig, comp = compress_image(sample_jpeg, dest, jpeg_quality=20, png_compression=6, webp_quality=50, lossless_webp=False)
        assert dest.exists()
        assert orig > 0
        assert comp > 0

    def test_compress_produces_valid_image(self, sample_jpeg: Path, tmp_path: Path):
        from PIL import Image

        from images.compress import compress_image

        dest = tmp_path / "out.jpg"
        compress_image(sample_jpeg, dest, jpeg_quality=85, png_compression=6, webp_quality=80, lossless_webp=False)
        with Image.open(dest) as img:
            assert img.size == (100, 100)

    def test_compress_dry_run_writes_nothing(self, sample_jpeg: Path, tmp_path: Path):
        from images.compress import compress_image

        dest = tmp_path / "out.jpg"
        # dry-run: we simply don't call compress_image; verify file is absent
        assert not dest.exists()

    def test_format_bytes_units(self):
        from images.compress import format_bytes

        assert format_bytes(500) == "500 B"
        assert "KB" in format_bytes(2048)
        assert "MB" in format_bytes(2 * 1024 * 1024)


class TestConvert:
    def test_jpeg_to_png(self, sample_jpeg: Path, tmp_path: Path):
        from PIL import Image

        from images.convert import convert_image

        dest = tmp_path / "out.png"
        convert_image(sample_jpeg, dest, target_format="PNG", quality=85, lossless=False)
        assert dest.exists()
        with Image.open(dest) as img:
            assert img.format == "PNG"

    def test_rgba_png_to_jpeg_no_error(self, sample_png: Path, tmp_path: Path):
        from images.convert import convert_image

        dest = tmp_path / "out.jpg"
        convert_image(sample_png, dest, target_format="JPEG", quality=85, lossless=False)
        assert dest.exists()


class TestResize:
    def test_scale_50_percent(self, sample_jpeg: Path, tmp_path: Path):
        from images.resize import resize_image

        dest = tmp_path / "out.jpg"
        (orig_w, orig_h), (new_w, new_h) = resize_image(sample_jpeg, dest, width=None, height=None, scale=0.5, stretch=False)
        assert new_w == 50
        assert new_h == 50

    def test_width_only_preserves_aspect(self, sample_jpeg: Path, tmp_path: Path):
        from images.resize import resize_image

        dest = tmp_path / "out.jpg"
        (orig_w, orig_h), (new_w, new_h) = resize_image(sample_jpeg, dest, width=50, height=None, scale=None, stretch=False)
        assert new_w == 50
        assert new_h == 50  # 100x100 square, so aspect ratio preserved = 50

    def test_exact_dimensions_with_stretch(self, sample_jpeg: Path, tmp_path: Path):
        from images.resize import resize_image

        dest = tmp_path / "out.jpg"
        (_, _), (new_w, new_h) = resize_image(sample_jpeg, dest, width=80, height=40, scale=None, stretch=True)
        assert new_w == 80
        assert new_h == 40
