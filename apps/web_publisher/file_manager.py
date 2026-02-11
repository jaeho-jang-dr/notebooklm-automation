#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파일 관리 - Firebase Storage 업로드
"""
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def _get_storage_bucket(bucket_name: str):
    """Firebase Storage bucket 가져오기 (lazy init)"""
    import firebase_admin
    from firebase_admin import storage

    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={
            'storageBucket': bucket_name,
        })

    return storage.bucket(bucket_name)


class FileManager:
    """Firebase Storage에 파일 업로드"""

    def __init__(self, storage_bucket: str = "miryangosweb.firebasestorage.app"):
        self.storage_bucket = storage_bucket

    def copy_pdf_and_thumbnail(
        self,
        pdf_path: Path,
        title: str,
        thumbnail: bytes = None,
    ) -> Tuple[str, Optional[str]]:
        """
        PDF 파일과 썸네일을 Firebase Storage에 업로드

        Returns:
            (pdf_url, thumb_url) — Firebase Storage 다운로드 URL
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_title = title.replace(" ", "_").replace("/", "-")

        bucket = _get_storage_bucket(self.storage_bucket)

        # PDF 업로드
        pdf_name = f"noterang_{timestamp}_{unique_id}_{safe_title}.pdf"
        pdf_blob = bucket.blob(f"articles/{pdf_name}")
        pdf_blob.upload_from_filename(str(pdf_path), content_type="application/pdf")
        pdf_blob.make_public()
        pdf_url = pdf_blob.public_url
        print(f"  PDF 업로드: {pdf_url}")

        # 썸네일 업로드
        thumb_url = None
        if thumbnail:
            thumb_name = f"noterang_{timestamp}_{unique_id}_{safe_title}_thumb.png"
            thumb_blob = bucket.blob(f"articles/{thumb_name}")
            thumb_blob.upload_from_string(thumbnail, content_type="image/png")
            thumb_blob.make_public()
            thumb_url = thumb_blob.public_url
            print(f"  썸네일 업로드: {thumb_url}")

        return pdf_url, thumb_url
