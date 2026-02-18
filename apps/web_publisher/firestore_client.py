#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firestore 자료실 등록 클라이언트
"""
import logging
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# 재시도 대상 예외 목록 (Google API 일시적 오류)
_RETRYABLE_GOOGLE_ERRORS: tuple = ()
try:
    from google.api_core.exceptions import (
        ServiceUnavailable,
        InternalServerError,
        DeadlineExceeded,
    )
    _RETRYABLE_GOOGLE_ERRORS = (ServiceUnavailable, InternalServerError, DeadlineExceeded)
except ImportError:
    pass  # google-api-core 없으면 일반 Exception으로 폴백


def _retry_sync(func, max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """동기 함수 재시도 (지수 백오프)"""
    for attempt in range(max_attempts):
        try:
            return func()
        except _RETRYABLE_GOOGLE_ERRORS as e:
            if attempt == max_attempts - 1:
                raise
            wait = delay * (backoff ** attempt)
            logger.warning(
                f"Firestore retry {attempt + 1}/{max_attempts}: {e}. "
                f"Waiting {wait:.1f}s..."
            )
            time.sleep(wait)


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
                firebase_admin.initialize_app(options={
                    'projectId': self.project_id,
                })
                print("  Firebase Admin 초기화 완료")
            except ValueError as e:
                # 이미 초기화된 경우 등 설정 오류
                print(f"  Firebase 초기화 설정 오류: {e}")
                logger.error("Firebase init ValueError", exc_info=True)
                raise
            except Exception as e:
                print(f"  Firebase 초기화 실패: {e}")
                logger.error("Firebase init failed", exc_info=True)
                raise

        try:
            self._db = fs_admin.client()
        except Exception as e:
            print(f"  Firestore 클라이언트 생성 실패: {e}")
            logger.error("Firestore client creation failed", exc_info=True)
            raise

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

        # Firestore 클라이언트 취득 — 초기화 실패 시 None 반환
        try:
            db = self._get_db()
        except Exception as e:
            print(f"  ❌ Firestore 연결 실패: {e}")
            return None

        summary_text = analysis.get("summary", "")

        # 슬라이드 제목들로 요약 구성
        titles = analysis.get("titles", [])
        if titles:
            title_summary = " / ".join(titles[:6])
            summary = f"{title} - {title_summary}"
            if len(titles) > 6:
                summary += f" 외 {len(titles) - 6}장"
        else:
            summary = f"{title}에 대해 알기 쉽게 정리한 슬라이드 자료입니다."

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

        # 입력 검증
        if not title:
            print("  ❌ Firestore 등록 실패: 제목이 비어 있습니다")
            return None
        if not pdf_url:
            print("  ❌ Firestore 등록 실패: PDF URL이 비어 있습니다")
            return None

        def _do_add():
            return db.collection('articles').add(doc_data)

        try:
            # 일시적 오류에 대해 재시도
            if _RETRYABLE_GOOGLE_ERRORS:
                result = _retry_sync(_do_add, max_attempts=3, delay=2.0)
            else:
                result = _do_add()

            _, doc_ref = result
            if doc_ref is None:
                print("  ❌ Firestore 등록 실패: add()가 None 반환")
                return None

            doc_id = doc_ref.id
            print(f"  자료실 등록 완료: {doc_id}")
            print(f"  공개: {'예' if visible else '아니오 (관리자 검토 필요)'}")
            return doc_id

        except Exception as e:
            # google.api_core 예외를 구체적으로 분류
            _handle_firestore_error(e)
            return None


def _handle_firestore_error(e: Exception) -> None:
    """Firestore 예외를 구체적인 메시지로 처리"""
    error_type = type(e).__name__
    error_module = type(e).__module__

    # google.api_core.exceptions 계층 감지
    if 'google.api_core' in error_module or 'grpc' in error_module:
        if 'NotFound' in error_type:
            print(f"  ❌ Firestore 오류: 컬렉션/문서를 찾을 수 없습니다 (NotFound). "
                  f"프로젝트 ID '{_get_project_hint()}' 를 확인하세요.")
            logger.error(f"Firestore NotFound: {e}")
        elif 'PermissionDenied' in error_type:
            print(f"  ❌ Firestore 오류: 권한 없음 (PermissionDenied). "
                  f"서비스 계정 권한 또는 Firestore 보안 규칙을 확인하세요.")
            logger.error(f"Firestore PermissionDenied: {e}")
        elif 'DeadlineExceeded' in error_type or 'Timeout' in error_type:
            print(f"  ❌ Firestore 오류: 요청 타임아웃. 네트워크 연결을 확인하세요.")
            logger.error(f"Firestore DeadlineExceeded: {e}")
        elif 'Unauthenticated' in error_type:
            print(f"  ❌ Firestore 오류: 인증 실패. GOOGLE_APPLICATION_CREDENTIALS 를 확인하세요.")
            logger.error(f"Firestore Unauthenticated: {e}")
        elif 'ResourceExhausted' in error_type:
            print(f"  ❌ Firestore 오류: 할당량 초과 (ResourceExhausted). 잠시 후 재시도하세요.")
            logger.error(f"Firestore ResourceExhausted: {e}")
        elif 'ServiceUnavailable' in error_type:
            print(f"  ❌ Firestore 오류: 서비스 일시 중단 (ServiceUnavailable). 잠시 후 재시도하세요.")
            logger.error(f"Firestore ServiceUnavailable: {e}")
        else:
            print(f"  ❌ Firestore API 오류 ({error_type}): {e}")
            logger.error(f"Firestore API error: {e}", exc_info=True)
    else:
        print(f"  ❌ Firestore 등록 실패: {e}")
        logger.error(f"Firestore unexpected error: {e}", exc_info=True)


def _get_project_hint() -> str:
    """현재 Firebase 프로젝트 ID 힌트 반환"""
    try:
        import firebase_admin
        if firebase_admin._apps:
            app = firebase_admin.get_app()
            return app.project_id or "unknown"
    except Exception:
        pass
    return "unknown"
