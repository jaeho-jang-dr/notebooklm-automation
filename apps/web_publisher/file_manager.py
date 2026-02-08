#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파일 관리 - UUID 파일명 + uploads 복사
"""
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class FileManager:
    """웹앱 uploads 디렉토리에 파일 복사"""

    def __init__(self, uploads_dir: Path):
        self.uploads_dir = uploads_dir
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def copy_pdf_and_thumbnail(
        self,
        pdf_path: Path,
        title: str,
        thumbnail: bytes = None,
    ) -> Tuple[str, Optional[str]]:
        """
        PDF 파일과 썸네일을 public/uploads에 복사

        Returns:
            (pdf_url, thumb_url) — 웹 경로 (예: /uploads/noterang_..._제목.pdf)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_title = title.replace(" ", "_").replace("/", "-")

        # PDF 복사
        pdf_name = f"noterang_{timestamp}_{unique_id}_{safe_title}.pdf"
        pdf_dest = self.uploads_dir / pdf_name
        shutil.copy2(str(pdf_path), str(pdf_dest))
        pdf_url = f"/uploads/{pdf_name}"
        print(f"  PDF 복사: {pdf_dest}")

        # 썸네일 저장
        thumb_url = None
        if thumbnail:
            thumb_name = f"noterang_{timestamp}_{unique_id}_{safe_title}_thumb.png"
            thumb_dest = self.uploads_dir / thumb_name
            thumb_dest.write_bytes(thumbnail)
            thumb_url = f"/uploads/{thumb_name}"
            print(f"  썸네일 저장: {thumb_dest}")

        return pdf_url, thumb_url
