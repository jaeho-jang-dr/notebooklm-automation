#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firestore 자료실 등록 클라이언트
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class FirestoreClient:
    """Firebase Admin Firestore 클라이언트"""

    def __init__(self, project_id: str = "miryangosweb"):
        self.project_id = project_id
        self._db = None

    def _get_db(self):
        """Firestore 클라이언트 초기화 (lazy)"""
        if self._db is not None:
            return self._db

        import firebase_admin
        from firebase_admin import firestore as fs_admin

        if not firebase_admin._apps:
            try:
                import os
                cred = None
                # 서비스 계정 경로 확인 순서:
                # 1. 환경 변수 FIREBASE_SERVICE_ACCOUNT_PATH
                # 2. 사용자 홈/Downloads/miryangosweb-*.json
                # 3. 프로젝트 루트/firebase-service-account.json
                # 4. ADC (Default)

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
                        'projectId': self.project_id,
                    })
                else:
                    firebase_admin.initialize_app(options={
                        'projectId': self.project_id,
                    })
                print("  Firebase Admin 초기화 완료")
            except Exception as e:
                print(f"  Firebase 초기화 실패: {e}")
                raise

        self._db = fs_admin.client()
        return self._db

    def register_article(
        self,
        title: str,
        pdf_url: str,
        thumb_url: Optional[str],
        analysis: Dict[str, Any],
        tags: List[str],
        article_type: str = "disease",
        visible: bool = True,
    ) -> Optional[str]:
        """
        Firestore articles 컬렉션에 문서 등록

        Returns:
            문서 ID 또는 None
        """
        from firebase_admin import firestore as fs_admin

        db = self._get_db()

        page_count = analysis.get("page_count", 0)
        summary_text = analysis.get("summary", "")

        # 슬라이드 제목들로 요약 구성
        titles = analysis.get("titles", [])

        # PyMuPDF 제목 추출 실패 시 → OCR content에서 [슬라이드 N] 패턴으로 폴백
        if not titles:
            import re as _re
            full_content_for_titles = analysis.get("content", "")
            _matches = _re.findall(
                r'\[슬라이드\s*\d+\]\s*\n(.+?)(?:\n|$)', full_content_for_titles
            )
            titles = [m.strip() for m in _matches if len(m.strip()) >= 2]

        if titles:
            title_summary = " / ".join(titles[:6])
            summary = f"{title} - {title_summary}"
            if len(titles) > 6:
                summary += f" 외 {len(titles) - 6}장"
        else:
            summary = f"{title}에 대해 알기 쉽게 정리한 슬라이드 자료입니다."

        # summary_text 재생성 (titles로부터)
        if titles and not summary_text:
            summary_text = "\n".join(
                f"{i}. {t[:60]}" for i, t in enumerate(titles, 1)
            )

        # 본문: 첫 페이지 이미지 + 슬라이드 목차 + 전체 텍스트
        content_parts = []

        # 첫 페이지 이미지를 content 최상단에 markdown으로 삽입
        if thumb_url:
            content_parts.append(f"![{title}]({thumb_url})\n")

        if summary_text:
            content_parts.append(f"\n[슬라이드 목차]\n{summary_text}\n")

        # 전체 텍스트 (8000자 제한)
        full_content = analysis.get("content", "")
        if full_content:
            if len(full_content) > 8000:
                full_content = full_content[:8000] + "\n\n... (이하 생략)"
            content_parts.append(f"\n[전체 내용]\n{full_content}")

        doc_data = {
            'title': title,
            'type': article_type,
            'tags': tags,
            'summary': summary[:200],
            'content': "\n".join(content_parts),
            'attachmentUrl': pdf_url,
            'attachmentName': Path(pdf_url).name,
            'images': [],
            'isVisible': visible,
            'createdAt': fs_admin.SERVER_TIMESTAMP,
        }

        try:
            _, doc_ref = db.collection('articles').add(doc_data)
            doc_id = doc_ref.id
            print(f"  자료실 등록 완료: {doc_id}")
            print(f"  공개: {'예' if visible else '아니오 (관리자 검토 필요)'}")
            return doc_id
        except Exception as e:
            print(f"  Firestore 등록 실패: {e}")
            return None
