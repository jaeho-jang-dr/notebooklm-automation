#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPublisher 설정
"""
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# .env.local 로드
try:
    from dotenv import load_dotenv
    for env_path in [
        Path(__file__).parent / '.env.local',
        Path("D:/Projects/notebooklm-automation/.env.local"),
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass


@dataclass
class WebPublisherConfig:
    """웹 자료실 퍼블리셔 설정"""

    # 웹앱 경로
    webapp_dir: Path = field(default_factory=lambda: Path("D:/Entertainments/DevEnvironment/miryangosweb"))

    # Firebase
    firebase_project_id: str = "miryangosweb"

    # 다운로드 디렉토리
    download_dir: Path = field(default_factory=lambda: Path("G:/내 드라이브/notebooklm"))

    # Vision API
    vision_api_key: str = ""

    # Firebase Storage
    storage_bucket: str = "miryangosweb.firebasestorage.app"

    # 기본값
    default_design: str = "인포그래픽"
    default_slide_count: int = 15
    default_article_type: str = "disease"

    @property
    def uploads_dir(self) -> Path:
        return self.webapp_dir / "public" / "uploads"

    @classmethod
    def load(cls) -> 'WebPublisherConfig':
        """환경변수에서 설정 로드"""
        config = cls()
        config.vision_api_key = (
            os.getenv('GOOGLE_CLOUD_VISION_API_KEY')
            or os.getenv('GOOGLE_VISION_API_KEY')
            or ''
        )

        webapp = os.getenv('WEBAPP_DIR')
        if webapp:
            config.webapp_dir = Path(webapp)

        project_id = os.getenv('FIREBASE_PROJECT_ID')
        if project_id:
            config.firebase_project_id = project_id

        bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
        if bucket:
            config.storage_bucket = bucket

        return config
