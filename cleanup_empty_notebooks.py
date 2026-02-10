#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빈 노트북 및 소스 없는 노트북 정리
- 소스가 없는 노트북 삭제
- 제목이 비어있거나 "Untitled"인 노트북 삭제
"""
import asyncio
import sys
from typing import List, Dict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang.browser import NotebookLMBrowser


async def get_notebook_source_count(browser: NotebookLMBrowser, notebook_id: str) -> int:
    """노트북의 소스 개수 확인"""
    await browser.open_notebook(notebook_id)
    await asyncio.sleep(3)

    # 소스 목록 찾기 - 다양한 셀렉터 시도
    source_selectors = [
        '[data-source-id]',
        '.source-item',
        '[class*="source"]',
        '[aria-label*="source"]',
        'li[role="listitem"]',
    ]

    for selector in source_selectors:
        sources = await browser.page.query_selector_all(selector)
        if sources and len(sources) > 0:
            return len(sources)

    # 소스 패널에서 "소스 추가" 버튼만 있는지 확인 (소스 없음)
    add_source_only = await browser.page.query_selector(
        '[aria-label*="소스 추가"], '
        '[aria-label*="Add source"], '
        'button:has-text("소스 추가")'
    )

    # "소스 없음" 텍스트 확인
    no_sources = await browser.page.query_selector(
        ':text("소스 없음"), '
        ':text("No sources"), '
        ':text("소스를 추가하세요")'
    )

    if no_sources:
        return 0

    # 소스 개수 텍스트에서 추출 시도
    source_count_elem = await browser.page.query_selector(
        '[class*="source-count"], '
        ':text-matches("\\d+.*소스"), '
        ':text-matches("\\d+.*source")'
    )

    if source_count_elem:
        text = await source_count_elem.inner_text()
        import re
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))

    return -1  # 알 수 없음


async def cleanup_empty_notebooks(dry_run: bool = True, delete_untitled: bool = True):
    """
    빈 노트북 정리

    Args:
        dry_run: True면 삭제하지 않고 목록만 표시
        delete_untitled: "Untitled" 노트북도 삭제할지
    """
    print("=" * 50)
    print("빈 노트북 정리 시작")
    print(f"모드: {'미리보기 (삭제 안함)' if dry_run else '실제 삭제'}")
    print("=" * 50)

    browser = NotebookLMBrowser()

    try:
        await browser.init()
        print("\n[1] 로그인 중...")
        await browser.login()

        print("\n[2] 노트북 목록 조회 중...")
        notebooks = await browser.list_notebooks()

        if not notebooks:
            print("  노트북이 없습니다.")
            return

        print(f"  총 {len(notebooks)}개 노트북 발견")

        # 삭제 대상 찾기
        to_delete: List[Dict] = []

        print("\n[3] 각 노트북 소스 확인 중...")
        for i, nb in enumerate(notebooks, 1):
            title = nb.get('title', 'Unknown')
            notebook_id = nb.get('id', '')

            print(f"\n  ({i}/{len(notebooks)}) {title[:30]}...")

            # 제목 없거나 Untitled인 경우
            is_untitled = not title or title.strip() == '' or title.lower() in ['untitled', '제목 없음', '무제']

            if is_untitled and delete_untitled:
                to_delete.append({
                    **nb,
                    'reason': '제목 없음',
                    'source_count': '?'
                })
                print(f"    → 삭제 대상 (제목 없음)")
                continue

            # 소스 개수 확인
            source_count = await get_notebook_source_count(browser, notebook_id)

            if source_count == 0:
                to_delete.append({
                    **nb,
                    'reason': '소스 없음',
                    'source_count': 0
                })
                print(f"    → 삭제 대상 (소스 없음)")
            elif source_count == -1:
                print(f"    → 소스 확인 불가")
            else:
                print(f"    → 소스 {source_count}개 있음")

        # 결과 출력
        print("\n" + "=" * 50)
        print(f"삭제 대상: {len(to_delete)}개")
        print("=" * 50)

        if not to_delete:
            print("삭제할 노트북이 없습니다.")
            return

        for nb in to_delete:
            print(f"  - {nb.get('title', 'Unknown')[:40]}")
            print(f"    ID: {nb.get('id', '')[:20]}...")
            print(f"    이유: {nb.get('reason')}")

        if dry_run:
            print("\n[미리보기 모드] 실제 삭제하려면 --execute 옵션을 사용하세요.")
            return

        # 실제 삭제
        print("\n[4] 노트북 삭제 중...")
        deleted = 0
        failed = 0

        for nb in to_delete:
            title = nb.get('title', 'Unknown')
            notebook_id = nb.get('id', '')

            print(f"\n  삭제 중: {title[:30]}...")

            if await browser.delete_notebook(notebook_id):
                print(f"    ✓ 삭제 완료")
                deleted += 1
            else:
                print(f"    ✗ 삭제 실패")
                failed += 1

            await asyncio.sleep(2)

        print("\n" + "=" * 50)
        print(f"완료: {deleted}개 삭제, {failed}개 실패")
        print("=" * 50)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='빈 노트북 및 소스 없는 노트북 정리')
    parser.add_argument('--execute', action='store_true',
                       help='실제로 삭제 (기본: 미리보기만)')
    parser.add_argument('--keep-untitled', action='store_true',
                       help='Untitled 노트북은 유지')

    args = parser.parse_args()

    asyncio.run(cleanup_empty_notebooks(
        dry_run=not args.execute,
        delete_untitled=not args.keep_untitled
    ))


if __name__ == "__main__":
    main()
