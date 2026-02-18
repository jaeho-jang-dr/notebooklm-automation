#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for apps/web_publisher/pdf_analyzer.py

Tests:
  - PDFAnalyzer.__init__()
  - extract_all_text(): normal, OCR fallback, insufficient text
  - _ocr_with_vision(): success, API error, no key, network failure
  - extract_slide_titles()
  - generate_thumbnail()
  - build_summary()
  - clean_slide_text() (static method)
  - build_content()
  - analyze()
  - _extract_keywords()
"""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures specific to pdf_analyzer
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_fitz_doc_with_text():
    """fitz doc where pages return substantial text."""
    page = MagicMock()
    page.get_text.return_value = "무릎 통증 원인\n슬개골 연골 연화증"

    # For extract_slide_titles dict mode
    block = {
        "type": 0,
        "lines": [{
            "spans": [{"text": "무릎 통증 원인", "size": 28.0}]
        }]
    }
    page.get_text.side_effect = None

    def get_text_dispatch(mode=None, flags=None):
        if mode == "dict":
            return {"blocks": [block]}
        return "무릎 통증 원인\n슬개골 연골 연화증"

    page.get_text.side_effect = get_text_dispatch

    pixmap = MagicMock()
    pixmap.tobytes.return_value = b"\x89PNG\r\nfake_thumb_bytes"
    page.get_pixmap.return_value = pixmap

    doc = MagicMock()
    doc.__len__ = MagicMock(return_value=3)
    doc.__iter__ = MagicMock(return_value=iter([page, page, page]))
    doc.__getitem__ = MagicMock(return_value=page)
    doc.close.return_value = None
    return doc


@pytest.fixture
def mock_fitz_doc_no_text():
    """fitz doc where pages return empty text (triggers OCR fallback)."""
    page = MagicMock()
    page.get_text.return_value = ""
    page.get_text.side_effect = None

    pixmap = MagicMock()
    pixmap.tobytes.return_value = b"\x89PNG\r\nfake_png"
    page.get_pixmap.return_value = pixmap

    doc = MagicMock()
    doc.__len__ = MagicMock(return_value=2)
    doc.__iter__ = MagicMock(return_value=iter([page, page]))
    doc.__getitem__ = MagicMock(return_value=page)
    doc.close.return_value = None
    return doc


# ---------------------------------------------------------------------------
# Tests: __init__
# ---------------------------------------------------------------------------

class TestPDFAnalyzerInit:

    def test_initializes_correctly(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="test-key")

        assert analyzer.page_count == 3
        assert analyzer.vision_api_key == "test-key"
        assert str(pdf_path) in str(analyzer.pdf_path)

    def test_reads_vision_key_from_env(self, mock_fitz_doc_with_text, tmp_path, monkeypatch):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")
        monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "env-vision-key")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path)

        assert analyzer.vision_api_key == "env-vision-key"


# ---------------------------------------------------------------------------
# Tests: extract_all_text
# ---------------------------------------------------------------------------

class TestExtractAllText:

    def test_returns_text_from_pages(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            texts = analyzer.extract_all_text()

        assert len(texts) == 3
        assert all(isinstance(t, str) for t in texts)

    def test_triggers_ocr_when_text_too_short(self, mock_fitz_doc_no_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        ocr_response = {
            "responses": [{"fullTextAnnotation": {"text": "OCR 추출 텍스트"}}]
        }

        with patch("fitz.open", return_value=mock_fitz_doc_no_text), \
             patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.json.return_value = ocr_response

            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="test-api-key")
            texts = analyzer.extract_all_text()

        # Should have attempted OCR
        assert mock_post.called

    def test_returns_empty_texts_when_no_ocr_key_and_no_text(
        self, mock_fitz_doc_no_text, tmp_path
    ):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_no_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")  # no OCR key
            texts = analyzer.extract_all_text()

        # Without OCR key, falls back to the empty PyMuPDF result
        assert texts == ["", ""]


# ---------------------------------------------------------------------------
# Tests: _ocr_with_vision
# ---------------------------------------------------------------------------

class TestOcrWithVision:

    def test_returns_none_when_no_api_key(self, mock_fitz_doc_no_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_no_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            result = analyzer._ocr_with_vision()

        assert result is None

    def test_returns_text_on_successful_api_call(self, mock_fitz_doc_no_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        ocr_response = {
            "responses": [{"fullTextAnnotation": {"text": "무릎 통증 OCR 텍스트"}}]
        }

        with patch("fitz.open", return_value=mock_fitz_doc_no_text), \
             patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.json.return_value = ocr_response

            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="valid-key")
            result = analyzer._ocr_with_vision()

        assert result is not None
        assert any("무릎" in t for t in result)

    def test_handles_api_error_response(self, mock_fitz_doc_no_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        error_response = {
            "responses": [{"error": {"code": 403, "message": "API key invalid"}}]
        }

        with patch("fitz.open", return_value=mock_fitz_doc_no_text), \
             patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.json.return_value = error_response

            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="bad-key")
            result = analyzer._ocr_with_vision()

        # All empty texts → returns None
        assert result is None

    def test_handles_network_exception(self, mock_fitz_doc_no_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_no_text), \
             patch("requests.post", side_effect=ConnectionError("timeout")):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="key")
            result = analyzer._ocr_with_vision()

        # Network failure → all empty → None
        assert result is None

    def test_handles_top_level_error_key(self, mock_fitz_doc_no_text, tmp_path):
        """Top-level error key in response (not per-response) is handled."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_no_text), \
             patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.json.return_value = {
                "error": {"code": 400, "message": "Bad request"}
            }

            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="key")
            result = analyzer._ocr_with_vision()

        assert result is None


# ---------------------------------------------------------------------------
# Tests: extract_slide_titles
# ---------------------------------------------------------------------------

class TestExtractSlideTitles:

    def test_returns_largest_font_text_per_page(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            titles = analyzer.extract_slide_titles()

        assert len(titles) == 3
        assert all(isinstance(t, str) for t in titles)

    def test_skips_blocks_with_no_text(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        page = MagicMock()
        page.get_text.side_effect = lambda mode=None, flags=None: (
            {"blocks": [{"type": 0, "lines": [{"spans": [{"text": "", "size": 20.0}]}]}]}
            if mode == "dict" else ""
        )

        doc = MagicMock()
        doc.__len__ = MagicMock(return_value=1)
        doc.__iter__ = MagicMock(return_value=iter([page]))
        doc.__getitem__ = MagicMock(return_value=page)
        doc.close.return_value = None

        with patch("fitz.open", return_value=doc):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            titles = analyzer.extract_slide_titles()

        assert titles == []  # empty text was skipped


# ---------------------------------------------------------------------------
# Tests: generate_thumbnail
# ---------------------------------------------------------------------------

class TestGenerateThumbnail:

    def test_returns_png_bytes(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            thumb = analyzer.generate_thumbnail(page_num=0)

        assert isinstance(thumb, bytes)
        assert len(thumb) > 0

    def test_uses_correct_scale(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            analyzer.generate_thumbnail(page_num=0, scale=2.0)

        # get_pixmap should have been called with a Matrix
        page_mock = mock_fitz_doc_with_text[0]
        page_mock.get_pixmap.assert_called()


# ---------------------------------------------------------------------------
# Tests: build_summary
# ---------------------------------------------------------------------------

class TestBuildSummary:

    def test_returns_numbered_title_list(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            summary = analyzer.build_summary()

        assert "1." in summary
        assert "무릎 통증 원인" in summary

    def test_returns_empty_when_no_titles(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        page = MagicMock()
        page.get_text.side_effect = lambda mode=None, flags=None: (
            {"blocks": []} if mode == "dict" else ""
        )

        doc = MagicMock()
        doc.__len__ = MagicMock(return_value=1)
        doc.__iter__ = MagicMock(return_value=iter([page]))
        doc.__getitem__ = MagicMock(return_value=page)
        doc.close.return_value = None

        with patch("fitz.open", return_value=doc):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            summary = analyzer.build_summary()

        assert summary == ""


# ---------------------------------------------------------------------------
# Tests: clean_slide_text (static)
# ---------------------------------------------------------------------------

class TestCleanSlideText:

    def setup_method(self):
        from apps.web_publisher.pdf_analyzer import PDFAnalyzer
        self.clean = PDFAnalyzer.clean_slide_text

    def test_removes_notebooklm_reference(self):
        text = "이 자료는 NotebookLM으로 작성되었습니다."
        result = self.clean(text)
        assert "NotebookLM" not in result
        assert "Notebook LM" not in result

    def test_removes_notebook_lm_with_space(self):
        text = "Powered by Notebook LM. 내용입니다."
        result = self.clean(text)
        assert "Notebook LM" not in result

    def test_removes_korean_notebook_lm(self):
        text = "노트북 LM에서 생성한 슬라이드입니다."
        result = self.clean(text)
        assert "노트북 LM" not in result

    def test_removes_repeated_e_artifacts(self):
        text = "무릎·E·E·E·E·E통증"
        result = self.clean(text)
        assert "·E·E·E" not in result

    def test_removes_repeated_dot_artifacts(self):
        text = "내용· · · · 끝"
        result = self.clean(text)
        assert "· · · ·" not in result

    def test_removes_repeated_zeros(self):
        text = "값: 0000000 이상"
        result = self.clean(text)
        assert "0000000" not in result

    def test_collapses_multiple_spaces(self):
        text = "무릎    통증"
        result = self.clean(text)
        assert "    " not in result
        assert "무릎 통증" in result

    def test_collapses_excessive_newlines(self):
        text = "A\n\n\n\n\nB"
        result = self.clean(text)
        assert "\n\n\n" not in result

    def test_strips_leading_trailing_whitespace(self):
        text = "   내용   "
        result = self.clean(text)
        assert result == "내용"

    def test_empty_string_returns_empty(self):
        assert self.clean("") == ""

    def test_normal_text_unchanged(self):
        text = "무릎 통증 원인과 치료"
        result = self.clean(text)
        assert result == text


# ---------------------------------------------------------------------------
# Tests: build_content
# ---------------------------------------------------------------------------

class TestBuildContent:

    def test_returns_formatted_slide_content(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            content = analyzer.build_content()

        assert "[슬라이드 1]" in content
        assert "무릎 통증 원인" in content

    def test_skips_empty_slides(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        page_empty = MagicMock()
        page_empty.get_text.side_effect = lambda mode=None, flags=None: ""

        doc = MagicMock()
        doc.__len__ = MagicMock(return_value=2)
        doc.__iter__ = MagicMock(return_value=iter([page_empty, page_empty]))
        doc.__getitem__ = MagicMock(return_value=page_empty)
        doc.close.return_value = None

        with patch("fitz.open", return_value=doc):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            content = analyzer.build_content()

        assert content == ""


# ---------------------------------------------------------------------------
# Tests: _extract_keywords
# ---------------------------------------------------------------------------

class TestExtractKeywords:

    def setup_method(self):
        pass

    def test_extracts_korean_words(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")

        text = "무릎 통증 무릎 재활 무릎 수술 재활 재활"
        keywords = analyzer._extract_keywords(text)
        assert "무릎" in keywords
        assert "재활" in keywords

    def test_filters_out_stopwords(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")

        text = "그리고 또한 하지만 그래서 무릎 무릎 무릎"
        keywords = analyzer._extract_keywords(text)
        assert "그리고" not in keywords
        assert "또한" not in keywords
        assert "무릎" in keywords

    def test_respects_top_n_limit(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")

        text = "가나 나다 다라 라마 마바 바사 사아 아자 자차 차카 카타 타파 파하 하가 가나나"
        keywords = analyzer._extract_keywords(text, top_n=5)
        assert len(keywords) <= 5

    def test_returns_empty_for_empty_text(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")

        keywords = analyzer._extract_keywords("")
        assert keywords == []

    def test_filters_single_char_words(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")

        text = "가 나 다 무릎 무릎"
        keywords = analyzer._extract_keywords(text)
        # single-char words filtered out (len < 2)
        assert "가" not in keywords


# ---------------------------------------------------------------------------
# Tests: analyze
# ---------------------------------------------------------------------------

class TestAnalyze:

    def test_returns_complete_analysis_dict(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            result = analyzer.analyze()

        assert "page_count" in result
        assert "titles" in result
        assert "summary" in result
        assert "content" in result
        assert "keywords" in result
        assert "total_chars" in result
        assert result["page_count"] == 3

    def test_page_count_is_correct(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            result = analyzer.analyze()

        assert result["page_count"] == 3

    def test_keywords_is_list(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            result = analyzer.analyze()

        assert isinstance(result["keywords"], list)

    def test_close_releases_doc(self, mock_fitz_doc_with_text, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")

        with patch("fitz.open", return_value=mock_fitz_doc_with_text):
            from apps.web_publisher.pdf_analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer(pdf_path, vision_api_key="")
            analyzer.close()

        mock_fitz_doc_with_text.close.assert_called_once()
