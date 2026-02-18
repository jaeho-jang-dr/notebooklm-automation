#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파일 관리 - UUID 파일명 + uploads 복사
"""
import logging
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
_UUID_LENGTH = 8
_FILE_PREFIX = "noterang"


class FileManager:
    """Copy PDF files and thumbnails into the web application uploads directory.

    Each file is given a unique name composed of a timestamp, a short UUID
    fragment, and a sanitised version of the article title to avoid collisions
    and make names human-readable.

    Attributes:
        uploads_dir: Target directory for uploaded files.
    """

    def __init__(self, uploads_dir: Path) -> None:
        """Initialise the manager and ensure the uploads directory exists.

        Args:
            uploads_dir: Directory where uploaded files will be stored.
        """
        self.uploads_dir = uploads_dir
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def copy_pdf_and_thumbnail(
        self,
        pdf_path: Path,
        title: str,
        thumbnail: Optional[bytes] = None,
    ) -> Tuple[str, Optional[str]]:
        """Copy a PDF and optional thumbnail into the uploads directory.

        File names follow the pattern::

            noterang_<YYYYMMDD_HHMMSS>_<uid>_<safe_title>.pdf
            noterang_<YYYYMMDD_HHMMSS>_<uid>_<safe_title>_thumb.png

        Args:
            pdf_path: Source PDF file to copy.
            title: Article title used in the generated file name.
            thumbnail: Raw PNG bytes for the thumbnail image. When ``None``,
                no thumbnail is saved.

        Returns:
            Tuple of ``(pdf_url, thumb_url)`` where each value is a web-root-
            relative path such as ``"/uploads/noterang_....pdf"``.
            *thumb_url* is ``None`` when no thumbnail was provided.
        """
        timestamp = datetime.now().strftime(_TIMESTAMP_FORMAT)
        unique_id = uuid.uuid4().hex[:_UUID_LENGTH]
        safe_title = title.replace(" ", "_").replace("/", "-")

        pdf_name = f"{_FILE_PREFIX}_{timestamp}_{unique_id}_{safe_title}.pdf"
        pdf_dest = self.uploads_dir / pdf_name
        shutil.copy2(str(pdf_path), str(pdf_dest))
        pdf_url = f"/uploads/{pdf_name}"
        logger.info("PDF copied to %s", pdf_dest)

        thumb_url: Optional[str] = None
        if thumbnail:
            thumb_name = f"{_FILE_PREFIX}_{timestamp}_{unique_id}_{safe_title}_thumb.png"
            thumb_dest = self.uploads_dir / thumb_name
            thumb_dest.write_bytes(thumbnail)
            thumb_url = f"/uploads/{thumb_name}"
            logger.info("Thumbnail saved to %s", thumb_dest)

        return pdf_url, thumb_url
