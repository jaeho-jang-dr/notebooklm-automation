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
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# noterang 패키지 경로
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .config import WebPublisherConfig
from .pipeline import WebPublishPipeline
from .batch import BatchPublisher


DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")


def find_latest_pdf(directory: Path = DOWNLOAD_DIR) -> Path | None:
    """다운로드 폴더에서 최신 PDF 파일 찾기"""
    if not directory.exists():
        return None
    pdfs = sorted(directory.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pdfs[0] if pdfs else None


def add_common_args(parser: argparse.ArgumentParser):
    """공통 옵션 추가"""
    parser.add_argument(
        "--no-register", action="store_true",
        help="자료실 등록 안 함"
    )
    parser.add_argument(
        "--hidden", action="store_true",
        help="비공개 등록"
    )
    parser.add_argument(
        "--type", default="disease",
        choices=["disease", "guide", "news"],
        help="자료 유형 (기본: disease)"
    )
    parser.add_argument(
        "--slides", "-s", type=int, default=15,
        help="슬라이드 장수 (기본: 15)"
    )


async def cmd_single(args):
    """단일 실행"""
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


async def cmd_batch(args):
    """병렬 배치"""
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


async def cmd_pdf(args):
    """기존 PDF만 등록"""
    pdf_path = None
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


def main():
    parser = argparse.ArgumentParser(
        description="web_publisher: NotebookLM PDF → 웹 자료실 등록"
    )
    subparsers = parser.add_subparsers(dest="command", help="실행 모드")

    # single
    p_single = subparsers.add_parser("single", help="단일 실행")
    p_single.add_argument("--title", "-t", required=True, help="제목")
    p_single.add_argument("--design", "-d", default="인포그래픽", help="디자인 스타일")
    p_single.add_argument("--queries", "-q", help="검색 쿼리 (쉼표 구분)")
    add_common_args(p_single)

    # batch
    p_batch = subparsers.add_parser("batch", help="병렬 배치")
    p_batch.add_argument("--titles", required=True, help="주제들 (쉼표 구분)")
    p_batch.add_argument("--design", "-d", default="인포그래픽", help="디자인 스타일")
    p_batch.add_argument("--max-workers", type=int, default=3, help="최대 동시 실행 수")
    add_common_args(p_batch)

    # pdf
    p_pdf = subparsers.add_parser("pdf", help="기존 PDF만 등록")
    p_pdf.add_argument("--title", "-t", required=True, help="제목")
    p_pdf.add_argument("--pdf", "-p", help="PDF 파일 경로")
    p_pdf.add_argument("--latest", "-l", action="store_true", help="최신 PDF 자동 선택")
    p_pdf.add_argument("--design", "-d", default="인포그래픽", help="디자인 스타일")
    add_common_args(p_pdf)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "single":
        return asyncio.run(cmd_single(args))
    elif args.command == "batch":
        return asyncio.run(cmd_batch(args))
    elif args.command == "pdf":
        return asyncio.run(cmd_pdf(args))

    return 1
