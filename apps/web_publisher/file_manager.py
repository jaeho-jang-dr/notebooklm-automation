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
    try:
        import firebase_admin
        from firebase_admin import storage
    except ImportError:
        raise RuntimeError(
            "firebase-admin 패키지가 필요합니다: pip install firebase-admin"
        )

    if not firebase_admin._apps:
        import os
        cred = None
        sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if sa_path and Path(sa_path).exists():
            cred = firebase_admin.credentials.Certificate(sa_path)
        else:
            sa_download = Path.home() / "Downloads" / "miryangosweb-firebase-adminsdk-fbsvc-e139abbe14.json"
            if sa_download.exists():
                cred = firebase_admin.credentials.Certificate(str(sa_download))
            else:
                sa_root = Path(__file__).resolve().parents[3] / "firebase-service-account.json"
                if sa_root.exists():
                    cred = firebase_admin.credentials.Certificate(str(sa_root))

        if cred:
            firebase_admin.initialize_app(cred, options={
                'storageBucket': bucket_name,
            })
        else:
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
