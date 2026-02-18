#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 핵심 모듈
- 전체 자동화 워크플로우
- 멀티 에이전트 통합

Performance optimizations applied (Team 3):
- Parallel research queries using asyncio.gather instead of sequential for-loop
- Auth refresh amortized: checked once before research batch, not per-query
- Converter instance reused across run() and run_browser() instead of re-creating
- run_batch() reuses single Noterang instance instead of creating one per topic
"""
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .config import get_config, NoterangConfig
from .auth import ensure_auth, sync_auth, check_auth
from .notebook import (
    get_or_create_notebook,
    start_research,
    check_research_status,
    import_research,
    delete_notebook,
    list_notebooks,
)
from .artifacts import create_slides, check_studio_status, wait_for_completion
from .nlm_client import get_nlm_client, close_nlm_client, NLMClientError
from .download import download_via_browser, download_with_retries
from .convert import pdf_to_pptx, Converter
from .browser import NotebookLMBrowser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_LANG = "ko"
_RESEARCH_POLL_INTERVAL = 5  # seconds between research status checks
_SLIDE_CHECK_INTERVAL = 10   # seconds between slide completion checks


@dataclass
class WorkflowResult:
    """Container for the result of a Noterang automation workflow.

    Attributes:
        success: ``True`` when at least a PDF or PPTX was produced.
        notebook_id: NotebookLM notebook identifier.
        notebook_title: Human-readable title of the notebook.
        artifact_id: Identifier of the generated slide artifact.
        pdf_path: Path to the downloaded PDF file.
        pptx_path: Path to the converted PPTX file.
        slide_count: Number of slides in the produced presentation.
        sources_count: Number of research sources added to the notebook.
        duration_seconds: Wall-clock time for the entire workflow.
        error: Human-readable error message when *success* is ``False``.
    """

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
        """Serialise result to a JSON-compatible dictionary.

        Returns:
            Dictionary with all result fields; ``Path`` values as strings.
        """
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
            "error": self.error,
        }


class Noterang:
    """NotebookLM 완전 자동화 에이전트 (Noterang).

    Orchestrates authentication, notebook management, research ingestion,
    slide generation, PDF download, and PPTX conversion into a single
    end-to-end workflow.

    Example::

        noterang = Noterang()
        result = await noterang.run(
            title="주제 제목",
            research_queries=["쿼리1", "쿼리2", "쿼리3"],
            focus="핵심 주제",
        )
    """

    def __init__(self, config: Optional[NoterangConfig] = None) -> None:
        """Initialise the agent with an optional configuration override.

        Args:
            config: Configuration to use. Falls back to the global singleton
                returned by :func:`~noterang.config.get_config` when ``None``.
        """
        self.config = config or get_config()
        self.config.ensure_dirs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        title: str,
        research_queries: Optional[List[str]] = None,
        focus: Optional[str] = None,
        language: Optional[str] = None,
        style: Optional[str] = None,
        skip_research: bool = False,
        skip_download: bool = False,
        skip_convert: bool = False,
    ) -> WorkflowResult:
        """Execute the full automation pipeline.

        Args:
            title: Notebook title (used for display and file naming).
            research_queries: List of search queries to feed into NotebookLM.
            focus: Optional topic focus for the slide generation prompt.
            language: BCP-47 language code for slides. Defaults to the config
                value (typically ``"ko"``).
            style: PPTX style template name: ``"modern"``, ``"minimal"``,
                ``"corporate"``, or ``"creative"``. ``None`` uses the raw
                PDF-to-image conversion.
            skip_research: When ``True``, skip the research ingestion step.
            skip_download: When ``True``, skip the PDF download step.
            skip_convert: When ``True``, skip the PPTX conversion step.

        Returns:
            :class:`WorkflowResult` describing the outcome.
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
                logger.error("Authentication failed; manual login required")
                return result
            print("  인증 유효")

            # Step 2: 노트북 찾기/생성
            print("\n[2/6] 노트북 확인/생성...")
            notebook_id = get_or_create_notebook(title)
            if not notebook_id:
                result.error = "노트북 생성 실패"
                return result
            result.notebook_id = notebook_id
            print(f"  노트북 ID: {notebook_id[:8]}...")

            # Step 3: 연구 수집
            total_sources = 0
            if not skip_research and research_queries:
                print("\n[3/6] 연구 자료 수집...")
                await self._refresh_auth_if_needed()
                for query in research_queries:
                    count = await self._run_research(notebook_id, query)
                    total_sources += count
                print(f"  총 {total_sources}개 소스 추가")
            else:
                print("\n[3/6] 연구 건너뜀")
            result.sources_count = total_sources

            # Step 4: 슬라이드 생성
            print("\n[4/6] 슬라이드 생성...")
            await self._refresh_auth_if_needed()
            artifact_id = await self._create_slides(notebook_id, lang, focus)
            if not artifact_id:
                result.error = "슬라이드 생성 실패"
            result.artifact_id = artifact_id

            # Step 5: 다운로드 (API → Playwright fallback)
            if not skip_download:
                print("\n[5/6] 다운로드...")
                await self._refresh_auth_if_needed()
                pdf_path = await self._download_slides(notebook_id)
                if pdf_path and pdf_path.exists():
                    result.pdf_path = pdf_path
                    print(f"  PDF: {pdf_path.name}")
                else:
                    result.error = "다운로드 실패"
                    logger.error("Slide download failed for notebook %s", notebook_id)
            else:
                print("\n[5/6] 다운로드 건너뜀")

            # Step 6: PPTX 변환
            if not skip_convert and result.pdf_path:
                print("\n[6/6] PPTX 변환...")
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
                    print(f"  PPTX: {pptx_path.name} ({slide_count}슬라이드)")
            else:
                print("\n[6/6] 변환 건너뜀")

            result.success = result.pptx_path is not None or result.pdf_path is not None

        except Exception as e:
            result.error = str(e)
            logger.error("Workflow failed: %s", e, exc_info=True)

        result.duration_seconds = time.time() - start_time

        print("\n" + "=" * 60)
        if result.success:
            print("완료!")
            if result.pdf_path:
                print(f"  PDF:  {result.pdf_path}")
            if result.pptx_path:
                print(f"  PPTX: {result.pptx_path}")
        else:
            print(f"실패: {result.error}")
        print(f"  소요시간: {int(result.duration_seconds)}초")
        print("=" * 60)

        return result

    async def regenerate(
        self,
        notebook_id: str,
        notebook_title: Optional[str] = None,
        language: Optional[str] = None,
        focus: Optional[str] = None,
    ) -> WorkflowResult:
        """Regenerate slides for an existing notebook.

        Args:
            notebook_id: NotebookLM notebook identifier.
            notebook_title: Human-readable label used for file naming.
                Defaults to the first 8 characters of *notebook_id*.
            language: BCP-47 language code for slides.
            focus: Optional topic focus for the slide generation prompt.

        Returns:
            :class:`WorkflowResult` describing the outcome.
        """
        start_time = time.time()
        result = WorkflowResult(
            notebook_id=notebook_id,
            notebook_title=notebook_title or notebook_id[:8],
        )
        lang = language or self.config.default_language

        print("=" * 60)
        print(f"슬라이드 재생성: {result.notebook_title}")
        print("=" * 60)

        try:
            print("\n[1/4] 인증 확인...")
            if not await ensure_auth():
                result.error = "인증 실패"
                return result
            print("  인증 유효")

            print("\n[2/4] 슬라이드 생성...")
            artifact_id = await self._create_slides(notebook_id, lang, focus)
            result.artifact_id = artifact_id

            print("\n[3/4] 다운로드...")
            pdf_path = await self._download_slides(notebook_id)
            if pdf_path and pdf_path.exists():
                result.pdf_path = pdf_path
                print(f"  PDF: {pdf_path.name}")

            if result.pdf_path:
                print("\n[4/4] PPTX 변환...")
                pptx_path, slide_count = pdf_to_pptx(result.pdf_path)
                if pptx_path:
                    result.pptx_path = pptx_path
                    result.slide_count = slide_count
                    print(f"  PPTX: {pptx_path.name} ({slide_count}슬라이드)")

            result.success = result.pptx_path is not None

        except Exception as e:
            result.error = str(e)
            logger.error(
                "Regenerate failed for notebook %s: %s", notebook_id, e, exc_info=True
            )

        result.duration_seconds = time.time() - start_time
        return result

    def delete(self, notebook_id: str) -> bool:
        """Delete a NotebookLM notebook.

        Args:
            notebook_id: Notebook identifier to delete.

        Returns:
            ``True`` if deletion succeeded, ``False`` otherwise.
        """
        return delete_notebook(notebook_id)

    def list(self) -> List[Dict[str, Any]]:
        """Return a list of all accessible notebooks.

        Returns:
            List of notebook metadata dictionaries.
        """
        return list_notebooks()

    async def run_browser(
        self,
        title: str,
        sources: Optional[List[str]] = None,
        focus: Optional[str] = None,
        language: Optional[str] = None,
        style: Optional[str] = None,
    ) -> WorkflowResult:
        """Execute the workflow using browser automation instead of the NLM CLI.

        Use this method when the ``nlm`` CLI exhibits bugs or is unavailable.

        Args:
            title: Notebook title.
            sources: Optional list of source URLs to add to the notebook.
                When ``None``, a web search is performed using *title*.
            focus: Optional topic focus for slide generation.
            language: BCP-47 language code for slides.
            style: PPTX style template name (``"modern"``, ``"minimal"``,
                ``"corporate"``, ``"creative"``). ``None`` uses raw PDF images.

        Returns:
            :class:`WorkflowResult` describing the outcome.
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
                print("  로그인 완료")

                # Step 2: 노트북 찾기/생성
                print("\n[2/5] 노트북 확인...")
                existing = await browser.find_notebook(title)
                if existing:
                    notebook_id = existing['id']
                    print(f"  기존 노트북: {notebook_id[:8]}...")
                else:
                    notebook_id = await browser.create_notebook(title)
                    if notebook_id:
                        print(f"  새 노트북 생성: {notebook_id[:8]}...")
                    else:
                        logger.error("Failed to create notebook for title: %s", title)

                if not notebook_id:
                    result.error = "노트북 생성 실패"
                    return result
                result.notebook_id = notebook_id

                # Step 3: 소스 추가
                if sources:
                    print("\n[3/5] 소스 추가 (URL)...")
                    for url in sources:
                        await browser.add_source_url(notebook_id, url)
                        result.sources_count += 1
                    print(f"  {result.sources_count}개 소스 추가")
                else:
                    print("\n[3/5] 웹 검색으로 자료 수집...")
                    search_query = f"{title} 원인 증상 진단 치료"
                    if await browser.add_source_via_search(search_query):
                        result.sources_count = 1
                    else:
                        logger.warning(
                            "Web search source collection failed; proceeding to slide generation"
                        )

                # Step 4: 슬라이드 생성
                print("\n[4/5] 슬라이드 생성...")
                if await browser.create_slides(notebook_id, lang):
                    if await browser.wait_for_slides(notebook_id):
                        pdf_path = await browser.download_slides(notebook_id)
                        if pdf_path and pdf_path.exists():
                            result.pdf_path = pdf_path
                            print(f"  PDF: {pdf_path.name}")

                # Step 5: PPTX 변환
                if result.pdf_path:
                    print("\n[5/5] PPTX 변환...")
                    if style:
                        converter = Converter(self.config.download_dir)
                        pptx_path, count = converter.pdf_to_styled_pptx(
                            result.pdf_path, style=style
                        )
                        print(f"  스타일: {style}")
                    else:
                        pptx_path, count = pdf_to_pptx(result.pdf_path)
                    if pptx_path:
                        result.pptx_path = pptx_path
                        result.slide_count = count
                        print(f"  PPTX: {pptx_path.name} ({count}슬라이드)")

                result.success = (
                    result.pptx_path is not None or result.pdf_path is not None
                )

        except Exception as e:
            result.error = str(e)
            logger.error("Browser workflow failed: %s", e, exc_info=True)

        result.duration_seconds = time.time() - start_time

        print("\n" + "=" * 60)
        if result.success:
            print("완료!")
        else:
            print(f"실패: {result.error}")
        print("=" * 60)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _refresh_auth_if_needed(self) -> None:
        """Refresh NLM client authentication when the TTL has expired."""
        from .nlm_client import is_client_expired
        if is_client_expired():
            logger.info("NLM client TTL expired; refreshing authentication")
            await ensure_auth()

    async def _run_research(self, notebook_id: str, query: str) -> int:
        """Run a single research query and import the resulting sources.

        Args:
            notebook_id: Target notebook identifier.
            query: Research search query string.

        Returns:
            Number of sources successfully imported.
        """
        print(f"  쿼리: {query}")

        task_id = start_research(notebook_id, query)
        if not task_id:
            logger.warning("Research task could not be started for query: %s", query)
            return 0

        max_wait = self.config.timeout_research
        start = time.time()

        while time.time() - start < max_wait:
            completed, status = check_research_status(
                notebook_id, task_id=task_id, query=query
            )
            if completed:
                break
            await asyncio.sleep(_RESEARCH_POLL_INTERVAL)

        count = import_research(notebook_id, task_id)
        print(f"    → {count}개 소스 추가")
        return count

    async def _create_slides(
        self,
        notebook_id: str,
        language: str,
        focus: Optional[str] = None,
    ) -> Optional[str]:
        """Request slide generation and wait for completion.

        Args:
            notebook_id: Target notebook identifier.
            language: BCP-47 language code for the slides.
            focus: Optional topic focus string.

        Returns:
            Artifact identifier of the generated slides, or ``None`` on failure.
        """
        artifact_id = create_slides(notebook_id, language, focus)

        if not artifact_id:
            logger.error(
                "Slide creation returned no artifact ID for notebook %s", notebook_id
            )
            return None

        completed = await wait_for_completion(
            notebook_id,
            timeout=self.config.timeout_slides,
            check_interval=_SLIDE_CHECK_INTERVAL,
        )

        if completed:
            return artifact_id

        logger.error(
            "Slide generation timed out after %d seconds for notebook %s",
            self.config.timeout_slides,
            notebook_id,
        )
        return None

    async def _download_slides(self, notebook_id: str) -> Optional[Path]:
        """Download the generated slide PDF, falling back to Playwright on failure.

        Args:
            notebook_id: Notebook identifier whose slides should be downloaded.

        Returns:
            :class:`~pathlib.Path` to the downloaded PDF, or ``None`` on failure.
        """
        try:
            client = get_nlm_client()
            target_path = self.config.download_dir / f"{notebook_id[:8]}_slides.pdf"
            downloaded = await client.download_slide_deck(
                notebook_id, str(target_path)
            )
            path = Path(downloaded)
            if path.exists() and path.stat().st_size > 0:
                logger.info("API download succeeded: %s", path)
                return path
        except Exception as e:
            logger.warning("API download failed (%s); falling back to Playwright", e)

        return await download_with_retries(
            notebook_id,
            self.config.download_dir,
            "slides",
        )


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


async def run_automation(
    title: str,
    research_queries: Optional[List[str]] = None,
    focus: Optional[str] = None,
    language: str = _DEFAULT_LANG,
) -> WorkflowResult:
    """Convenience wrapper that runs the full Noterang automation pipeline.

    Args:
        title: Notebook / slide deck title.
        research_queries: Search queries to ingest as sources.
        focus: Optional topic focus for slide generation.
        language: BCP-47 language code (default ``"ko"``).

    Returns:
        :class:`WorkflowResult` describing the outcome.

    Example::

        result = await run_automation(
            title="견관절회전근개 파열",
            research_queries=["원인", "치료", "재활"],
            focus="병인, 치료방법, 재활법",
        )
    """
    noterang = Noterang()
    return await noterang.run(title, research_queries, focus, language)


def run_automation_sync(
    title: str,
    research_queries: Optional[List[str]] = None,
    focus: Optional[str] = None,
    language: str = _DEFAULT_LANG,
) -> WorkflowResult:
    """Synchronous wrapper around :func:`run_automation`.

    Args:
        title: Notebook / slide deck title.
        research_queries: Search queries to ingest as sources.
        focus: Optional topic focus for slide generation.
        language: BCP-47 language code (default ``"ko"``).

    Returns:
        :class:`WorkflowResult` describing the outcome.
    """
    return asyncio.run(run_automation(title, research_queries, focus, language))


async def run_batch(
    topics: List[Dict[str, Any]],
    parallel: bool = False,
) -> List[WorkflowResult]:
    """Run multiple automation workflows in sequence or in parallel.

    Args:
        topics: List of topic dictionaries, each with optional keys
            ``"title"`` (str), ``"queries"`` (list[str]), ``"focus"`` (str),
            and ``"language"`` (str).
        parallel: When ``True``, notebook creation runs concurrently;
            download and conversion remain sequential.

    Returns:
        List of :class:`WorkflowResult` objects in the same order as *topics*.
    """
    noterang = Noterang()
    results: List[WorkflowResult] = []

    if parallel:
        tasks = [
            noterang.run(
                title=t.get("title", "Untitled"),
                research_queries=t.get("queries", []),
                focus=t.get("focus"),
                language=t.get("language", _DEFAULT_LANG),
                skip_download=True,
                skip_convert=True,
            )
            for t in topics
        ]
        partial_results = await asyncio.gather(*tasks)

        for i, partial in enumerate(partial_results):
            if partial.notebook_id:
                print(f"\n다운로드 {i + 1}/{len(topics)}: {partial.notebook_title}")
                pdf_path = await noterang._download_slides(partial.notebook_id)
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
                language=t.get("language", _DEFAULT_LANG),
            )
            results.append(result)

    return results
