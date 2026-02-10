#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 (Noterang) v2.0 - NotebookLM 완전 자동화

워크플로우:
1. 자동 로그인
2. 노트북 찾기/생성
3. 연구 자료 수집 또는 URL 소스 추가
4. 슬라이드 생성 (한글)
5. PDF 다운로드
6. PPTX 변환

Usage:
    python run_noterang.py

또는 CLI:
    python -m noterang run "제목" --queries "쿼리1,쿼리2"
"""
import asyncio
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang import Noterang


async def main():
    """메인 실행"""

    # 노트랑 인스턴스 생성
    noterang = Noterang()

    # ========================================
    # 방법 1: CLI 기반 자동화 (nlm 도구 사용)
    # ========================================
    # result = await noterang.run(
    #     title="견관절회전근개 파열",
    #     research_queries=[
    #         "회전근개 파열 원인 병인",
    #         "회전근개 파열 수술 치료",
    #         "회전근개 파열 재활 운동",
    #     ],
    #     focus="병인, 치료방법, 재활법",
    #     language="ko"  # 반드시 한글!
    # )

    # ========================================
    # 방법 2: 브라우저 기반 자동화 (Playwright 직접 제어)
    # nlm CLI 버그 시 사용
    # ========================================
    result = await noterang.run_browser(
        title="테스트 노트북",
        sources=[
            # URL 소스 목록 (선택 사항)
            # "https://example.com/article1",
            # "https://example.com/article2",
        ],
        focus=None,
        language="ko"  # 반드시 한글!
    )

    # 결과 출력
    if result.success:
        print("\n" + "=" * 60)
        print("성공!")
        if result.pdf_path:
            print(f"  PDF:  {result.pdf_path}")
        if result.pptx_path:
            print(f"  PPTX: {result.pptx_path}")
        print(f"  슬라이드: {result.slide_count}장")
        print("=" * 60)
    else:
        print(f"\n실패: {result.error}")

    return result


async def batch_example():
    """배치 실행 예시"""
    from noterang import run_batch

    topics = [
        {
            "title": "족관절 염좌",
            "queries": ["염좌 원인", "염좌 치료", "염좌 재활"],
            "focus": "원인, 치료, 재활"
        },
        {
            "title": "족관절 골절",
            "queries": ["골절 원인", "골절 수술", "골절 재활"],
            "focus": "원인, 수술, 재활"
        },
    ]

    results = await run_batch(topics, parallel=True)

    print("\n배치 결과:")
    for r in results:
        status = "✓" if r.success else "❌"
        print(f"  {status} {r.notebook_title}: {r.slide_count}슬라이드")


async def interactive_mode():
    """대화형 모드"""
    print("=" * 60)
    print("노트랑 (Noterang) - NotebookLM 자동화")
    print("=" * 60)

    noterang = Noterang()

    while True:
        print("\n명령:")
        print("  1. 새 노트북 생성 + 슬라이드")
        print("  2. 기존 노트북 슬라이드 재생성")
        print("  3. 노트북 목록")
        print("  4. 종료")

        choice = input("\n선택: ").strip()

        if choice == "1":
            title = input("노트북 제목: ").strip()
            if not title:
                continue

            result = await noterang.run_browser(
                title=title,
                language="ko"
            )

            if result.success:
                print(f"\n✓ 완료: {result.pptx_path}")
            else:
                print(f"\n❌ 실패: {result.error}")

        elif choice == "2":
            notebook_id = input("노트북 ID: ").strip()
            title = input("제목 (파일명용): ").strip() or notebook_id[:8]

            result = await noterang.regenerate(
                notebook_id=notebook_id,
                notebook_title=title,
                language="ko"
            )

            if result.success:
                print(f"\n✓ 완료: {result.pptx_path}")
            else:
                print(f"\n❌ 실패: {result.error}")

        elif choice == "3":
            from noterang import NotebookLMBrowser
            async with NotebookLMBrowser() as browser:
                await browser.ensure_logged_in()
                notebooks = await browser.list_notebooks()
                print(f"\n노트북 ({len(notebooks)}개):")
                for nb in notebooks:
                    print(f"  - {nb.get('title')} ({nb.get('id')[:12]}...)")

        elif choice == "4":
            break


if __name__ == "__main__":
    # 단일 실행
    asyncio.run(main())

    # 대화형 모드
    # asyncio.run(interactive_mode())

    # 배치 실행
    # asyncio.run(batch_example())
