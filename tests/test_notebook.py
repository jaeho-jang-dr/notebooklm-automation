#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for noterang/notebook.py

Tests:
  - list_notebooks()
  - find_notebook()
  - create_notebook()
  - delete_notebook()
  - get_or_create_notebook()
  - start_research()
  - check_research_status()
  - import_research()
  - get_notebook_sources()
  - add_source_url()
  - add_source_text()
  - NotebookManager class
  - get_notebook_manager() singleton
"""
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper fixture: reset global NotebookManager singleton
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_notebook_manager():
    import noterang.notebook as nb_mod
    nb_mod._manager = None
    yield
    nb_mod._manager = None


# ---------------------------------------------------------------------------
# Tests: list_notebooks
# ---------------------------------------------------------------------------

class TestListNotebooks:

    def test_returns_list_of_dicts(self, mock_nlm_client):
        nb1 = MagicMock(id="id-1", title="노트북1")
        nb2 = MagicMock(id="id-2", title="노트북2")
        mock_nlm_client.list_notebooks.return_value = [nb1, nb2]

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import list_notebooks
            result = list_notebooks()

        assert len(result) == 2
        assert result[0] == {"id": "id-1", "title": "노트북1"}
        assert result[1] == {"id": "id-2", "title": "노트북2"}

    def test_returns_empty_list_on_exception(self, mock_nlm_client):
        mock_nlm_client.list_notebooks.side_effect = Exception("network error")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import list_notebooks
            result = list_notebooks()

        assert result == []

    def test_returns_empty_list_when_no_notebooks(self, mock_nlm_client):
        mock_nlm_client.list_notebooks.return_value = []

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import list_notebooks
            result = list_notebooks()

        assert result == []


# ---------------------------------------------------------------------------
# Tests: find_notebook
# ---------------------------------------------------------------------------

class TestFindNotebook:

    def test_finds_existing_notebook_by_title(self, mock_nlm_client):
        nb = MagicMock(id="id-abc", title="무릎 통증")
        mock_nlm_client.list_notebooks.return_value = [nb]

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import find_notebook
            result = find_notebook("무릎 통증")

        assert result == {"id": "id-abc", "title": "무릎 통증"}

    def test_returns_none_when_not_found(self, mock_nlm_client):
        nb = MagicMock(id="id-abc", title="다른 노트북")
        mock_nlm_client.list_notebooks.return_value = [nb]

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import find_notebook
            result = find_notebook("없는 노트북")

        assert result is None

    def test_returns_none_on_empty_list(self, mock_nlm_client):
        mock_nlm_client.list_notebooks.return_value = []

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import find_notebook
            result = find_notebook("아무거나")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: create_notebook
# ---------------------------------------------------------------------------

class TestCreateNotebook:

    def test_creates_notebook_and_returns_id(self, mock_nlm_client):
        mock_nlm_client.create_notebook.return_value = MagicMock(id="nb-new-id-12345678")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import create_notebook
            result = create_notebook("새 노트북")

        assert result == "nb-new-id-12345678"
        mock_nlm_client.create_notebook.assert_called_once_with("새 노트북")

    def test_returns_none_when_no_id_in_response(self, mock_nlm_client):
        mock_nlm_client.create_notebook.return_value = MagicMock(id=None)

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import create_notebook
            result = create_notebook("노트북")

        assert result is None

    def test_returns_none_when_response_is_none(self, mock_nlm_client):
        mock_nlm_client.create_notebook.return_value = None

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import create_notebook
            result = create_notebook("노트북")

        assert result is None

    def test_returns_none_on_exception(self, mock_nlm_client):
        mock_nlm_client.create_notebook.side_effect = Exception("API error")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import create_notebook
            result = create_notebook("노트북")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: delete_notebook
# ---------------------------------------------------------------------------

class TestDeleteNotebook:

    def test_deletes_notebook_successfully(self, mock_nlm_client):
        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import delete_notebook
            result = delete_notebook("nb-id-12345678")

        assert result is True
        mock_nlm_client.delete_notebook.assert_called_once_with("nb-id-12345678")

    def test_returns_false_on_exception(self, mock_nlm_client):
        mock_nlm_client.delete_notebook.side_effect = Exception("not found")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import delete_notebook
            result = delete_notebook("bad-id-12345678")

        assert result is False


# ---------------------------------------------------------------------------
# Tests: get_or_create_notebook
# ---------------------------------------------------------------------------

class TestGetOrCreateNotebook:

    def test_returns_existing_notebook_id(self, mock_nlm_client):
        nb = MagicMock(id="existing-id-12", title="기존 노트북")
        mock_nlm_client.list_notebooks.return_value = [nb]

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import get_or_create_notebook
            result = get_or_create_notebook("기존 노트북")

        assert result == "existing-id-12"
        mock_nlm_client.create_notebook.assert_not_called()

    def test_creates_new_when_not_found(self, mock_nlm_client):
        mock_nlm_client.list_notebooks.return_value = []
        mock_nlm_client.create_notebook.return_value = MagicMock(id="new-id-12345678")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import get_or_create_notebook
            result = get_or_create_notebook("새 노트북")

        assert result == "new-id-12345678"
        mock_nlm_client.create_notebook.assert_called_once_with("새 노트북")


# ---------------------------------------------------------------------------
# Tests: start_research
# ---------------------------------------------------------------------------

class TestStartResearch:

    def test_returns_task_id_on_success(self, mock_nlm_client):
        mock_nlm_client.start_research.return_value = {"task_id": "task-xyz-001"}

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import start_research
            result = start_research("nb-id-12345678", "무릎 통증 치료")

        assert result == "task-xyz-001"

    def test_returns_none_when_no_task_id(self, mock_nlm_client):
        mock_nlm_client.start_research.return_value = {}

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import start_research
            result = start_research("nb-id-12345678", "query")

        assert result is None

    def test_returns_none_when_result_is_none(self, mock_nlm_client):
        mock_nlm_client.start_research.return_value = None

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import start_research
            result = start_research("nb-id-12345678", "query")

        assert result is None

    def test_returns_none_on_exception(self, mock_nlm_client):
        mock_nlm_client.start_research.side_effect = Exception("timeout")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import start_research
            result = start_research("nb-id-12345678", "query")

        assert result is None

    def test_passes_mode_to_client(self, mock_nlm_client):
        mock_nlm_client.start_research.return_value = {"task_id": "t1"}

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import start_research
            start_research("nb-id-12345678", "query", mode="deep")

        mock_nlm_client.start_research.assert_called_once_with(
            "nb-id-12345678", "query", source="web", mode="deep"
        )


# ---------------------------------------------------------------------------
# Tests: check_research_status
# ---------------------------------------------------------------------------

class TestCheckResearchStatus:

    def test_returns_true_and_completed_status(self, mock_nlm_client):
        mock_nlm_client.poll_research.return_value = {"status": "completed"}

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import check_research_status
            done, status = check_research_status("nb-id", task_id="t1")

        assert done is True
        assert status == "completed"

    def test_returns_false_when_in_progress(self, mock_nlm_client):
        mock_nlm_client.poll_research.return_value = {"status": "in_progress"}

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import check_research_status
            done, status = check_research_status("nb-id")

        assert done is False
        assert status == "in_progress"

    def test_returns_false_when_no_result(self, mock_nlm_client):
        mock_nlm_client.poll_research.return_value = None

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import check_research_status
            done, status = check_research_status("nb-id")

        assert done is False
        assert status == "no_research"

    def test_returns_error_string_on_exception(self, mock_nlm_client):
        mock_nlm_client.poll_research.side_effect = Exception("network timeout")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import check_research_status
            done, status = check_research_status("nb-id")

        assert done is False
        assert "network timeout" in status


# ---------------------------------------------------------------------------
# Tests: import_research
# ---------------------------------------------------------------------------

class TestImportResearch:

    def test_returns_count_of_imported_sources(self, mock_nlm_client):
        mock_nlm_client.poll_research.return_value = {
            "sources": [{"url": "http://a.com"}, {"url": "http://b.com"}]
        }
        mock_nlm_client.import_research_sources.return_value = ["s1", "s2"]

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import import_research
            count = import_research("nb-id", "task-1")

        assert count == 2

    def test_returns_zero_when_no_sources(self, mock_nlm_client):
        mock_nlm_client.poll_research.return_value = {"sources": []}

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import import_research
            count = import_research("nb-id", "task-1")

        assert count == 0

    def test_returns_zero_when_poll_returns_none(self, mock_nlm_client):
        mock_nlm_client.poll_research.return_value = None

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import import_research
            count = import_research("nb-id", "task-1")

        assert count == 0

    def test_returns_zero_on_exception(self, mock_nlm_client):
        mock_nlm_client.poll_research.side_effect = Exception("error")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import import_research
            count = import_research("nb-id", "task-1")

        assert count == 0


# ---------------------------------------------------------------------------
# Tests: get_notebook_sources / add_source_url / add_source_text
# ---------------------------------------------------------------------------

class TestNotebookSources:

    def test_get_notebook_sources_returns_list(self, mock_nlm_client):
        mock_nlm_client.get_notebook_sources_with_types.return_value = [
            {"type": "url", "url": "http://example.com"}
        ]

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import get_notebook_sources
            result = get_notebook_sources("nb-id")

        assert len(result) == 1

    def test_get_notebook_sources_returns_empty_on_exception(self, mock_nlm_client):
        mock_nlm_client.get_notebook_sources_with_types.side_effect = Exception("err")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import get_notebook_sources
            result = get_notebook_sources("nb-id")

        assert result == []

    def test_get_notebook_sources_returns_empty_for_non_list(self, mock_nlm_client):
        mock_nlm_client.get_notebook_sources_with_types.return_value = "not a list"

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import get_notebook_sources
            result = get_notebook_sources("nb-id")

        assert result == []

    def test_add_source_url_returns_true_on_success(self, mock_nlm_client):
        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import add_source_url
            result = add_source_url("nb-id", "http://example.com")

        assert result is True
        mock_nlm_client.add_url_source.assert_called_once_with("nb-id", "http://example.com")

    def test_add_source_url_returns_false_on_exception(self, mock_nlm_client):
        mock_nlm_client.add_url_source.side_effect = Exception("rejected")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import add_source_url
            result = add_source_url("nb-id", "http://bad.com")

        assert result is False

    def test_add_source_text_returns_true_on_success(self, mock_nlm_client):
        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import add_source_text
            result = add_source_text("nb-id", "텍스트 내용", "텍스트 소스")

        assert result is True

    def test_add_source_text_returns_false_on_exception(self, mock_nlm_client):
        mock_nlm_client.add_text_source.side_effect = Exception("quota")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import add_source_text
            result = add_source_text("nb-id", "텍스트")

        assert result is False


# ---------------------------------------------------------------------------
# Tests: NotebookManager
# ---------------------------------------------------------------------------

class TestNotebookManager:

    def test_initial_state_is_empty(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        assert mgr.current_notebook_id is None
        assert mgr.current_title is None

    def test_set_current(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        mgr.set_current("id-xyz", "테스트 노트북")
        assert mgr.current_notebook_id == "id-xyz"
        assert mgr.current_title == "테스트 노트북"

    def test_create_sets_current(self, mock_nlm_client):
        mock_nlm_client.list_notebooks.return_value = []
        mock_nlm_client.create_notebook.return_value = MagicMock(id="new-nb-12345678")

        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import NotebookManager
            mgr = NotebookManager()
            nb_id = mgr.create("새 노트북")

        assert nb_id == "new-nb-12345678"
        assert mgr.current_notebook_id == "new-nb-12345678"
        assert mgr.current_title == "새 노트북"

    def test_delete_clears_current_when_matching(self, mock_nlm_client):
        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import NotebookManager
            mgr = NotebookManager()
            mgr.set_current("nb-12345678", "테스트")
            result = mgr.delete("nb-12345678")

        assert result is True
        assert mgr.current_notebook_id is None
        assert mgr.current_title is None

    def test_delete_without_id_uses_current(self, mock_nlm_client):
        with patch("noterang.notebook.get_nlm_client", return_value=mock_nlm_client):
            from noterang.notebook import NotebookManager
            mgr = NotebookManager()
            mgr.set_current("cur-nb-12345678", "현재")
            result = mgr.delete()  # no explicit id

        assert result is True
        mock_nlm_client.delete_notebook.assert_called_once_with("cur-nb-12345678")

    def test_delete_without_current_returns_false(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        result = mgr.delete()
        assert result is False

    def test_get_sources_returns_empty_without_notebook(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        result = mgr.get_sources()
        assert result == []

    def test_research_returns_none_without_notebook(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        result = mgr.research("query")
        assert result is None

    def test_check_research_returns_false_without_notebook(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        done, status = mgr.check_research()
        assert done is False

    def test_import_research_results_returns_zero_without_notebook(self):
        from noterang.notebook import NotebookManager
        mgr = NotebookManager()
        result = mgr.import_research_results("task-id")
        assert result == 0


# ---------------------------------------------------------------------------
# Tests: get_notebook_manager singleton
# ---------------------------------------------------------------------------

class TestGetNotebookManager:

    def test_returns_singleton(self):
        from noterang.notebook import get_notebook_manager
        m1 = get_notebook_manager()
        m2 = get_notebook_manager()
        assert m1 is m2

    def test_returns_notebook_manager_instance(self):
        from noterang.notebook import get_notebook_manager, NotebookManager
        mgr = get_notebook_manager()
        assert isinstance(mgr, NotebookManager)
