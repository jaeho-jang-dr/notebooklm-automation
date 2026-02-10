#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM Python API Client - Singleton Factory

notebooklm-mcp-cli (notebooklm_tools) Python API direct integration.
Replaces subprocess-based nlm CLI calls.

TTL 추적으로 인증 만료 자동 감지 및 갱신 지원.
"""
import sys
import time
import logging

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------

class NLMClientError(Exception):
    """Base error for NLM client operations."""


class NLMAuthError(NLMClientError):
    """Authentication-related error."""


# ---------------------------------------------------------------------------
# Singleton client with TTL tracking
# ---------------------------------------------------------------------------

_client = None
_client_created_at: float = 0.0
_CLIENT_TTL: int = 1200  # 20분 (Google 세션 30-60분보다 여유있게)


def get_nlm_client(force_refresh: bool = False):
    """
    Get or create a NotebookLMClient singleton.

    Uses ``notebooklm_tools.core.auth.load_cached_tokens()`` to obtain
    cookies/CSRF, then constructs a ``NotebookLMClient``.

    TTL 만료시 자동으로 클라이언트를 갱신합니다.

    Args:
        force_refresh: Discard cached client and create a new one.

    Returns:
        NotebookLMClient instance.

    Raises:
        NLMAuthError: If no cached tokens are found.
    """
    global _client, _client_created_at

    # TTL 만료 체크
    if _client is not None and not force_refresh:
        age = time.time() - _client_created_at
        if age > _CLIENT_TTL:
            print(f"  NLM 클라이언트 TTL 만료 ({int(age)}초) → 갱신")
            close_nlm_client()
            force_refresh = True

    if _client is not None and not force_refresh:
        return _client

    from notebooklm_tools.core.auth import load_cached_tokens
    from notebooklm_tools.core.client import NotebookLMClient

    tokens = load_cached_tokens()
    if tokens is None:
        raise NLMAuthError(
            "No cached auth tokens found. Run 'nlm login' first."
        )

    _client = NotebookLMClient(
        cookies=tokens.cookies,
        csrf_token=tokens.csrf_token,
        session_id=tokens.session_id,
    )
    _client_created_at = time.time()
    return _client


def close_nlm_client():
    """Close and discard the singleton client."""
    global _client, _client_created_at
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
    _client_created_at = 0.0


def is_client_expired() -> bool:
    """클라이언트 TTL 만료 여부 확인"""
    if _client is None:
        return True
    return (time.time() - _client_created_at) > _CLIENT_TTL


def check_nlm_auth() -> bool:
    """
    Quick auth check by attempting ``list_notebooks()``.

    Returns:
        True if the API responds successfully, False otherwise.
    """
    try:
        client = get_nlm_client()
        client.list_notebooks()
        return True
    except Exception:
        return False
