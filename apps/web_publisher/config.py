#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPublisher 설정
"""
import logging
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# .env.local 로드
try:
    from dotenv import load_dotenv
    for env_path in [
        Path(__file__).parent / '.env.local',
        Path("D:/Projects/notebooklm-automation/.env.local"),
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug("Loaded environment variables from %s", env_path)
            break
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_WEBAPP_DIR = Path("D:/Projects/miryangosweb")
DEFAULT_DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")
DEFAULT_FIREBASE_PROJECT_ID = "miryangosweb"
DEFAULT_DESIGN = "인포그래픽"
DEFAULT_SLIDE_COUNT = 15
DEFAULT_ARTICLE_TYPE = "disease"


@dataclass
class WebPublisherConfig:
    """Configuration for the WebPublisher pipeline.

    Attributes:
        webapp_dir: Root directory of the Next.js web application.
        firebase_project_id: Firebase project identifier.
        download_dir: Directory where NotebookLM PDFs are downloaded.
        vision_api_key: Google Cloud Vision API key for OCR operations.
        default_design: Default slide design preset name.
        default_slide_count: Default number of slides to generate.
        default_article_type: Default article type for the web archive.
    """

    webapp_dir: Path = field(default_factory=lambda: DEFAULT_WEBAPP_DIR)
    firebase_project_id: str = DEFAULT_FIREBASE_PROJECT_ID
    download_dir: Path = field(default_factory=lambda: DEFAULT_DOWNLOAD_DIR)
    vision_api_key: str = ""
    default_design: str = DEFAULT_DESIGN
    default_slide_count: int = DEFAULT_SLIDE_COUNT
    default_article_type: str = DEFAULT_ARTICLE_TYPE

    @property
    def uploads_dir(self) -> Path:
        """Return the public uploads directory inside the web application.

        Returns:
            Path to ``<webapp_dir>/public/uploads``.
        """
        return self.webapp_dir / "public" / "uploads"

    @classmethod
    def load(cls) -> 'WebPublisherConfig':
        """Create a :class:`WebPublisherConfig` populated from environment variables.

        Reads the following variables:
            - ``GOOGLE_CLOUD_VISION_API_KEY`` / ``GOOGLE_VISION_API_KEY``
            - ``WEBAPP_DIR``
            - ``FIREBASE_PROJECT_ID``

        Returns:
            Configured :class:`WebPublisherConfig` instance.
        """
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

        logger.debug(
            "WebPublisherConfig loaded: webapp_dir=%s, project=%s",
            config.webapp_dir,
            config.firebase_project_id,
        )
        return config
