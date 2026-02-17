#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM Automation 테스트 설정
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트를 PATH에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 테스트용 임시 디렉토리
@pytest.fixture
def tmp_dir(tmp_path):
    """테스트용 임시 디렉토리"""
    return tmp_path


@pytest.fixture
def mock_config(tmp_path):
    """테스트용 NoterangConfig"""
    from noterang.config import NoterangConfig
    config = NoterangConfig(
        download_dir=tmp_path / "downloads",
        auth_dir=tmp_path / "auth",
        timeout_slides=600,
        timeout_research=120,
        timeout_download=60,
        timeout_login=120,
        browser_headless=True,
        default_language="ko",
        debug=True,
    )
    config.ensure_dirs()
    return config


@pytest.fixture
def sample_config_json(tmp_path):
    """테스트용 설정 JSON 파일"""
    config_data = {
        "download_dir": str(tmp_path / "downloads"),
        "auth_dir": str(tmp_path / "auth"),
        "timeout_slides": 600,
        "timeout_research": 120,
        "default_language": "ko",
        "debug": True,
    }
    config_file = tmp_path / "noterang_config.json"
    config_file.write_text(json.dumps(config_data, ensure_ascii=False), encoding="utf-8")
    return config_file


@pytest.fixture
def mock_env_vars():
    """테스트용 환경 변수"""
    env = {
        "GOOGLE_EMAIL": "test@gmail.com",
        "GOOGLE_PASSWORD": "testpassword",
        "GOOGLE_2FA_SECRET": "JBSWY3DPEHPK3PXP",
        "NOTEBOOKLM_APP_PASSWORD": "xxxx yyyy zzzz wwww",
        "APIFY_API_KEY": "apify_test_key",
    }
    with patch.dict(os.environ, env):
        yield env
