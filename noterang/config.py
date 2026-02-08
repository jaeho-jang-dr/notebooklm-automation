#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 설정 관리
- 환경 설정 로드/저장
- API 키 관리
- 경로 설정
"""
import os
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def _find_nlm_exe() -> Path:
    """nlm.exe 자동 찾기"""
    import shutil

    # 1. PATH에서 찾기
    nlm_path = shutil.which("nlm")
    if nlm_path:
        return Path(nlm_path)

    # 2. 일반적인 위치 검색
    home = Path.home()
    search_paths = [
        home / "AppData/Local/Programs/Python/Python312/Scripts/nlm.exe",
        home / "AppData/Local/Programs/Python/Python311/Scripts/nlm.exe",
        home / "AppData/Local/Programs/Python/Python313/Scripts/nlm.exe",
        home / "AppData/Roaming/Python/Python312/Scripts/nlm.exe",
        home / "AppData/Roaming/Python/Python311/Scripts/nlm.exe",
        home / "AppData/Roaming/Python/Python313/Scripts/nlm.exe",
    ]

    for path in search_paths:
        if path.exists():
            return path

    # 3. 기본값 반환 (없으면 나중에 오류 발생)
    return Path("nlm")


def _find_nlm_auth_exe() -> Path:
    """notebooklm-mcp-auth.exe 자동 찾기"""
    import shutil

    # 1. PATH에서 찾기
    auth_path = shutil.which("notebooklm-mcp-auth")
    if auth_path:
        return Path(auth_path)

    # 2. nlm.exe와 같은 디렉토리에서 찾기
    nlm_exe = _find_nlm_exe()
    if nlm_exe.parent.exists():
        auth_exe = nlm_exe.parent / "notebooklm-mcp-auth.exe"
        if auth_exe.exists():
            return auth_exe

    # 3. 기본값 반환
    return Path("notebooklm-mcp-auth")


@dataclass
class NoterangConfig:
    """노트랑 설정"""

    # 기본 경로
    download_dir: Path = field(default_factory=lambda: Path("G:/내 드라이브/notebooklm"))
    auth_dir: Path = field(default_factory=lambda: Path.home() / ".notebooklm-mcp-cli")

    # NLM CLI 경로 (자동 감지)
    nlm_exe: Path = field(default_factory=lambda: _find_nlm_exe())
    nlm_auth_exe: Path = field(default_factory=lambda: _find_nlm_auth_exe())

    # API 키
    apify_api_key: str = ""
    notebooklm_app_password: str = ""  # 형식: "xxxx xxxx xxxx xxxx"

    # 타임아웃 설정 (초)
    timeout_slides: int = 600       # 10분 (NLM 슬라이드 생성은 느릴 수 있음)
    timeout_research: int = 120     # 2분
    timeout_download: int = 60      # 1분
    timeout_login: int = 120        # 2분

    # 브라우저 설정
    browser_headless: bool = False  # 다운로드는 headless=False 권장
    browser_viewport_width: int = 1920
    browser_viewport_height: int = 1080

    # 기본 언어
    default_language: str = "ko"    # 반드시 한글!

    # 디버그
    debug: bool = False
    save_screenshots: bool = True

    # 병렬 실행
    worker_id: Optional[int] = None  # 병렬 실행시 워커 ID

    @property
    def browser_profile(self) -> Path:
        base = self.auth_dir / "browser_profile"
        if self.worker_id is not None:
            return base.parent / f"browser_profile_{self.worker_id}"
        return base

    @property
    def profile_dir(self) -> Path:
        return self.auth_dir / "profiles" / "default"

    @property
    def root_auth_file(self) -> Path:
        return self.auth_dir / "auth.json"

    @property
    def memory_file(self) -> Path:
        return self.download_dir / "agent_memory.json"

    def ensure_dirs(self):
        """필요한 디렉토리 생성"""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.browser_profile.mkdir(parents=True, exist_ok=True)
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = {}
        for key, value in asdict(self).items():
            if isinstance(value, Path):
                data[key] = str(value)
            else:
                data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoterangConfig':
        """딕셔너리에서 생성"""
        # null 값 제거 (기본값 사용)
        data = {k: v for k, v in data.items() if v is not None}

        # dataclass 필드에 없는 키 제거
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        data = {k: v for k, v in data.items() if k in valid_fields}

        # Path 변환
        path_fields = ['download_dir', 'auth_dir', 'nlm_exe', 'nlm_auth_exe']
        for field in path_fields:
            if field in data and isinstance(data[field], str):
                data[field] = Path(data[field])

        return cls(**data)

    def save(self, path: Optional[Path] = None):
        """설정 저장"""
        save_path = path or (Path(__file__).parent.parent / "noterang_config.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'NoterangConfig':
        """설정 로드"""
        load_path = path or (Path(__file__).parent.parent / "noterang_config.json")

        if load_path.exists():
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)

        # 환경 변수에서 로드
        config = cls()
        config.apify_api_key = os.environ.get('APIFY_API_KEY', '')
        config.notebooklm_app_password = os.environ.get('NOTEBOOKLM_APP_PASSWORD', '')
        return config


# 전역 설정 인스턴스
_config: Optional[NoterangConfig] = None


def get_config() -> NoterangConfig:
    """전역 설정 반환"""
    global _config
    if _config is None:
        _config = NoterangConfig.load()
        _config.ensure_dirs()
    return _config


def set_config(config: NoterangConfig):
    """전역 설정 설정"""
    global _config
    _config = config
    config.ensure_dirs()


def init_config(
    apify_api_key: str = "",
    notebooklm_app_password: str = "",
    download_dir: Optional[str] = None,
    **kwargs
) -> NoterangConfig:
    """설정 초기화"""
    config = NoterangConfig.load()

    if apify_api_key:
        config.apify_api_key = apify_api_key
    if notebooklm_app_password:
        config.notebooklm_app_password = notebooklm_app_password
    if download_dir:
        config.download_dir = Path(download_dir)

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    config.ensure_dirs()
    config.save()
    set_config(config)

    return config
