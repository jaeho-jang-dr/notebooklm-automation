#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_publisher CLI - 통합 커맨드라인 인터페이스

Usage:
    python -m apps.web_publisher single --title "아킬레스건염" --design "미니멀 젠"
    python -m apps.web_publisher batch --titles "골다공증,측만증,거북목" --max-workers 3
    python -m apps.web_publisher pdf --pdf "경로.pdf" --title "오십견"
    python -m apps.web_publisher pdf --latest --title "족저근막염"
"""
import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# noterang 패키지 경로
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .config import WebPublisherConfig
from .pipeline import WebPublishPipeline
from .batch import BatchPublisher

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")
DEFAULT_MAX_WORKERS = 3
DEFAULT_DESIGN = "인포그래픽"
DEFAULT_ARTICLE_TYPE = "disease"
DEFAULT_SLIDE_COUNT = 15


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def find_latest_pdf(directory: Path = DOWNLOAD_DIR) -> Optional[Path]:
    """Return the most recently modified PDF in *directory*.

    Args:
        directory: Directory to search. Defaults to :data:`DOWNLOAD_DIR`.

    Returns:
        Path to the most recently modified PDF, or ``None`` when the directory
        does not exist or contains no PDF files.
    """
    if not directory.exists():
        logger.warning("Download directory does not exist: %s", directory)
        return None
    pdfs = sorted(directory.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pdfs[0] if pdfs else None


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add shared CLI arguments to *parser*.

    Adds ``--no-register``, ``--hidden``, ``--type``, and ``--slides``.

    Args:
        parser: The :class:`~argparse.ArgumentParser` to extend.
    """
    parser.add_argument(
        "--no-register", action="store_true",
        help="자료실 등록 안 함",
    )
    parser.add_argument(
        "--hidden", action="store_true",
        help="비공개 등록",
    )
    parser.add_argument(
        "--type", default=DEFAULT_ARTICLE_TYPE,
        choices=["disease", "guide", "news"],
        help=f"자료 유형 (기본: {DEFAULT_ARTICLE_TYPE})",
    )
    parser.add_argument(
        "--slides", "-s", type=int, default=DEFAULT_SLIDE_COUNT,
        help=f"슬라이드 장수 (기본: {DEFAULT_SLIDE_COUNT})",
    )


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


async def cmd_single(args: argparse.Namespace) -> int:
    """Run a single full-pipeline publication.

    Args:
        args: Parsed CLI arguments with ``title``, ``queries``, ``no_register``,
            ``hidden``, ``type``, ``design``, and ``slides`` attributes.

    Returns:
        Exit code: ``0`` on success, ``1`` on failure.
    """
    queries = args.queries.split(",") if args.queries else None

    pipeline = WebPublishPipeline(
        title=args.title,
        queries=queries,
        register=not args.no_register,
        visible=not args.hidden,
        article_type=args.type,
        design=args.design,
        slide_count=args.slides,
    )

    result = await pipeline.run()
    print(f"\nRESULT:{json.dumps(result, ensure_ascii=False)}")
    return 0 if result.get("success") else 1


async def cmd_batch(args: argparse.Namespace) -> int:
    """Run a batch of publications in parallel.

    Args:
        args: Parsed CLI arguments with ``titles``, ``design``,
            ``max_workers``, ``no_register``, ``hidden``, ``type``,
            and ``slides`` attributes.

    Returns:
        Exit code: ``0`` when all titles succeeded, ``1`` otherwise.
    """
    titles = [t.strip() for t in args.titles.split(",") if t.strip()]
    if not titles:
        print("오류: --titles에 최소 1개 주제를 입력하세요.")
        return 1

    batch = BatchPublisher(
        titles=titles,
        design=args.design,
        max_workers=args.max_workers,
        register=not args.no_register,
        visible=not args.hidden,
        article_type=args.type,
        slide_count=args.slides,
    )

    results = await batch.run()
    success_count = sum(1 for r in results if r.get("success"))
    print(f"\nRESULT:{json.dumps(results, ensure_ascii=False)}")
    return 0 if success_count == len(titles) else 1


async def cmd_pdf(args: argparse.Namespace) -> int:
    """Register an existing PDF in the web archive.

    Args:
        args: Parsed CLI arguments with ``pdf``, ``latest``, ``title``,
            ``no_register``, ``hidden``, ``type``, and ``design`` attributes.

    Returns:
        Exit code: ``0`` on success, ``1`` on failure.
    """
    pdf_path: Optional[str] = None

    if args.pdf:
        pdf_path = args.pdf
    elif args.latest:
        latest = find_latest_pdf()
        if not latest:
            print(f"오류: {DOWNLOAD_DIR}에서 PDF를 찾을 수 없습니다.")
            return 1
        pdf_path = str(latest)
        print(f"최신 PDF 선택: {pdf_path}")
    else:
        print("오류: --pdf 또는 --latest 중 하나를 지정하세요.")
        return 1

    pipeline = WebPublishPipeline(
        title=args.title,
        pdf_path=pdf_path,
        register=not args.no_register,
        visible=not args.hidden,
        article_type=args.type,
        design=args.design,
    )

    result = await pipeline.run()
    print(f"\nRESULT:{json.dumps(result, ensure_ascii=False)}")
    return 0 if result.get("success") else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point for the web_publisher CLI.

    Returns:
        Exit code: ``0`` on success, ``1`` on failure or missing command.
    """
    parser = argparse.ArgumentParser(
        description="web_publisher: NotebookLM PDF → 웹 자료실 등록"
    )
    subparsers = parser.add_subparsers(dest="command", help="실행 모드")

    # single
    p_single = subparsers.add_parser("single", help="단일 실행")
    p_single.add_argument("--title", "-t", required=True, help="제목")
    p_single.add_argument(
        "--design", "-d", default=DEFAULT_DESIGN, help="디자인 스타일"
    )
    p_single.add_argument("--queries", "-q", help="검색 쿼리 (쉼표 구분)")
    add_common_args(p_single)

    # batch
    p_batch = subparsers.add_parser("batch", help="병렬 배치")
    p_batch.add_argument("--titles", required=True, help="주제들 (쉼표 구분)")
    p_batch.add_argument(
        "--design", "-d", default=DEFAULT_DESIGN, help="디자인 스타일"
    )
    p_batch.add_argument(
        "--max-workers", type=int, default=DEFAULT_MAX_WORKERS,
        help=f"최대 동시 실행 수 (기본: {DEFAULT_MAX_WORKERS})",
    )
    add_common_args(p_batch)

    # pdf
    p_pdf = subparsers.add_parser("pdf", help="기존 PDF만 등록")
    p_pdf.add_argument("--title", "-t", required=True, help="제목")
    p_pdf.add_argument("--pdf", "-p", help="PDF 파일 경로")
    p_pdf.add_argument("--latest", "-l", action="store_true", help="최신 PDF 자동 선택")
    p_pdf.add_argument(
        "--design", "-d", default=DEFAULT_DESIGN, help="디자인 스타일"
    )
    add_common_args(p_pdf)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "single":
        return asyncio.run(cmd_single(args))
    if args.command == "batch":
        return asyncio.run(cmd_batch(args))
    if args.command == "pdf":
        return asyncio.run(cmd_pdf(args))

    return 1
