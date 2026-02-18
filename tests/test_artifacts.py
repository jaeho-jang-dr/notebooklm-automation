#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for noterang/artifacts.py

Tests:
  - create_slides()
  - create_infographic()
  - check_studio_status()
  - is_generation_complete()
  - wait_for_completion() (async)
  - create_slides_and_wait() (async)
  - create_infographic_and_wait() (async)
  - ArtifactManager class
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Tests: create_slides
# ---------------------------------------------------------------------------

class TestCreateSlides:

    def test_returns_artifact_id_from_stdout(self, mock_run_nlm):
        mock_run_nlm.return_value = (
            True,
            "Slide deck generation started\nArtifact ID: art-12345",
            ""
        )
        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            result = create_slides("nb-id-12345678")

        assert result == "art-12345"

    def test_returns_pending_when_no_artifact_id_in_stdout(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "Slide deck generation started", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            result = create_slides("nb-id-12345678")

        assert result == "pending"

    def test_returns_none_on_nlm_failure(self, mock_run_nlm):
        mock_run_nlm.return_value = (False, "", "Error: command failed")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            result = create_slides("nb-id-12345678")

        assert result is None

    def test_returns_none_when_stdout_has_no_start_indicator(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "Some other output", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            result = create_slides("nb-id-12345678")

        assert result is None

    def test_uses_config_language_when_none_provided(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "generation started", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            create_slides("nb-id-12345678", language=None)

        args_passed = mock_run_nlm.call_args[0][0]
        assert "ko" in args_passed

    def test_uses_provided_language(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "generation started", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            create_slides("nb-id-12345678", language="en")

        args_passed = mock_run_nlm.call_args[0][0]
        assert "en" in args_passed

    def test_includes_focus_flag_when_provided(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "generation started", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            create_slides("nb-id-12345678", focus="무릎 통증")

        args_passed = mock_run_nlm.call_args[0][0]
        assert "--focus" in args_passed
        assert "무릎 통증" in args_passed

    def test_korean_start_indicator_accepted(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "슬라이드 생성 시작", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides
            result = create_slides("nb-id-12345678")

        assert result == "pending"


# ---------------------------------------------------------------------------
# Tests: create_infographic
# ---------------------------------------------------------------------------

class TestCreateInfographic:

    def test_returns_pending_on_success_without_id(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "Infographic generation started", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_infographic
            result = create_infographic("nb-id-12345678")

        assert result == "pending"

    def test_returns_none_on_failure(self, mock_run_nlm):
        mock_run_nlm.return_value = (False, "", "error")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_infographic
            result = create_infographic("nb-id-12345678")

        assert result is None

    def test_passes_style_argument(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "generation started", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_infographic
            create_infographic("nb-id-12345678", style="minimal")

        args_passed = mock_run_nlm.call_args[0][0]
        assert "--style" in args_passed
        assert "minimal" in args_passed


# ---------------------------------------------------------------------------
# Tests: check_studio_status
# ---------------------------------------------------------------------------

class TestCheckStudioStatus:

    def test_returns_completed_from_python_api(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "completed"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client):
            from noterang.artifacts import check_studio_status
            status, data = check_studio_status("nb-id-12345678")

        assert status == "completed"
        assert data["status"] == "completed"

    def test_returns_in_progress_when_empty_list(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = []

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client):
            from noterang.artifacts import check_studio_status
            status, data = check_studio_status("nb-id-12345678")

        assert status == "in_progress"

    def test_falls_back_to_cli_on_python_api_exception(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.side_effect = Exception("encoding error")
        cli_output = json.dumps([{"status": "completed"}])

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.run_nlm", return_value=(True, cli_output, "")):
            from noterang.artifacts import check_studio_status
            status, data = check_studio_status("nb-id-12345678")

        assert status == "completed"

    def test_cli_fallback_parses_text_completed(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.side_effect = Exception("error")

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.run_nlm", return_value=(True, "Status: COMPLETED", "")):
            from noterang.artifacts import check_studio_status
            status, data = check_studio_status("nb-id-12345678")

        assert status == "completed"

    def test_cli_fallback_parses_text_failed(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.side_effect = Exception("error")

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.run_nlm", return_value=(True, "Generation failed", "")):
            from noterang.artifacts import check_studio_status
            status, data = check_studio_status("nb-id-12345678")

        assert status == "failed"

    def test_cli_fallback_returns_unknown_on_cli_failure(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.side_effect = Exception("error")

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.run_nlm", return_value=(False, "", "cli error")):
            from noterang.artifacts import check_studio_status
            status, data = check_studio_status("nb-id-12345678")

        assert status == "unknown"

    def test_cli_parses_empty_json_list_as_in_progress(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.side_effect = Exception("err")

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.run_nlm", return_value=(True, "[]", "")):
            from noterang.artifacts import check_studio_status
            status, _ = check_studio_status("nb-id-12345678")

        assert status == "in_progress"


# ---------------------------------------------------------------------------
# Tests: is_generation_complete
# ---------------------------------------------------------------------------

class TestIsGenerationComplete:

    def test_returns_true_when_completed(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "completed"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client):
            from noterang.artifacts import is_generation_complete
            assert is_generation_complete("nb-id-12345678") is True

    def test_returns_false_when_in_progress(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "in_progress"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client):
            from noterang.artifacts import is_generation_complete
            assert is_generation_complete("nb-id-12345678") is False


# ---------------------------------------------------------------------------
# Tests: wait_for_completion (async)
# ---------------------------------------------------------------------------

class TestWaitForCompletion:

    @pytest.mark.asyncio
    async def test_returns_true_when_completed_immediately(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "completed"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.get_config") as mock_cfg, \
             patch("asyncio.sleep", new=AsyncMock()):
            mock_cfg.return_value.timeout_slides = 30
            from noterang.artifacts import wait_for_completion
            result = await wait_for_completion("nb-id-12345678", timeout=30, check_interval=1)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_timeout(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "in_progress"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.get_config") as mock_cfg, \
             patch("asyncio.sleep", new=AsyncMock()), \
             patch("noterang.artifacts.time") as mock_time:
            mock_cfg.return_value.timeout_slides = 5
            # Simulate time advancing: first call 0, then exceed timeout
            mock_time.time.side_effect = [0, 0, 10, 10, 10]
            from noterang.artifacts import wait_for_completion
            result = await wait_for_completion("nb-id-12345678", timeout=5, check_interval=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_failed(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "failed"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.get_config") as mock_cfg, \
             patch("asyncio.sleep", new=AsyncMock()):
            mock_cfg.return_value.timeout_slides = 30
            from noterang.artifacts import wait_for_completion
            result = await wait_for_completion("nb-id-12345678", timeout=30, check_interval=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_calls_on_progress_callback(self, mock_nlm_client):
        call_count = 0

        def progress_cb(elapsed, status):
            nonlocal call_count
            call_count += 1

        mock_nlm_client.poll_studio_status.return_value = [{"status": "completed"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("noterang.artifacts.get_config") as mock_cfg, \
             patch("asyncio.sleep", new=AsyncMock()):
            mock_cfg.return_value.timeout_slides = 30
            from noterang.artifacts import wait_for_completion
            await wait_for_completion(
                "nb-id-12345678", timeout=30, check_interval=1, on_progress=progress_cb
            )

        assert call_count >= 1


# ---------------------------------------------------------------------------
# Tests: create_slides_and_wait (async)
# ---------------------------------------------------------------------------

class TestCreateSlidesAndWait:

    @pytest.mark.asyncio
    async def test_returns_artifact_id_on_success(self, mock_run_nlm, mock_nlm_client):
        mock_run_nlm.return_value = (True, "Artifact ID: art-xyz", "")
        mock_nlm_client.poll_studio_status.return_value = [{"status": "completed"}]

        with patch("noterang.artifacts.get_config") as mock_cfg, \
             patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("asyncio.sleep", new=AsyncMock()):
            mock_cfg.return_value.default_language = "ko"
            mock_cfg.return_value.timeout_slides = 30
            from noterang.artifacts import create_slides_and_wait
            result = await create_slides_and_wait("nb-id-12345678", timeout=30)

        assert result == "art-xyz"

    @pytest.mark.asyncio
    async def test_returns_none_when_slides_creation_fails(self, mock_run_nlm):
        mock_run_nlm.return_value = (False, "", "error")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import create_slides_and_wait
            result = await create_slides_and_wait("nb-id-12345678")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_wait_times_out(self, mock_run_nlm, mock_nlm_client):
        mock_run_nlm.return_value = (True, "Artifact ID: art-001", "")
        mock_nlm_client.poll_studio_status.return_value = [{"status": "in_progress"}]

        with patch("noterang.artifacts.get_config") as mock_cfg, \
             patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client), \
             patch("asyncio.sleep", new=AsyncMock()), \
             patch("noterang.artifacts.time") as mock_time:
            mock_cfg.return_value.default_language = "ko"
            mock_cfg.return_value.timeout_slides = 1
            mock_time.time.side_effect = [0, 0, 2, 2, 2]
            from noterang.artifacts import create_slides_and_wait
            result = await create_slides_and_wait("nb-id-12345678", timeout=1)

        assert result is None


# ---------------------------------------------------------------------------
# Tests: ArtifactManager
# ---------------------------------------------------------------------------

class TestArtifactManager:

    def test_initial_state(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        assert mgr.notebook_id is None
        assert mgr.artifacts == {}

    def test_set_notebook(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        mgr.set_notebook("nb-123")
        assert mgr.notebook_id == "nb-123"

    def test_create_slides_with_no_notebook_returns_none(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        result = mgr.create_slides()
        assert result is None

    def test_create_slides_stores_artifact(self, mock_run_nlm):
        mock_run_nlm.return_value = (True, "Artifact ID: art-stored", "")

        with patch("noterang.artifacts.get_config") as mock_cfg:
            mock_cfg.return_value.default_language = "ko"
            from noterang.artifacts import ArtifactManager
            mgr = ArtifactManager("nb-id-12345678")
            result = mgr.create_slides(language="ko")

        assert result == "art-stored"
        assert "art-stored" in mgr.artifacts
        assert mgr.artifacts["art-stored"]["type"] == "slides"

    def test_create_infographic_with_no_notebook_returns_none(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        result = mgr.create_infographic()
        assert result is None

    def test_check_status_with_no_notebook_returns_unknown(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        status, data = mgr.check_status()
        assert status == "unknown"
        assert "error" in data

    def test_is_complete_with_no_notebook_returns_false(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        assert mgr.is_complete() is False

    def test_check_status_delegates_to_check_studio_status(self, mock_nlm_client):
        mock_nlm_client.poll_studio_status.return_value = [{"status": "completed"}]

        with patch("noterang.artifacts.get_nlm_client", return_value=mock_nlm_client):
            from noterang.artifacts import ArtifactManager
            mgr = ArtifactManager("nb-id-12345678")
            status, _ = mgr.check_status()

        assert status == "completed"

    @pytest.mark.asyncio
    async def test_wait_complete_with_no_notebook_returns_false(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        result = await mgr.wait_complete(timeout=1)
        assert result is False

    @pytest.mark.asyncio
    async def test_create_slides_wait_with_no_notebook_returns_none(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        result = await mgr.create_slides_wait()
        assert result is None

    @pytest.mark.asyncio
    async def test_create_infographic_wait_with_no_notebook_returns_none(self):
        from noterang.artifacts import ArtifactManager
        mgr = ArtifactManager()
        result = await mgr.create_infographic_wait()
        assert result is None
