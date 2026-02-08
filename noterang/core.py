#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 핵심 모듈
- 전체 자동화 워크플로우
- 멀티 에이전트 통합
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .config import get_config, NoterangConfig
from .auth import ensure_auth, sync_auth, check_auth
from .notebook import get_or_create_notebook, start_research, check_research_status, import_research, delete_notebook, list_notebooks
from .artifacts import create_slides, check_studio_status, wait_for_completion
from .nlm_client import get_nlm_client, close_nlm_client, NLMClientError
from .download import download_via_browser, download_with_retries
from .convert import pdf_to_pptx, Converter
from .browser import NotebookLMBrowser


@dataclass
class WorkflowResult:
    """워크플로우 결과"""
    success: bool = False
    notebook_id: Optional[str] = None
    notebook_title: Optional[str] = None
    artifact_id: Optional[str] = None
    pdf_path: Optional[Path] = None
    pptx_path: Optional[Path] = None
    slide_count: int = 0
    sources_count: int = 0
    duration_seconds: float = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "notebook_id": self.notebook_id,
            "notebook_title": self.notebook_title,
            "artifact_id": self.artifact_id,
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "pptx_path": str(self.pptx_path) if self.pptx_path else None,
            "slide_count": self.slide_count,
            "sources_count": self.sources_count,
            "duration_seconds": self.duration_seconds,
            "error": self.error
        }


class Noterang:
    """
    노트랑 - NotebookLM 완전 자동화 에이전트

    Usage:
        noterang = Noterang()
        result = await noterang.run(
            title="주제 제목",
            research_queries=["쿼리1", "쿼리2", "쿼리3"],
            focus="핵심 주제"
        )
    """

    def __init__(self, config: NoterangConfig = None):
        self.config = config or get_config()
        self.config.ensure_dirs()

    async def run(
        self,
        title: str,
        research_queries: List[str] = None,
        focus: str = None,
        language: str = None,
        style: str = None,
        skip_research: bool = False,
        skip_download: bool = False,
        skip_convert: bool = False
    ) -> WorkflowResult:
        """
        전체 자동화 실행

        Args:
            title: 노트북 제목
            research_queries: 연구 쿼리 목록
            focus: 슬라이드 집중 주제
            language: 언어 (기본: "ko" 한글)
            style: PPTX 스타일 ("modern", "minimal", "corporate", "creative")
            skip_research: 연구 단계 건너뛰기
            skip_download: 다운로드 단계 건너뛰기
            skip_convert: 변환 단계 건너뛰기

        Returns:
            WorkflowResult
        """
        start_time = time.time()
        result = WorkflowResult(notebook_title=title)
        lang = language or self.config.default_language

        print("=" * 60)
        print(f"노트랑 자동화: {title}")
        print("=" * 60)

        try:
            # Step 1: 인증 확인
            print("\n[1/6] 인증 확인...")
            if not await ensure_auth():
                result.error = "인증 실패"
                print("  ❌ 인증 실패 - 수동 로그인 필요")
                return result
            print("  ✓ 인증 유효")

            # Step 2: 노트북 찾기/생성
            print(f"\n[2/6] 노트북 확인/생성...")
            notebook_id = get_or_create_notebook(title)
            if not notebook_id:
                result.error = "노트북 생성 실패"
                return result
            result.notebook_id = notebook_id
            print(f"  ✓ 노트북 ID: {notebook_id[:8]}...")

            # Step 3: 연구 수집
            total_sources = 0
            if not skip_research and research_queries:
                print(f"\n[3/6] 연구 자료 수집...")
                await self._refresh_auth_if_needed()
                for query in research_queries:
                    count = await self._run_research(notebook_id, query)
                    total_sources += count
                print(f"  총 {total_sources}개 소스 추가")
            else:
                print("\n[3/6] 연구 건너뜀")
            result.sources_count = total_sources

            # Step 4: 슬라이드 생성
            print(f"\n[4/6] 슬라이드 생성...")
            await self._refresh_auth_if_needed()
            artifact_id = await self._create_slides(notebook_id, lang, focus)
            if not artifact_id:
                result.error = "슬라이드 생성 실패"
                # 생성 실패해도 다운로드 시도
            result.artifact_id = artifact_id

            # Step 5: 다운로드 (API → Playwright fallback)
            if not skip_download:
                print(f"\n[5/6] 다운로드...")
                await self._refresh_auth_if_needed()
                pdf_path = await self._download_slides(notebook_id)
                if pdf_path and pdf_path.exists():
                    result.pdf_path = pdf_path
                    print(f"  ✓ PDF: {pdf_path.name}")
                else:
                    result.error = "다운로드 실패"
                    print("  ❌ 다운로드 실패")
            else:
                print("\n[5/6] 다운로드 건너뜀")

            # Step 6: PPTX 변환
            if not skip_convert and result.pdf_path:
                print(f"\n[6/6] PPTX 변환...")
                if style:
                    converter = Converter(self.config.download_dir)
                    pptx_path, slide_count = converter.pdf_to_styled_pptx(
                        result.pdf_path, style=style
                    )
                    print(f"  스타일: {style}")
                else:
                    pptx_path, slide_count = pdf_to_pptx(result.pdf_path)
                if pptx_path:
                    result.pptx_path = pptx_path
                    result.slide_count = slide_count
                    print(f"  ✓ PPTX: {pptx_path.name} ({slide_count}슬라이드)")
            else:
                print("\n[6/6] 변환 건너뜀")

            result.success = result.pptx_path is not None or result.pdf_path is not None

        except Exception as e:
            result.error = str(e)
            print(f"\n❌ 오류 발생: {e}")

        result.duration_seconds = time.time() - start_time

        # 결과 출력
        print("\n" + "=" * 60)
        if result.success:
            print("✓ 완료!")
            if result.pdf_path:
                print(f"  PDF:  {result.pdf_path}")
            if result.pptx_path:
                print(f"  PPTX: {result.pptx_path}")
        else:
            print(f"❌ 실패: {result.error}")
        print(f"  소요시간: {int(result.duration_seconds)}초")
        print("=" * 60)

        return result

    async def _refresh_auth_if_needed(self):
        """NLM 클라이언트 TTL 만료시 재인증"""
        from .nlm_client import is_client_expired
        if is_client_expired():
            print("  인증 갱신 중...")
            await ensure_auth()

    async def _run_research(self, notebook_id: str, query: str) -> int:
        """연구 실행 및 소스 가져오기"""
        print(f"  쿼리: {query}")

        task_id = start_research(notebook_id, query)
        if not task_id:
            return 0

        # 완료 대기 (task_id + query로 정확한 매칭)
        max_wait = self.config.timeout_research
        start = time.time()

        while time.time() - start < max_wait:
            completed, status = check_research_status(notebook_id, task_id=task_id, query=query)
            if completed:
                break
            await asyncio.sleep(5)

        # 소스 가져오기
        count = import_research(notebook_id, task_id)
        print(f"    → {count}개 소스 추가")
        return count

    async def _create_slides(self, notebook_id: str, language: str, focus: str = None) -> Optional[str]:
        """슬라이드 생성 및 완료 대기"""
        artifact_id = create_slides(notebook_id, language, focus)

        if not artifact_id:
            return None

        # 완료 대기
        completed = await wait_for_completion(
            notebook_id,
            timeout=self.config.timeout_slides,
            check_interval=10
        )

        if completed:
            return artifact_id
        return None

    async def _download_slides(self, notebook_id: str) -> Optional[Path]:
        """API로 슬라이드 다운로드 시도, 실패시 Playwright fallback"""
        # Primary: API download
        try:
            client = get_nlm_client()
            target_path = self.config.download_dir / f"{notebook_id[:8]}_slides.pdf"
            downloaded = await client.download_slide_deck(
                notebook_id, str(target_path)
            )
            path = Path(downloaded)
            if path.exists() and path.stat().st_size > 0:
                print(f"  ✓ API 다운로드 성공")
                return path
        except Exception as e:
            print(f"  API 다운로드 실패 ({e}) - Playwright fallback...")

        # Fallback: Playwright browser download
        return await download_with_retries(
            notebook_id,
            self.config.download_dir,
            "slides"
        )

    async def regenerate(
        self,
        notebook_id: str,
        notebook_title: str = None,
        language: str = None,
        focus: str = None
    ) -> WorkflowResult:
        """
        기존 노트북의 슬라이드 재생성

        Args:
            notebook_id: 노트북 ID
            notebook_title: 제목 (파일명용)
            language: 언어
            focus: 집중 주제

        Returns:
            WorkflowResult
        """
        start_time = time.time()
        result = WorkflowResult(
            notebook_id=notebook_id,
            notebook_title=notebook_title or notebook_id[:8]
        )
        lang = language or self.config.default_language

        print("=" * 60)
        print(f"슬라이드 재생성: {result.notebook_title}")
        print("=" * 60)

        try:
            # 인증 확인
            print("\n[1/4] 인증 확인...")
            if not await ensure_auth():
                result.error = "인증 실패"
                return result
            print("  ✓ 인증 유효")

            # 슬라이드 생성
            print(f"\n[2/4] 슬라이드 생성...")
            artifact_id = await self._create_slides(notebook_id, lang, focus)
            result.artifact_id = artifact_id

            # 다운로드 (API → Playwright fallback)
            print(f"\n[3/4] 다운로드...")
            pdf_path = await self._download_slides(notebook_id)
            if pdf_path and pdf_path.exists():
                result.pdf_path = pdf_path
                print(f"  ✓ PDF: {pdf_path.name}")

            # 변환
            if result.pdf_path:
                print(f"\n[4/4] PPTX 변환...")
                pptx_path, slide_count = pdf_to_pptx(result.pdf_path)
                if pptx_path:
                    result.pptx_path = pptx_path
                    result.slide_count = slide_count
                    print(f"  ✓ PPTX: {pptx_path.name} ({slide_count}슬라이드)")

            result.success = result.pptx_path is not None

        except Exception as e:
            result.error = str(e)

        result.duration_seconds = time.time() - start_time
        return result

    def delete(self, notebook_id: str) -> bool:
        """노트북 삭제"""
        return delete_notebook(notebook_id)

    def list(self) -> List[Dict]:
        """노트북 목록"""
        return list_notebooks()

    async def run_browser(
        self,
        title: str,
        sources: List[str] = None,
        focus: str = None,
        language: str = None,
        style: str = None
    ) -> WorkflowResult:
        """
        브라우저 기반 자동화 (CLI 우회)
        nlm CLI 버그 시 사용

        Args:
            title: 노트북 제목
            sources: 소스 URL 목록
            focus: 집중 주제
            language: 언어
            style: PPTX 스타일 ("modern", "minimal", "corporate", "creative")
                   None이면 원본 PDF 이미지 그대로 변환

        Returns:
            WorkflowResult
        """
        start_time = time.time()
        result = WorkflowResult(notebook_title=title)
        lang = language or self.config.default_language

        print("=" * 60)
        print(f"노트랑 브라우저 자동화: {title}")
        print("=" * 60)

        try:
            async with NotebookLMBrowser() as browser:
                # Step 1: 로그인 확인
                print("\n[1/5] 로그인 확인...")
                if not await browser.ensure_logged_in():
                    result.error = "로그인 실패"
                    return result
                print("  ✓ 로그인 완료")

                # Step 2: 노트북 찾기/생성
                print(f"\n[2/5] 노트북 확인...")
                existing = await browser.find_notebook(title)
                if existing:
                    notebook_id = existing['id']
                    print(f"  기존 노트북: {notebook_id[:8]}...")
                else:
                    notebook_id = await browser.create_notebook(title)
                    print(f"  새 노트북 생성: {notebook_id[:8]}..." if notebook_id else "  ❌ 생성 실패")

                if not notebook_id:
                    result.error = "노트북 생성 실패"
                    return result
                result.notebook_id = notebook_id

                # Step 3: 소스 추가
                if sources:
                    print(f"\n[3/5] 소스 추가 (URL)...")
                    for url in sources:
                        await browser.add_source_url(notebook_id, url)
                        result.sources_count += 1
                    print(f"  {result.sources_count}개 소스 추가")
                else:
                    # URL 없으면 웹 검색으로 자료 수집
                    print(f"\n[3/5] 웹 검색으로 자료 수집...")
                    search_query = f"{title} 원인 증상 진단 치료"
                    if await browser.add_source_via_search(search_query):
                        result.sources_count = 1
                    else:
                        print("  ⚠️ 자료 수집 실패 - 슬라이드 생성 시도")

                # Step 4: 슬라이드 생성
                print(f"\n[4/5] 슬라이드 생성...")
                if await browser.create_slides(notebook_id, lang):
                    # 완료 대기
                    if await browser.wait_for_slides(notebook_id):
                        # 다운로드
                        pdf_path = await browser.download_slides(notebook_id)
                        if pdf_path and pdf_path.exists():
                            result.pdf_path = pdf_path
                            print(f"  ✓ PDF: {pdf_path.name}")

                # Step 5: PPTX 변환
                if result.pdf_path:
                    print(f"\n[5/5] PPTX 변환...")
                    if style:
                        # 스타일 템플릿 적용
                        converter = Converter(self.config.download_dir)
                        pptx_path, count = converter.pdf_to_styled_pptx(
                            result.pdf_path, style=style
                        )
                        print(f"  스타일: {style}")
                    else:
                        # 원본 이미지 그대로 변환
                        pptx_path, count = pdf_to_pptx(result.pdf_path)
                    if pptx_path:
                        result.pptx_path = pptx_path
                        result.slide_count = count
                        print(f"  ✓ PPTX: {pptx_path.name} ({count}슬라이드)")

                result.success = result.pptx_path is not None or result.pdf_path is not None

        except Exception as e:
            result.error = str(e)
            print(f"\n❌ 오류: {e}")

        result.duration_seconds = time.time() - start_time

        print("\n" + "=" * 60)
        if result.success:
            print("✓ 완료!")
        else:
            print(f"❌ 실패: {result.error}")
        print("=" * 60)

        return result


async def run_automation(
    title: str,
    research_queries: List[str] = None,
    focus: str = None,
    language: str = "ko"
) -> WorkflowResult:
    """
    간편 자동화 함수

    Usage:
        result = await run_automation(
            title="견관절회전근개 파열",
            research_queries=["원인", "치료", "재활"],
            focus="병인, 치료방법, 재활법"
        )
    """
    noterang = Noterang()
    return await noterang.run(title, research_queries, focus, language)


def run_automation_sync(
    title: str,
    research_queries: List[str] = None,
    focus: str = None,
    language: str = "ko"
) -> WorkflowResult:
    """동기 버전 자동화"""
    return asyncio.run(run_automation(title, research_queries, focus, language))


async def run_batch(
    topics: List[Dict[str, Any]],
    parallel: bool = False
) -> List[WorkflowResult]:
    """
    배치 자동화

    Args:
        topics: [{"title": "...", "queries": [...], "focus": "..."}, ...]
        parallel: 병렬 실행 여부 (노트북 생성만)

    Returns:
        결과 목록
    """
    noterang = Noterang()
    results = []

    if parallel:
        # 노트북 생성은 병렬, 다운로드는 순차
        tasks = [
            noterang.run(
                title=t.get("title", "Untitled"),
                research_queries=t.get("queries", []),
                focus=t.get("focus"),
                language=t.get("language", "ko"),
                skip_download=True,
                skip_convert=True
            )
            for t in topics
        ]
        partial_results = await asyncio.gather(*tasks)

        # 다운로드/변환은 순차
        for i, partial in enumerate(partial_results):
            if partial.notebook_id:
                print(f"\n다운로드 {i+1}/{len(topics)}: {partial.notebook_title}")
                pdf_path = await noterang._download_slides(
                    partial.notebook_id
                )
                if pdf_path and pdf_path.exists():
                    partial.pdf_path = pdf_path
                    pptx_path, count = pdf_to_pptx(pdf_path)
                    if pptx_path:
                        partial.pptx_path = pptx_path
                        partial.slide_count = count
                        partial.success = True

            results.append(partial)
    else:
        for t in topics:
            result = await noterang.run(
                title=t.get("title", "Untitled"),
                research_queries=t.get("queries", []),
                focus=t.get("focus"),
                language=t.get("language", "ko")
            )
            results.append(result)

    return results
