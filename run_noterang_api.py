#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 API 스크립트 - Conductor 통합용

외부에서 호출 가능한 API 인터페이스
결과를 RESULT:{json} 형식으로 출력

Usage:
    python run_noterang_api.py --title "제목" --language ko
    python run_noterang_api.py --title "제목" --queries "쿼리1,쿼리2"
    python run_noterang_api.py --title "제목" --sources "url1,url2"
"""
import argparse
import asyncio
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang import Noterang


async def main():
    parser = argparse.ArgumentParser(description='노트랑 API')
    parser.add_argument('--title', required=True, help='노트북 제목')
    parser.add_argument('--language', default='ko', help='언어 (기본: ko)')
    parser.add_argument('--queries', help='연구 쿼리 (쉼표 구분)')
    parser.add_argument('--sources', help='소스 URL (쉼표 구분)')
    parser.add_argument('--focus', help='집중 주제')
    parser.add_argument('--style', choices=['modern', 'minimal', 'corporate', 'creative'],
                        help='PPTX 스타일 템플릿')
    parser.add_argument('--browser', action='store_true', help='브라우저 모드 사용')

    args = parser.parse_args()

    # 쿼리/소스 파싱
    queries = args.queries.split(',') if args.queries else None
    sources = args.sources.split(',') if args.sources else None

    # 노트랑 실행
    noterang = Noterang()

    try:
        if args.browser or sources:
            # 브라우저 기반 (소스 URL 사용 시)
            result = await noterang.run_browser(
                title=args.title,
                sources=sources,
                focus=args.focus,
                language=args.language,
                style=args.style
            )
        else:
            # CLI 기반 (연구 쿼리 사용 시)
            result = await noterang.run(
                title=args.title,
                research_queries=queries,
                focus=args.focus,
                language=args.language,
                style=args.style
            )

        # 결과 출력 (Conductor가 파싱할 수 있는 형식)
        output = {
            'success': result.success,
            'notebookId': result.notebook_id,
            'pdfPath': str(result.pdf_path) if result.pdf_path else None,
            'pptxPath': str(result.pptx_path) if result.pptx_path else None,
            'slideCount': result.slide_count,
            'error': result.error,
        }

        print(f"RESULT:{json.dumps(output, ensure_ascii=False)}")

        return 0 if result.success else 1

    except Exception as e:
        error_output = {
            'success': False,
            'error': str(e),
        }
        print(f"RESULT:{json.dumps(error_output, ensure_ascii=False)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
