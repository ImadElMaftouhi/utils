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
