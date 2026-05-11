"""Tests for the pdf module (compress, merge, split, extract)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

pytest.importorskip("pypdf", reason="pypdf required for PDF tests")


class TestMerge:
    def test_merge_two_pdfs_page_count(self, sample_pdf: Path, tmp_path: Path):
        from pdf.merge import merge_pdfs

        dest = tmp_path / "merged.pdf"
        page_count = merge_pdfs([sample_pdf, sample_pdf], dest)
        assert dest.exists()
        assert page_count == 2

    def test_merge_single_pdf(self, sample_pdf: Path, tmp_path: Path):
        from pdf.merge import merge_pdfs

        dest = tmp_path / "out.pdf"
        page_count = merge_pdfs([sample_pdf], dest)
        assert page_count == 1

    def test_merge_returns_correct_total(self, sample_pdf_multi: Path, sample_pdf: Path, tmp_path: Path):
        from pdf.merge import merge_pdfs

        dest = tmp_path / "merged.pdf"
        page_count = merge_pdfs([sample_pdf_multi, sample_pdf], dest)
        assert page_count == 6


class TestSplit:
    def test_parse_page_ranges_single(self):
        from pdf.split import parse_page_ranges

        assert parse_page_ranges("1", 5) == [0]

    def test_parse_page_ranges_range(self):
        from pdf.split import parse_page_ranges

        assert parse_page_ranges("1-3", 5) == [0, 1, 2]

    def test_parse_page_ranges_mixed(self):
        from pdf.split import parse_page_ranges

        assert parse_page_ranges("1-2,4", 5) == [0, 1, 3]

    def test_parse_page_ranges_out_of_bounds(self):
        from pdf.split import parse_page_ranges

        with pytest.raises(ValueError):
            parse_page_ranges("10", 5)

    def test_split_each_page(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.split import split_pdf

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        created = split_pdf(sample_pdf_multi, out_dir, pages=None, chunk=None)
        assert len(created) == 5
        for p in created:
            assert p.exists()

    def test_split_by_chunk(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.split import split_pdf

        out_dir = tmp_path / "chunks"
        out_dir.mkdir()
        created = split_pdf(sample_pdf_multi, out_dir, pages=None, chunk=2)
        assert len(created) == 3  # 5 pages / chunk-2 → parts of 2, 2, 1

    def test_split_page_range(self, sample_pdf_multi: Path, tmp_path: Path):
        from pypdf import PdfReader

        from pdf.split import split_pdf

        out_dir = tmp_path / "range"
        out_dir.mkdir()
        created = split_pdf(sample_pdf_multi, out_dir, pages="1-3", chunk=None)
        assert len(created) == 1
        reader = PdfReader(str(created[0]))
        assert len(reader.pages) == 3


class TestExtract:
    def test_extract_text_produces_file(self, sample_pdf: Path, tmp_path: Path):
        from pdf.extract import extract_text

        dest = tmp_path / "out.txt"
        pages, chars = extract_text(sample_pdf, dest, page_spec=None)
        assert dest.exists()
        assert pages == 1

    def test_extract_text_with_page_range(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.extract import extract_text

        dest = tmp_path / "partial.txt"
        pages, _ = extract_text(sample_pdf_multi, dest, page_spec="1-2")
        assert pages == 2

    def test_format_bytes(self):
        from pdf.extract import format_bytes

        assert format_bytes(100) == "100 B"
        assert "KB" in format_bytes(1500)
        assert "MB" in format_bytes(1024 * 1024 + 1)


class TestRepair:
    def test_repair_produces_valid_pdf(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("pikepdf")
        from pypdf import PdfReader

        from pdf.repair import repair_pdf

        dest = tmp_path / "repaired.pdf"
        orig, repaired = repair_pdf(sample_pdf, dest)
        assert dest.exists()
        assert orig > 0
        assert repaired > 0
        # Output is openable
        reader = PdfReader(str(dest))
        assert len(reader.pages) == 1

    def test_repair_format_bytes(self):
        from pdf.repair import format_bytes

        assert format_bytes(100) == "100 B"
        assert "KB" in format_bytes(1500)


class TestRedact:
    def test_parse_region_valid(self):
        from pdf.redact import parse_region

        assert parse_region("10,20,100,50") == (10.0, 20.0, 100.0, 50.0)

    def test_parse_region_wrong_arity(self):
        from pdf.redact import parse_region

        with pytest.raises(ValueError, match="x,y,w,h"):
            parse_region("10,20,30")

    def test_parse_region_negative_size(self):
        from pdf.redact import parse_region

        with pytest.raises(ValueError, match="positive"):
            parse_region("0,0,-5,10")

    def test_redact_all_pages(self, sample_pdf_multi: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.redact import redact_pdf

        dest = tmp_path / "redacted.pdf"
        regions = [(50.0, 100.0, 200.0, 30.0)]
        count = redact_pdf(sample_pdf_multi, dest, regions, pages_spec=None)
        assert dest.exists()
        assert count == 5

    def test_redact_subset(self, sample_pdf_multi: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.redact import redact_pdf

        dest = tmp_path / "redacted.pdf"
        regions = [(50.0, 100.0, 200.0, 30.0)]
        count = redact_pdf(sample_pdf_multi, dest, regions, pages_spec="1-2")
        assert count == 2

    def test_redact_empty_regions_raises(self, sample_pdf: Path, tmp_path: Path):
        from pdf.redact import redact_pdf

        with pytest.raises(ValueError, match="region"):
            redact_pdf(sample_pdf, tmp_path / "out.pdf", regions=[], pages_spec=None)
class TestImagesToPdf:
    def test_single_image_to_pdf(self, sample_jpeg: Path, tmp_path: Path):
        pytest.importorskip("PIL")
        from pypdf import PdfReader

        from pdf.images_to_pdf import images_to_pdf

        dest = tmp_path / "single.pdf"
        count = images_to_pdf([sample_jpeg], dest, page_size="auto", margin=0)
        assert dest.exists()
        assert count == 1
        reader = PdfReader(str(dest))
        assert len(reader.pages) == 1

    def test_multiple_images_to_pdf(self, sample_jpeg: Path, sample_png: Path, tmp_path: Path):
        pytest.importorskip("PIL")
        from pypdf import PdfReader

        from pdf.images_to_pdf import images_to_pdf

        dest = tmp_path / "album.pdf"
        count = images_to_pdf([sample_jpeg, sample_png, sample_jpeg], dest,
                               page_size="auto", margin=0)
        assert count == 3
        reader = PdfReader(str(dest))
        assert len(reader.pages) == 3

    def test_fixed_page_size_a4(self, sample_jpeg: Path, tmp_path: Path):
        pytest.importorskip("PIL")
        from pdf.images_to_pdf import images_to_pdf

        dest = tmp_path / "a4.pdf"
        count = images_to_pdf([sample_jpeg], dest, page_size="A4", margin=20)
        assert count == 1
        assert dest.exists()

    def test_empty_list_raises(self, tmp_path: Path):
        from pdf.images_to_pdf import images_to_pdf

        with pytest.raises(ValueError, match="No images"):
            images_to_pdf([], tmp_path / "x.pdf", page_size="auto", margin=0)

    def test_unknown_page_size_raises(self, sample_jpeg: Path, tmp_path: Path):
        pytest.importorskip("PIL")
        from pdf.images_to_pdf import images_to_pdf

        with pytest.raises(ValueError, match="Unknown page size"):
            images_to_pdf([sample_jpeg], tmp_path / "x.pdf", page_size="A3", margin=0)
class TestProtect:
    def test_protect_creates_encrypted_pdf(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("pikepdf")
        import pikepdf

        from pdf.protect import protect_pdf

        dest = tmp_path / "locked.pdf"
        protect_pdf(sample_pdf, dest, user_password="secret", owner_password=None,
                    allow_print=True, allow_copy=True)
        assert dest.exists()
        # Confirm the file is actually encrypted
        with pytest.raises(pikepdf.PasswordError):
            pikepdf.open(dest)
        # Confirm the password works
        with pikepdf.open(dest, password="secret") as pdf:
            assert len(pdf.pages) == 1

    def test_protect_no_print_permission(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("pikepdf")
        import pikepdf

        from pdf.protect import protect_pdf

        dest = tmp_path / "locked.pdf"
        protect_pdf(sample_pdf, dest, user_password="x", owner_password=None,
                    allow_print=False, allow_copy=True)
        with pikepdf.open(dest, password="x") as pdf:
            assert pdf.allow.print_lowres is False


class TestUnlock:
    def test_unlock_removes_encryption(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("pikepdf")
        import pikepdf

        from pdf.protect import protect_pdf
        from pdf.unlock import unlock_pdf

        locked = tmp_path / "locked.pdf"
        protect_pdf(sample_pdf, locked, user_password="key", owner_password=None,
                    allow_print=True, allow_copy=True)

        unlocked = tmp_path / "open.pdf"
        unlock_pdf(locked, unlocked, password="key")
        assert unlocked.exists()
        # No password should be required now
        with pikepdf.open(unlocked) as pdf:
            assert len(pdf.pages) == 1

    def test_unlock_wrong_password_raises(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("pikepdf")
        import pikepdf

        from pdf.protect import protect_pdf
        from pdf.unlock import unlock_pdf

        locked = tmp_path / "locked.pdf"
        protect_pdf(sample_pdf, locked, user_password="right", owner_password=None,
                    allow_print=True, allow_copy=True)
        with pytest.raises(pikepdf.PasswordError):
            unlock_pdf(locked, tmp_path / "out.pdf", password="wrong")
class TestWatermark:
    def test_watermark_text_stamps_all_pages(self, sample_pdf_multi: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.watermark import watermark_text

        dest = tmp_path / "wm.pdf"
        count = watermark_text(
            sample_pdf_multi, dest, text="DRAFT", opacity=0.3, angle=45,
            position="center", font_size=72, pages_spec=None,
        )
        assert dest.exists()
        assert count == 5

    def test_watermark_text_subset(self, sample_pdf_multi: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.watermark import watermark_text

        dest = tmp_path / "wm.pdf"
        count = watermark_text(
            sample_pdf_multi, dest, text="X", opacity=0.5, angle=0,
            position="bottom-right", font_size=24, pages_spec="1-2",
        )
        assert count == 2

    def test_watermark_image_stamps_pages(self, sample_pdf: Path, sample_png: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.watermark import watermark_image

        dest = tmp_path / "wm.pdf"
        count = watermark_image(sample_pdf, dest, sample_png, opacity=0.5, position="center", pages_spec=None)
        assert dest.exists()
        assert count == 1


class TestPaginate:
    def test_paginate_default_format(self, sample_pdf_multi: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.paginate import add_page_numbers

        dest = tmp_path / "numbered.pdf"
        count = add_page_numbers(
            sample_pdf_multi, dest, fmt="Page {n} of {total}",
            position="bottom-center", start=1, font_size=10,
        )
        assert dest.exists()
        assert count == 5

    def test_paginate_with_offset_start(self, sample_pdf_multi: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.paginate import add_page_numbers

        dest = tmp_path / "numbered.pdf"
        count = add_page_numbers(
            sample_pdf_multi, dest, fmt="{n}",
            position="top-right", start=10, font_size=12,
        )
        assert count == 5

    def test_paginate_custom_format(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("reportlab")
        from pdf.paginate import add_page_numbers

        dest = tmp_path / "numbered.pdf"
        count = add_page_numbers(
            sample_pdf, dest, fmt="-- {n} --",
            position="bottom-left", start=1, font_size=8,
        )
        assert count == 1
class TestRotate:
    def test_rotate_all_pages(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.rotate import rotate_pdf

        dest = tmp_path / "rotated.pdf"
        count = rotate_pdf(sample_pdf_multi, dest, angle=90, pages_spec=None)
        assert dest.exists()
        assert count == 5

    def test_rotate_subset(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.rotate import rotate_pdf

        dest = tmp_path / "rotated.pdf"
        count = rotate_pdf(sample_pdf_multi, dest, angle=180, pages_spec="1-2")
        assert count == 2

    def test_rotate_invalid_pages(self, sample_pdf: Path, tmp_path: Path):
        from pdf.rotate import rotate_pdf

        dest = tmp_path / "out.pdf"
        with pytest.raises(ValueError):
            rotate_pdf(sample_pdf, dest, angle=90, pages_spec="10")


class TestOrganize:
    def test_reorder_pages(self, sample_pdf_multi: Path, tmp_path: Path):
        from pypdf import PdfReader

        from pdf.organize import organize_pdf

        dest = tmp_path / "reordered.pdf"
        count = organize_pdf(sample_pdf_multi, dest, order_spec="5,4,3,2,1")
        assert count == 5
        reader = PdfReader(str(dest))
        assert len(reader.pages) == 5

    def test_drop_pages(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.organize import organize_pdf

        dest = tmp_path / "trimmed.pdf"
        count = organize_pdf(sample_pdf_multi, dest, order_spec="1,3,5")
        assert count == 3

    def test_duplicate_pages(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.organize import organize_pdf

        dest = tmp_path / "dup.pdf"
        count = organize_pdf(sample_pdf_multi, dest, order_spec="1,1,2,2")
        assert count == 4

    def test_parse_order_range(self):
        from pdf.organize import parse_order_spec

        assert parse_order_spec("1-3", 5) == [0, 1, 2]

    def test_parse_order_invalid(self):
        from pdf.organize import parse_order_spec

        with pytest.raises(ValueError):
            parse_order_spec("99", 5)


class TestCrop:
    def test_crop_uniform_margin(self, sample_pdf_multi: Path, tmp_path: Path):
        from pypdf import PdfReader

        from pdf.crop import crop_pdf

        dest = tmp_path / "cropped.pdf"
        count = crop_pdf(sample_pdf_multi, dest, top=10, right=10, bottom=10, left=10, pages_spec=None)
        assert count == 5
        reader = PdfReader(str(dest))
        page0 = reader.pages[0]
        # original cropbox was 612 x 792; cropped by 10 each side = 592 x 772
        assert float(page0.cropbox.width) == 592
        assert float(page0.cropbox.height) == 772

    def test_crop_subset(self, sample_pdf_multi: Path, tmp_path: Path):
        from pdf.crop import crop_pdf

        dest = tmp_path / "cropped.pdf"
        count = crop_pdf(sample_pdf_multi, dest, top=20, right=0, bottom=0, left=0, pages_spec="1-2")
        assert count == 2

    def test_crop_too_much_raises(self, sample_pdf: Path, tmp_path: Path):
        from pdf.crop import crop_pdf

        dest = tmp_path / "out.pdf"
        with pytest.raises(ValueError, match="exceed"):
            crop_pdf(sample_pdf, dest, top=500, right=500, bottom=500, left=500, pages_spec=None)
