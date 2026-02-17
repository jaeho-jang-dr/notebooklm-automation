#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_login.py 유닛 테스트 (notebooklm-automation)
- TOTP 코드 생성 테스트 (브라우저 불필요)
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import pyotp

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTOTPCodeGeneration:
    """TOTP 코드 생성 테스트"""

    def test_get_totp_code_returns_6_digits(self, mock_env_vars):
        from noterang.auto_login import get_totp_code
        code = get_totp_code()
        assert len(code) == 6, f"TOTP 코드는 6자리여야 합니다: {code}"
        assert code.isdigit(), f"TOTP 코드는 숫자여야 합니다: {code}"

    def test_get_totp_code_matches_pyotp(self, mock_env_vars):
        from noterang.auto_login import get_totp_code
        secret = mock_env_vars["GOOGLE_2FA_SECRET"]
        expected = pyotp.TOTP(secret.upper()).now()
        actual = get_totp_code()
        assert actual == expected

    def test_get_totp_code_consistency(self, mock_env_vars):
        """같은 시간 윈도우 내 일관성"""
        from noterang.auto_login import get_totp_code
        code1 = get_totp_code()
        code2 = get_totp_code()
        assert code1 == code2

    def test_totp_verify_works(self, mock_env_vars):
        """생성된 코드 검증 가능 확인"""
        secret = mock_env_vars["GOOGLE_2FA_SECRET"]
        totp = pyotp.TOTP(secret.upper())
        code = totp.now()
        assert totp.verify(code)


class TestEnvironmentVariables:
    """환경 변수 로딩 테스트"""

    def test_email_loaded(self, mock_env_vars):
        import importlib
        import noterang.auto_login as auto_login_module
        importlib.reload(auto_login_module)
        assert auto_login_module.EMAIL == "test@gmail.com"

    def test_password_loaded(self, mock_env_vars):
        import importlib
        import noterang.auto_login as auto_login_module
        importlib.reload(auto_login_module)
        assert auto_login_module.PASSWORD == "testpassword"

    def test_totp_secret_loaded(self, mock_env_vars):
        import importlib
        import noterang.auto_login as auto_login_module
        importlib.reload(auto_login_module)
        assert auto_login_module.TOTP_SECRET == "JBSWY3DPEHPK3PXP"

    def test_empty_defaults(self):
        remove_keys = {
            "GOOGLE_EMAIL": "",
            "GOOGLE_PASSWORD": "",
            "GOOGLE_2FA_SECRET": "",
            "NOTEBOOKLM_APP_PASSWORD": "",
            "APIFY_API_KEY": "",
        }
        with patch.dict(os.environ, remove_keys):
            import importlib
            import noterang.auto_login as auto_login_module
            importlib.reload(auto_login_module)
            assert auto_login_module.EMAIL == ""
            assert auto_login_module.PASSWORD == ""


class TestBrowserProfile:
    """브라우저 프로필 경로 테스트"""

    def test_browser_profile_path(self):
        from noterang.auto_login import BROWSER_PROFILE
        assert ".notebooklm-auto-v3" in str(BROWSER_PROFILE)
        assert isinstance(BROWSER_PROFILE, Path)
