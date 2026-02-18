#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared pytest fixtures for notebooklm-automation tests.
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir(tmp_path):
    """Temporary directory that is cleaned up after each test."""
    return tmp_path


@pytest.fixture
def sample_pdf_path(tmp_path):
    """A fake PDF path (does not contain real PDF bytes — use with fitz mocks)."""
    p = tmp_path / "test_slides.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    return p


@pytest.fixture
def sample_pptx_path(tmp_path):
    """A fake PPTX path placeholder."""
    p = tmp_path / "test_slides.pptx"
    p.write_bytes(b"PK fake pptx")
    return p


# ---------------------------------------------------------------------------
# NoterangConfig fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def noterang_config(tmp_path):
    """A NoterangConfig with all paths pointing to tmp_path."""
    from noterang.config import NoterangConfig
    config = NoterangConfig(
        download_dir=tmp_path / "downloads",
        auth_dir=tmp_path / "auth",
        nlm_exe=Path("nlm"),
        nlm_auth_exe=Path("notebooklm-mcp-auth"),
        apify_api_key="test-apify-key",
        notebooklm_app_password="xxxx xxxx xxxx xxxx",
        timeout_slides=30,
        timeout_research=10,
        timeout_download=10,
        timeout_login=10,
        browser_headless=True,
        debug=True,
    )
    (tmp_path / "downloads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "auth").mkdir(parents=True, exist_ok=True)
    return config


# ---------------------------------------------------------------------------
# NLM client / browser mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_nlm_client():
    """Mocked NotebookLMClient."""
    client = MagicMock()
    client.list_notebooks.return_value = []
    client.create_notebook.return_value = MagicMock(id="nb-test-id-12345678")
    client.delete_notebook.return_value = None
    client.start_research.return_value = {"task_id": "task-abc123"}
    client.poll_research.return_value = {"status": "completed", "sources": []}
    client.import_research_sources.return_value = []
    client.get_notebook_sources_with_types.return_value = []
    client.add_url_source.return_value = None
    client.add_text_source.return_value = None
    client.poll_studio_status.return_value = [{"status": "completed"}]
    client.close.return_value = None
    return client


@pytest.fixture
def mock_browser():
    """Mocked Playwright browser instance."""
    browser = MagicMock()
    page = MagicMock()
    browser.new_page.return_value = page
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"PNG_BYTES")
    page.content = AsyncMock(return_value="<html></html>")
    return browser


# ---------------------------------------------------------------------------
# Firestore / Firebase mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_firestore_db():
    """Mocked Firestore database client."""
    db = MagicMock()
    collection_mock = MagicMock()
    doc_ref = MagicMock()
    doc_ref.id = "doc-id-abc123"
    collection_mock.add.return_value = (MagicMock(), doc_ref)
    db.collection.return_value = collection_mock
    return db


@pytest.fixture
def mock_firebase_admin(mock_firestore_db):
    """Patch firebase_admin and firestore modules."""
    with patch.dict("sys.modules", {
        "firebase_admin": MagicMock(_apps={}),
        "firebase_admin.firestore": MagicMock(
            client=MagicMock(return_value=mock_firestore_db),
            SERVER_TIMESTAMP="SERVER_TIMESTAMP",
        ),
    }):
        yield mock_firestore_db


# ---------------------------------------------------------------------------
# fitz (PyMuPDF) mock
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_fitz_page():
    """Mocked fitz page."""
    page = MagicMock()
    page.get_text.return_value = "슬라이드 제목\n본문 내용입니다."
    page.get_text.side_effect = None
    pixmap = MagicMock()
    pixmap.tobytes.return_value = b"\x89PNG\r\nfake_png_bytes"
    page.get_pixmap.return_value = pixmap

    # dict mode for extract_slide_titles
    page.get_text.return_value = "슬라이드 제목\n본문 내용입니다."
    return page


@pytest.fixture
def mock_fitz_doc(mock_fitz_page):
    """Mocked fitz document with 3 pages."""
    doc = MagicMock()
    doc.__len__ = MagicMock(return_value=3)
    doc.__iter__ = MagicMock(return_value=iter([
        mock_fitz_page, mock_fitz_page, mock_fitz_page
    ]))
    doc.__getitem__ = MagicMock(return_value=mock_fitz_page)
    doc.close.return_value = None
    return doc


# ---------------------------------------------------------------------------
# HTTP requests mock
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_requests_post():
    """Mocked requests.post for Vision API calls."""
    response = MagicMock()
    response.json.return_value = {
        "responses": [{
            "fullTextAnnotation": {
                "text": "OCR 추출 텍스트입니다."
            }
        }]
    }
    return response


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_analysis_result():
    """Sample PDF analysis result dict."""
    return {
        "page_count": 5,
        "titles": ["무릎 통증", "원인", "증상", "치료", "예방"],
        "summary": "1. 무릎 통증\n2. 원인\n3. 증상\n4. 치료\n5. 예방",
        "content": "[슬라이드 1]\n무릎 통증 내용\n\n\n[슬라이드 2]\n원인 내용",
        "keywords": ["무릎", "통증", "치료", "재활", "수술"],
        "total_chars": 250,
        "thumbnail": b"\x89PNG\r\nfake_thumb",
    }


@pytest.fixture
def sample_content_data():
    """Sample slide content data for PPTX generation."""
    return [
        {"title": "제목 슬라이드", "body": "발표 내용 소개"},
        {"title": "원인", "body": "주요 원인 설명"},
        {"title": "치료법", "body": "치료 방법 안내"},
    ]


@pytest.fixture
def mock_run_nlm():
    """Patch noterang.artifacts.run_nlm to return success."""
    with patch("noterang.artifacts.run_nlm") as mock:
        mock.return_value = (True, "Slide deck generation started\nArtifact ID: art-123", "")
        yield mock
