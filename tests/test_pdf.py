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
