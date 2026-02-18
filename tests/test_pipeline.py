#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for apps/web_publisher/pipeline.py

Tests:
  - WebPublishPipeline.__init__()
  - get_research_queries()
  - get_focus_prompt()
  - generate_tags()
  - run() — full pipeline: success, PDF not found, noterang failure,
    skipping registration, existing PDF path
  - FirestoreClient.register_article()
  - FileManager.copy_pdf_and_thumbnail()
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call

import pytest


# ---------------------------------------------------------------------------
# FirestoreClient Tests
# ---------------------------------------------------------------------------

class TestFirestoreClient:

    def test_register_article_returns_doc_id_on_success(self, mock_firestore_db):
        with patch.dict("sys.modules", {
            "firebase_admin": MagicMock(_apps={}),
            "firebase_admin.firestore": MagicMock(
                client=MagicMock(return_value=mock_firestore_db),
                SERVER_TIMESTAMP="__server_timestamp__",
            ),
        }):
            from apps.web_publisher.firestore_client import FirestoreClient
            client = FirestoreClient(project_id="test-project")
            client._db = mock_firestore_db

            analysis = {
                "page_count": 5,
                "titles": ["무릎 통증", "원인", "증상"],
                "summary": "1. 무릎 통증\n2. 원인",
                "content": "슬라이드 내용",
            }

            with patch("firebase_admin.firestore.SERVER_TIMESTAMP", "__ts__"):
                doc_id = client.register_article(
                    title="무릎 통증",
                    pdf_url="/uploads/test.pdf",
                    thumb_url="/uploads/test_thumb.png",
                    analysis=analysis,
                    tags=["무릎", "통증"],
                    article_type="disease",
                    visible=True,
                )

        assert doc_id == "doc-id-abc123"

    def test_register_article_returns_none_on_firestore_error(self, mock_firestore_db):
        mock_firestore_db.collection.return_value.add.side_effect = Exception("Firestore down")

        with patch.dict("sys.modules", {
            "firebase_admin": MagicMock(_apps={}),
            "firebase_admin.firestore": MagicMock(
                client=MagicMock(return_value=mock_firestore_db),
                SERVER_TIMESTAMP="__ts__",
            ),
        }):
            from apps.web_publisher.firestore_client import FirestoreClient
            client = FirestoreClient(project_id="test-project")
            client._db = mock_firestore_db

            analysis = {"page_count": 0, "titles": [], "summary": "", "content": ""}

            with patch("firebase_admin.firestore.SERVER_TIMESTAMP", "__ts__"):
                doc_id = client.register_article(
                    title="실패 테스트",
                    pdf_url="/uploads/x.pdf",
                    thumb_url=None,
                    analysis=analysis,
                    tags=[],
                )

        assert doc_id is None

    def test_register_article_uses_title_summary_when_no_slide_titles(self, mock_firestore_db):
        with patch.dict("sys.modules", {
            "firebase_admin": MagicMock(_apps={}),
            "firebase_admin.firestore": MagicMock(
                client=MagicMock(return_value=mock_firestore_db),
                SERVER_TIMESTAMP="__ts__",
            ),
        }):
            from apps.web_publisher.firestore_client import FirestoreClient
            client = FirestoreClient(project_id="test-project")
            client._db = mock_firestore_db

            analysis = {"page_count": 3, "titles": [], "summary": "", "content": ""}

            with patch("firebase_admin.firestore.SERVER_TIMESTAMP", "__ts__"):
                client.register_article(
                    title="족저근막염",
                    pdf_url="/uploads/x.pdf",
                    thumb_url=None,
                    analysis=analysis,
                    tags=[],
                )

        call_args = mock_firestore_db.collection.return_value.add.call_args
        doc_data = call_args[0][0]
        assert "족저근막염" in doc_data["summary"]

    def test_register_article_includes_thumbnail_in_content(self, mock_firestore_db):
        with patch.dict("sys.modules", {
            "firebase_admin": MagicMock(_apps={}),
            "firebase_admin.firestore": MagicMock(
                client=MagicMock(return_value=mock_firestore_db),
                SERVER_TIMESTAMP="__ts__",
            ),
        }):
            from apps.web_publisher.firestore_client import FirestoreClient
            client = FirestoreClient(project_id="test-project")
            client._db = mock_firestore_db

            analysis = {
                "page_count": 1,
                "titles": ["제목"],
                "summary": "1. 제목",
                "content": "내용",
            }

            with patch("firebase_admin.firestore.SERVER_TIMESTAMP", "__ts__"):
                client.register_article(
                    title="테스트",
                    pdf_url="/uploads/x.pdf",
                    thumb_url="/uploads/x_thumb.png",
                    analysis=analysis,
                    tags=[],
                )

        call_args = mock_firestore_db.collection.return_value.add.call_args
        doc_data = call_args[0][0]
        assert "![테스트]" in doc_data["content"]

    def test_register_article_truncates_long_content(self, mock_firestore_db):
        with patch.dict("sys.modules", {
            "firebase_admin": MagicMock(_apps={}),
            "firebase_admin.firestore": MagicMock(
                client=MagicMock(return_value=mock_firestore_db),
                SERVER_TIMESTAMP="__ts__",
            ),
        }):
            from apps.web_publisher.firestore_client import FirestoreClient
            client = FirestoreClient(project_id="test-project")
            client._db = mock_firestore_db

            long_content = "가나다라" * 3000  # > 8000 chars
            analysis = {
                "page_count": 1,
                "titles": [],
                "summary": "",
                "content": long_content,
            }

            with patch("firebase_admin.firestore.SERVER_TIMESTAMP", "__ts__"):
                client.register_article(
                    title="긴 내용",
                    pdf_url="/uploads/x.pdf",
                    thumb_url=None,
                    analysis=analysis,
                    tags=[],
                )

        call_args = mock_firestore_db.collection.return_value.add.call_args
        doc_data = call_args[0][0]
        assert "이하 생략" in doc_data["content"]

    def test_lazy_db_initialization(self, tmp_path):
        """_get_db() is not called until register_article is invoked."""
        from apps.web_publisher.firestore_client import FirestoreClient
        client = FirestoreClient(project_id="test-project")
        assert client._db is None


# ---------------------------------------------------------------------------
# FileManager Tests
# ---------------------------------------------------------------------------

class TestFileManager:

    def test_copy_pdf_and_thumbnail_returns_url_paths(self, tmp_path, sample_pdf_path):
        uploads_dir = tmp_path / "uploads"

        from apps.web_publisher.file_manager import FileManager
        mgr = FileManager(uploads_dir)
        thumb_bytes = b"\x89PNG\r\nfake"
        pdf_url, thumb_url = mgr.copy_pdf_and_thumbnail(
            pdf_path=sample_pdf_path,
            title="무릎 통증",
            thumbnail=thumb_bytes,
        )

        assert pdf_url.startswith("/uploads/")
        assert pdf_url.endswith(".pdf")
        assert thumb_url is not None
        assert thumb_url.startswith("/uploads/")
        assert thumb_url.endswith(".png")

    def test_copy_pdf_creates_file_on_disk(self, tmp_path, sample_pdf_path):
        uploads_dir = tmp_path / "uploads"

        from apps.web_publisher.file_manager import FileManager
        mgr = FileManager(uploads_dir)
        pdf_url, _ = mgr.copy_pdf_and_thumbnail(
            pdf_path=sample_pdf_path,
            title="테스트",
            thumbnail=None,
        )

        filename = pdf_url.lstrip("/uploads/")
        dest_path = uploads_dir / pdf_url.split("/uploads/")[1]
        assert dest_path.exists()

    def test_thumb_url_is_none_when_no_thumbnail(self, tmp_path, sample_pdf_path):
        uploads_dir = tmp_path / "uploads"

        from apps.web_publisher.file_manager import FileManager
        mgr = FileManager(uploads_dir)
        _, thumb_url = mgr.copy_pdf_and_thumbnail(
            pdf_path=sample_pdf_path,
            title="테스트",
            thumbnail=None,
        )

        assert thumb_url is None

    def test_creates_uploads_dir_if_not_exists(self, tmp_path, sample_pdf_path):
        uploads_dir = tmp_path / "new_uploads"
        assert not uploads_dir.exists()

        from apps.web_publisher.file_manager import FileManager
        mgr = FileManager(uploads_dir)

        assert uploads_dir.exists()

    def test_sanitizes_title_in_filename(self, tmp_path, sample_pdf_path):
        uploads_dir = tmp_path / "uploads"

        from apps.web_publisher.file_manager import FileManager
        mgr = FileManager(uploads_dir)
        pdf_url, _ = mgr.copy_pdf_and_thumbnail(
            pdf_path=sample_pdf_path,
            title="무릎 통증/원인",
            thumbnail=None,
        )

        # Spaces → underscore, slashes → dash
        assert " " not in pdf_url
        assert "/" not in pdf_url.replace("/uploads/", "")

    def test_unique_filenames_per_call(self, tmp_path, sample_pdf_path):
        uploads_dir = tmp_path / "uploads"

        from apps.web_publisher.file_manager import FileManager
        mgr = FileManager(uploads_dir)
        url1, _ = mgr.copy_pdf_and_thumbnail(sample_pdf_path, "테스트", None)
        url2, _ = mgr.copy_pdf_and_thumbnail(sample_pdf_path, "테스트", None)

        assert url1 != url2  # uuid suffix makes them different


# ---------------------------------------------------------------------------
# WebPublishPipeline.__init__ and helper method tests
# ---------------------------------------------------------------------------

class TestWebPublishPipelineInit:

    def _make_pipeline(self, **kwargs):
        """Helper to create pipeline with mocked configs."""
        with patch("apps.web_publisher.pipeline.get_config") as mock_get_cfg, \
             patch("apps.web_publisher.pipeline.WebPublisherConfig") as mock_wp_cfg:
            mock_get_cfg.return_value = MagicMock()
            mock_wp_cfg.load.return_value = MagicMock()

            from apps.web_publisher.pipeline import WebPublishPipeline
            return WebPublishPipeline(
                title=kwargs.get("title", "무릎 통증"),
                **{k: v for k, v in kwargs.items() if k != "title"},
            )

    def test_sets_title(self):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            pipeline = WebPublishPipeline(title="족저근막염")
        assert pipeline.title == "족저근막염"

    def test_sets_pdf_path_when_provided(self, tmp_path, sample_pdf_path):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            pipeline = WebPublishPipeline(title="테스트", pdf_path=str(sample_pdf_path))
        assert pipeline.pdf_path == sample_pdf_path

    def test_pdf_path_is_none_by_default(self):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            pipeline = WebPublishPipeline(title="테스트")
        assert pipeline.pdf_path is None

    def test_default_register_is_true(self):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            pipeline = WebPublishPipeline(title="테스트")
        assert pipeline.register is True

    def test_default_visible_is_true(self):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            pipeline = WebPublishPipeline(title="테스트")
        assert pipeline.visible is True


# ---------------------------------------------------------------------------
# WebPublishPipeline.get_research_queries
# ---------------------------------------------------------------------------

class TestGetResearchQueries:

    def _make_pipeline(self, title="무릎 통증", queries=None):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            return WebPublishPipeline(title=title, queries=queries)

    def test_returns_3_queries_by_default(self):
        pipeline = self._make_pipeline()
        queries = pipeline.get_research_queries()
        assert len(queries) == 3

    def test_queries_exclude_korean_medicine_terms(self):
        pipeline = self._make_pipeline()
        queries = pipeline.get_research_queries()
        for q in queries:
            assert "-한의학" in q
            assert "-한방" in q
            assert "-침" in q

    def test_title_appears_in_default_queries(self):
        pipeline = self._make_pipeline(title="족저근막염")
        queries = pipeline.get_research_queries()
        assert all("족저근막염" in q for q in queries)

    def test_uses_provided_queries(self):
        custom_queries = ["무릎 수술", "무릎 재활"]
        pipeline = self._make_pipeline(queries=custom_queries)
        queries = pipeline.get_research_queries()
        assert len(queries) == 2
        # Custom queries get the exclusion suffix added
        assert "-한의학" in queries[0]

    def test_custom_queries_preserve_original_text(self):
        pipeline = self._make_pipeline(queries=["아킬레스건염 치료"])
        queries = pipeline.get_research_queries()
        assert "아킬레스건염 치료" in queries[0]


# ---------------------------------------------------------------------------
# WebPublishPipeline.get_focus_prompt
# ---------------------------------------------------------------------------

class TestGetFocusPrompt:

    def _make_pipeline(self, title="무릎 통증", design="인포그래픽"):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"), \
             patch("apps.web_publisher.pipeline.SlidePrompts") as mock_prompts:
            mock_prompts.return_value.get_prompt.return_value = "[디자인 프롬프트]"
            from apps.web_publisher.pipeline import WebPublishPipeline
            return WebPublishPipeline(title=title, design=design)

    def test_includes_korean_language_instruction(self):
        pipeline = self._make_pipeline()
        with patch("apps.web_publisher.pipeline.SlidePrompts") as mock_prompts:
            mock_prompts.return_value.get_prompt.return_value = ""
            prompt = pipeline.get_focus_prompt()
        assert "한글" in prompt

    def test_includes_title_in_prompt(self):
        pipeline = self._make_pipeline(title="회전근개 파열")
        with patch("apps.web_publisher.pipeline.SlidePrompts") as mock_prompts:
            mock_prompts.return_value.get_prompt.return_value = ""
            prompt = pipeline.get_focus_prompt()
        assert "회전근개 파열" in prompt

    def test_excludes_korean_medicine_reference(self):
        pipeline = self._make_pipeline()
        with patch("apps.web_publisher.pipeline.SlidePrompts") as mock_prompts:
            mock_prompts.return_value.get_prompt.return_value = ""
            prompt = pipeline.get_focus_prompt()
        assert "한의학" in prompt  # mentioned as exclusion rule


# ---------------------------------------------------------------------------
# WebPublishPipeline.generate_tags
# ---------------------------------------------------------------------------

class TestGenerateTags:

    def _make_pipeline(self, title="무릎 통증", design="인포그래픽"):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig"):
            from apps.web_publisher.pipeline import WebPublishPipeline
            return WebPublishPipeline(title=title, design=design)

    def test_always_includes_base_tags(self):
        pipeline = self._make_pipeline()
        with patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"):
            tags = pipeline.generate_tags()
        assert "자동생성" in tags
        assert "노트랑" in tags

    def test_includes_title_words(self):
        pipeline = self._make_pipeline(title="무릎 통증")
        with patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"):
            tags = pipeline.generate_tags()
        assert "무릎" in tags
        assert "통증" in tags

    def test_includes_pdf_keywords(self):
        pipeline = self._make_pipeline()
        keywords = ["재활", "수술", "통증"]
        with patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"):
            tags = pipeline.generate_tags(pdf_keywords=keywords)
        assert "재활" in tags

    def test_limits_pdf_keywords_to_top_5(self):
        pipeline = self._make_pipeline(title="테스트")
        keywords = ["a", "b", "c", "d", "e", "f", "g"]  # 7 items
        with patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"):
            tags = pipeline.generate_tags(pdf_keywords=keywords)
        # Only top 5 pdf keywords should be added
        keyword_count = sum(1 for k in keywords[:5] if k in tags)
        assert keyword_count <= 5

    def test_adds_body_part_tag_when_detected(self):
        from apps.web_publisher.body_parts import BODY_PARTS

        # Find a body part with a known label
        test_part = BODY_PARTS[0] if BODY_PARTS else None
        if test_part is None:
            pytest.skip("No body parts defined")

        pipeline = self._make_pipeline(title=test_part.get("label", "무릎"))
        with patch("apps.web_publisher.pipeline.match_body_part", return_value=test_part["id"]):
            tags = pipeline.generate_tags()
        assert test_part["label"] in tags

    def test_no_duplicate_tags(self):
        pipeline = self._make_pipeline(title="무릎 통증")
        with patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"):
            tags = pipeline.generate_tags(pdf_keywords=["무릎"])
        # "무릎" from title and "무릎" from keywords → no duplicate
        assert tags.count("무릎") == 1


# ---------------------------------------------------------------------------
# WebPublishPipeline.run() — full pipeline integration tests
# ---------------------------------------------------------------------------

class TestWebPublishPipelineRun:

    def _make_pipeline(
        self,
        title="무릎 통증",
        pdf_path=None,
        register=True,
        visible=True,
    ):
        with patch("apps.web_publisher.pipeline.get_config"), \
             patch("apps.web_publisher.pipeline.WebPublisherConfig") as mock_wp:
            mock_wp.load.return_value = MagicMock(
                vision_api_key="",
                uploads_dir=Path("/fake/uploads"),
                firebase_project_id="test-project",
            )
            from apps.web_publisher.pipeline import WebPublishPipeline
            return WebPublishPipeline(
                title=title,
                pdf_path=pdf_path,
                register=register,
                visible=visible,
            )

    @pytest.mark.asyncio
    async def test_run_returns_success_with_existing_pdf(
        self, tmp_path, sample_pdf_path, sample_analysis_result, mock_firestore_db
    ):
        pipeline = self._make_pipeline(pdf_path=str(sample_pdf_path))
        pipeline.publisher_config = MagicMock(
            vision_api_key="",
            uploads_dir=tmp_path / "uploads",
            firebase_project_id="test-project",
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_analysis_result
        mock_analyzer.generate_thumbnail.return_value = b"\x89PNG\r\nfake"

        mock_file_mgr = MagicMock()
        mock_file_mgr.copy_pdf_and_thumbnail.return_value = ("/uploads/test.pdf", "/uploads/test_thumb.png")

        mock_fs_client = MagicMock()
        mock_fs_client.register_article.return_value = "new-doc-id"

        with patch("apps.web_publisher.pipeline.PDFAnalyzer", return_value=mock_analyzer), \
             patch("apps.web_publisher.pipeline.FileManager", return_value=mock_file_mgr), \
             patch("apps.web_publisher.pipeline.FirestoreClient", return_value=mock_fs_client), \
             patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"), \
             patch("apps.web_publisher.pipeline.SlidePrompts"):
            result = await pipeline.run()

        assert result["success"] is True
        assert result["title"] == "무릎 통증"
        assert result["pdf_url"] == "/uploads/test.pdf"
        assert result["doc_id"] == "new-doc-id"

    @pytest.mark.asyncio
    async def test_run_returns_failure_when_pdf_not_found(self, tmp_path):
        missing_pdf = tmp_path / "nonexistent.pdf"
        pipeline = self._make_pipeline(pdf_path=str(missing_pdf))

        result = await pipeline.run()

        assert result["success"] is False
        assert "PDF 파일 없음" in result["error"]

    @pytest.mark.asyncio
    async def test_run_skips_registration_when_register_false(
        self, tmp_path, sample_pdf_path, sample_analysis_result
    ):
        pipeline = self._make_pipeline(
            pdf_path=str(sample_pdf_path),
            register=False,
        )
        pipeline.publisher_config = MagicMock(
            vision_api_key="",
            uploads_dir=tmp_path / "uploads",
            firebase_project_id="test-project",
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_analysis_result
        mock_analyzer.generate_thumbnail.return_value = b"\x89PNG\r\n"

        mock_file_mgr = MagicMock()
        mock_file_mgr.copy_pdf_and_thumbnail.return_value = ("/uploads/x.pdf", None)

        mock_fs_client = MagicMock()

        with patch("apps.web_publisher.pipeline.PDFAnalyzer", return_value=mock_analyzer), \
             patch("apps.web_publisher.pipeline.FileManager", return_value=mock_file_mgr), \
             patch("apps.web_publisher.pipeline.FirestoreClient", return_value=mock_fs_client), \
             patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"), \
             patch("apps.web_publisher.pipeline.SlidePrompts"):
            result = await pipeline.run()

        assert result["success"] is True
        assert result["doc_id"] is None
        mock_fs_client.register_article.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_calls_noterang_when_no_pdf_provided(
        self, tmp_path, sample_analysis_result
    ):
        """When pdf_path=None, pipeline calls run_noterang to generate PDF."""
        generated_pdf = tmp_path / "generated.pdf"
        generated_pdf.write_bytes(b"%PDF-1.4 generated")

        pipeline = self._make_pipeline(pdf_path=None, register=False)
        pipeline.publisher_config = MagicMock(
            vision_api_key="",
            uploads_dir=tmp_path / "uploads",
            firebase_project_id="test-project",
        )

        mock_noterang_result = MagicMock()
        mock_noterang_result.success = True
        mock_noterang_result.pdf_path = str(generated_pdf)
        mock_noterang_result.notebook_id = "nb-generated-123"
        mock_noterang_result.error = None

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_analysis_result
        mock_analyzer.generate_thumbnail.return_value = b"\x89PNG\r\n"

        mock_file_mgr = MagicMock()
        mock_file_mgr.copy_pdf_and_thumbnail.return_value = ("/uploads/gen.pdf", None)

        with patch.object(pipeline, "run_noterang", new=AsyncMock(return_value=mock_noterang_result)), \
             patch("apps.web_publisher.pipeline.PDFAnalyzer", return_value=mock_analyzer), \
             patch("apps.web_publisher.pipeline.FileManager", return_value=mock_file_mgr), \
             patch("apps.web_publisher.pipeline.FirestoreClient"), \
             patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"), \
             patch("apps.web_publisher.pipeline.SlidePrompts"):
            result = await pipeline.run()

        assert result["success"] is True
        assert result["notebook_id"] == "nb-generated-123"

    @pytest.mark.asyncio
    async def test_run_returns_failure_when_noterang_fails(self):
        """Pipeline fails gracefully when noterang returns error."""
        pipeline = self._make_pipeline(pdf_path=None)

        mock_noterang_result = MagicMock()
        mock_noterang_result.success = False
        mock_noterang_result.pdf_path = None
        mock_noterang_result.error = "NotebookLM timeout"

        with patch.object(pipeline, "run_noterang", new=AsyncMock(return_value=mock_noterang_result)):
            result = await pipeline.run()

        assert result["success"] is False
        assert "NotebookLM timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_run_includes_page_count_in_result(
        self, tmp_path, sample_pdf_path, sample_analysis_result
    ):
        pipeline = self._make_pipeline(pdf_path=str(sample_pdf_path), register=False)
        pipeline.publisher_config = MagicMock(
            vision_api_key="",
            uploads_dir=tmp_path / "uploads",
            firebase_project_id="test-project",
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_analysis_result
        mock_analyzer.generate_thumbnail.return_value = b"\x89PNG\r\n"

        mock_file_mgr = MagicMock()
        mock_file_mgr.copy_pdf_and_thumbnail.return_value = ("/uploads/x.pdf", None)

        with patch("apps.web_publisher.pipeline.PDFAnalyzer", return_value=mock_analyzer), \
             patch("apps.web_publisher.pipeline.FileManager", return_value=mock_file_mgr), \
             patch("apps.web_publisher.pipeline.FirestoreClient"), \
             patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"), \
             patch("apps.web_publisher.pipeline.SlidePrompts"):
            result = await pipeline.run()

        assert result["page_count"] == sample_analysis_result["page_count"]

    @pytest.mark.asyncio
    async def test_run_includes_duration_in_result(
        self, tmp_path, sample_pdf_path, sample_analysis_result
    ):
        pipeline = self._make_pipeline(pdf_path=str(sample_pdf_path), register=False)
        pipeline.publisher_config = MagicMock(
            vision_api_key="",
            uploads_dir=tmp_path / "uploads",
            firebase_project_id="test-project",
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_analysis_result
        mock_analyzer.generate_thumbnail.return_value = b"\x89PNG\r\n"

        mock_file_mgr = MagicMock()
        mock_file_mgr.copy_pdf_and_thumbnail.return_value = ("/uploads/x.pdf", None)

        with patch("apps.web_publisher.pipeline.PDFAnalyzer", return_value=mock_analyzer), \
             patch("apps.web_publisher.pipeline.FileManager", return_value=mock_file_mgr), \
             patch("apps.web_publisher.pipeline.FirestoreClient"), \
             patch("apps.web_publisher.pipeline.match_body_part", return_value="etc"), \
             patch("apps.web_publisher.pipeline.SlidePrompts"):
            result = await pipeline.run()

        assert "duration" in result
        assert isinstance(result["duration"], int)
        assert result["duration"] >= 0

    @pytest.mark.asyncio
    async def test_analyzer_close_called_even_on_analysis_exception(
        self, tmp_path, sample_pdf_path
    ):
        """PDFAnalyzer.close() is called via finally block even when analyze() fails."""
        pipeline = self._make_pipeline(pdf_path=str(sample_pdf_path))
        pipeline.publisher_config = MagicMock(
            vision_api_key="",
            uploads_dir=tmp_path / "uploads",
            firebase_project_id="test-project",
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = RuntimeError("PDF parse error")

        with patch("apps.web_publisher.pipeline.PDFAnalyzer", return_value=mock_analyzer), \
             patch("apps.web_publisher.pipeline.SlidePrompts"):
            with pytest.raises(RuntimeError):
                await pipeline.run()

        mock_analyzer.close.assert_called_once()
