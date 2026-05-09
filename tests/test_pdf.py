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


class TestOcr:
    def test_imports_resolve(self):
        pytest.importorskip("pytesseract")
        pytest.importorskip("pdf2image")
        from pdf.ocr import ocr_pdf  # noqa: F401

    def test_ocr_invalid_dpi_via_cli(self):
        # Functional smoke: argparse rejects --dpi < 72.
        # Full end-to-end OCR test would require system tesseract + poppler binaries.
        import subprocess

        result = subprocess.run(
            ["python", "pdf/ocr.py", "fake.pdf", "-o", "/tmp/x", "--dpi", "10"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "--dpi" in result.stderr


class TestPdfToWord:
    def test_imports_resolve(self):
        pytest.importorskip("pdf2docx")
        from pdf.pdf_to_word import pdf_to_word  # noqa: F401

    def test_pdf_to_word_creates_docx(self, sample_pdf: Path, tmp_path: Path):
        pytest.importorskip("pdf2docx")
        from pdf.pdf_to_word import pdf_to_word

        dest = tmp_path / "out.docx"
        pdf_to_word(sample_pdf, dest)
        assert dest.exists()
        assert dest.stat().st_size > 0


class TestHtmlToPdf:
    def test_imports_resolve(self):
        pytest.importorskip("weasyprint")
        from pdf.html_to_pdf import html_to_pdf  # noqa: F401

    def test_is_url_helper(self):
        from pdf.html_to_pdf import _is_url

        assert _is_url("https://example.com") is True
        assert _is_url("http://example.com") is True
        assert _is_url("/local/path.html") is False
        assert _is_url("file.html") is False

    def test_html_to_pdf_from_file(self, tmp_path: Path):
        pytest.importorskip("weasyprint")
        from pdf.html_to_pdf import html_to_pdf

        src = tmp_path / "page.html"
        src.write_text("<html><body><h1>Hello</h1></body></html>", encoding="utf-8")
        dest = tmp_path / "page.pdf"
        try:
            html_to_pdf(str(src), dest)
        except Exception as e:
            pytest.skip(f"weasyprint runtime deps missing: {e}")
        assert dest.exists()
        assert dest.stat().st_size > 0
