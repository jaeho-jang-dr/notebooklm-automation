#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for noterang/nlm_client.py

Tests:
  - get_nlm_client() singleton creation and TTL expiry
  - close_nlm_client() cleanup
  - is_client_expired() logic
  - check_nlm_auth() happy path and failure
"""
import time
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers: reset the module-level singleton between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_nlm_client_state():
    """Reset global singleton state before every test."""
    import noterang.nlm_client as nlm_mod
    nlm_mod._client = None
    nlm_mod._client_created_at = 0.0
    yield
    nlm_mod._client = None
    nlm_mod._client_created_at = 0.0


# ---------------------------------------------------------------------------
# Tests: get_nlm_client
# ---------------------------------------------------------------------------

class TestGetNlmClient:

    def test_creates_new_client_when_none_exists(self):
        """get_nlm_client() calls load_cached_tokens and NotebookLMClient."""
        mock_tokens = MagicMock()
        mock_tokens.cookies = {"cookie": "val"}
        mock_tokens.csrf_token = "csrf-123"
        mock_tokens.session_id = "sess-456"

        mock_client = MagicMock()

        with patch("noterang.nlm_client.load_cached_tokens", return_value=mock_tokens) as mock_load, \
             patch("noterang.nlm_client.NotebookLMClient", return_value=mock_client) as mock_cls:
            from noterang.nlm_client import get_nlm_client
            result = get_nlm_client()

        assert result is mock_client
        mock_load.assert_called_once()
        mock_cls.assert_called_once_with(
            cookies=mock_tokens.cookies,
            csrf_token=mock_tokens.csrf_token,
            session_id=mock_tokens.session_id,
        )

    def test_returns_existing_client_when_fresh(self):
        """Singleton is reused if TTL has not expired."""
        import noterang.nlm_client as nlm_mod

        mock_client = MagicMock()
        nlm_mod._client = mock_client
        nlm_mod._client_created_at = time.time()  # just created

        with patch("noterang.nlm_client.load_cached_tokens") as mock_load:
            from noterang.nlm_client import get_nlm_client
            result = get_nlm_client()

        assert result is mock_client
        mock_load.assert_not_called()

    def test_refreshes_client_on_ttl_expiry(self):
        """Expired client is replaced with a new one."""
        import noterang.nlm_client as nlm_mod

        old_client = MagicMock()
        nlm_mod._client = old_client
        nlm_mod._client_created_at = time.time() - 9999  # far in the past

        mock_tokens = MagicMock()
        mock_tokens.cookies = {}
        mock_tokens.csrf_token = "tok"
        mock_tokens.session_id = "sess"
        new_client = MagicMock()

        with patch("noterang.nlm_client.load_cached_tokens", return_value=mock_tokens), \
             patch("noterang.nlm_client.NotebookLMClient", return_value=new_client):
            from noterang.nlm_client import get_nlm_client
            result = get_nlm_client()

        # old client should have been closed during TTL refresh
        old_client.close.assert_called_once()
        assert result is new_client

    def test_force_refresh_replaces_fresh_client(self):
        """force_refresh=True bypasses TTL and replaces an existing client."""
        import noterang.nlm_client as nlm_mod

        existing_client = MagicMock()
        nlm_mod._client = existing_client
        nlm_mod._client_created_at = time.time()

        mock_tokens = MagicMock()
        mock_tokens.cookies = {}
        mock_tokens.csrf_token = "t"
        mock_tokens.session_id = "s"
        fresh_client = MagicMock()

        with patch("noterang.nlm_client.load_cached_tokens", return_value=mock_tokens), \
             patch("noterang.nlm_client.NotebookLMClient", return_value=fresh_client):
            from noterang.nlm_client import get_nlm_client
            result = get_nlm_client(force_refresh=True)

        assert result is fresh_client

    def test_raises_nlm_auth_error_when_no_tokens(self):
        """NLMAuthError raised when load_cached_tokens returns None."""
        from noterang.nlm_client import NLMAuthError, get_nlm_client

        with patch("noterang.nlm_client.load_cached_tokens", return_value=None):
            with pytest.raises(NLMAuthError):
                get_nlm_client()

    def test_records_creation_timestamp(self):
        """_client_created_at is set close to now after creation."""
        import noterang.nlm_client as nlm_mod

        mock_tokens = MagicMock()
        mock_tokens.cookies = {}
        mock_tokens.csrf_token = "t"
        mock_tokens.session_id = "s"

        before = time.time()
        with patch("noterang.nlm_client.load_cached_tokens", return_value=mock_tokens), \
             patch("noterang.nlm_client.NotebookLMClient", return_value=MagicMock()):
            from noterang.nlm_client import get_nlm_client
            get_nlm_client()
        after = time.time()

        assert before <= nlm_mod._client_created_at <= after


# ---------------------------------------------------------------------------
# Tests: close_nlm_client
# ---------------------------------------------------------------------------

class TestCloseNlmClient:

    def test_closes_and_clears_existing_client(self):
        """close_nlm_client() calls client.close() and resets singleton."""
        import noterang.nlm_client as nlm_mod
        from noterang.nlm_client import close_nlm_client

        mock_client = MagicMock()
        nlm_mod._client = mock_client
        nlm_mod._client_created_at = 12345.0

        close_nlm_client()

        mock_client.close.assert_called_once()
        assert nlm_mod._client is None
        assert nlm_mod._client_created_at == 0.0

    def test_close_when_no_client_is_safe(self):
        """close_nlm_client() with no existing client does not raise."""
        from noterang.nlm_client import close_nlm_client
        close_nlm_client()  # should not raise

    def test_close_suppresses_exception_from_client_close(self):
        """Exceptions during client.close() are suppressed gracefully."""
        import noterang.nlm_client as nlm_mod
        from noterang.nlm_client import close_nlm_client

        bad_client = MagicMock()
        bad_client.close.side_effect = RuntimeError("socket error")
        nlm_mod._client = bad_client

        close_nlm_client()  # should not raise
        assert nlm_mod._client is None


# ---------------------------------------------------------------------------
# Tests: is_client_expired
# ---------------------------------------------------------------------------

class TestIsClientExpired:

    def test_returns_true_when_no_client(self):
        """No client means expired."""
        from noterang.nlm_client import is_client_expired
        assert is_client_expired() is True

    def test_returns_false_when_fresh_client(self):
        """Fresh client (just created) is not expired."""
        import noterang.nlm_client as nlm_mod
        from noterang.nlm_client import is_client_expired

        nlm_mod._client = MagicMock()
        nlm_mod._client_created_at = time.time()

        assert is_client_expired() is False

    def test_returns_true_when_ttl_exceeded(self):
        """Client older than _CLIENT_TTL is expired."""
        import noterang.nlm_client as nlm_mod
        from noterang.nlm_client import is_client_expired, _CLIENT_TTL

        nlm_mod._client = MagicMock()
        nlm_mod._client_created_at = time.time() - (_CLIENT_TTL + 1)

        assert is_client_expired() is True


# ---------------------------------------------------------------------------
# Tests: check_nlm_auth
# ---------------------------------------------------------------------------

class TestCheckNlmAuth:

    def test_returns_true_on_successful_list(self):
        """check_nlm_auth() returns True when list_notebooks succeeds."""
        from noterang.nlm_client import check_nlm_auth

        mock_client = MagicMock()
        mock_client.list_notebooks.return_value = []

        with patch("noterang.nlm_client.get_nlm_client", return_value=mock_client):
            assert check_nlm_auth() is True

        mock_client.list_notebooks.assert_called_once()

    def test_returns_false_on_exception(self):
        """check_nlm_auth() returns False when get_nlm_client raises."""
        from noterang.nlm_client import check_nlm_auth, NLMAuthError

        with patch("noterang.nlm_client.get_nlm_client", side_effect=NLMAuthError("no tokens")):
            assert check_nlm_auth() is False

    def test_returns_false_when_list_notebooks_raises(self):
        """check_nlm_auth() returns False when list_notebooks throws."""
        from noterang.nlm_client import check_nlm_auth

        mock_client = MagicMock()
        mock_client.list_notebooks.side_effect = ConnectionError("network error")

        with patch("noterang.nlm_client.get_nlm_client", return_value=mock_client):
            assert check_nlm_auth() is False
