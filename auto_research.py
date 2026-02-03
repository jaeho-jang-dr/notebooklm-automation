#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 완전 자동화 v3 - Fast Research로 소스 추가 및 슬라이드 생성
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

NOTEBOOK_ID = "9204bd03-cddb-4866-8f7d-bcffcf7aff97"
NOTEBOOK_TITLE = "견관절회전근개 파열"
DOWNLOAD_DIR = Path("D:/Entertainments/DevEnvironment/notebooklm")
SCREENSHOT_DIR = Path("D:/Entertainments/DevEnvironment/notebooklm-automation/CCimages/screenshots")

# 한글 연구 쿼리
RESEARCH_QUERIES = [
    "회전근개 파열 원인 병인",
    "회전근개 파열 수술 치료",
    "회전근개 파열 재활 운동",
]

SLIDE_INSTRUCTION = "모든 내용을 한글로 작성해주세요. 병인, 치료방법, 재활법 순서로 구성해주세요."

async def screenshot(page, name):
    """스크린샷 저장"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}_{datetime.now().strftime('%H%M%S')}.png"
    await page.screenshot(path=str(path))
    print(f"    [스크린샷] {path.name}")
    return path

async def find_element(page, selectors, timeout=3000):
    """여러 셀렉터로 요소 찾기"""
    for selector in selectors:
        try:
            elem = await page.wait_for_selector(selector, timeout=timeout)
            if elem:
                return elem
        except:
            continue
    return None

async def safe_click(page, element, description=""):
    """안전한 클릭"""
    try:
        await element.click(timeout=5000)
        print(f"  ✓ {description}")
        return True
    except:
        try:
            await element.click(force=True, timeout=5000)
            print(f"  ✓ {description} (force)")
            return True
        except:
            print(f"  ⚠️ {description} 실패")
            return False

async def add_source_via_search(page, query):
    """검색창을 통해 소스 추가"""
    print(f"\n  검색: {query}")

    # 왼쪽 패널의 검색창 찾기
    search_input = await find_element(page, [
        'input[placeholder*="웹에서"]',
        'input[placeholder*="검색"]',
        'input[placeholder*="search"]',
        '.source-search input',
        '[aria-label*="검색"] input',
    ])

    if search_input:
        await search_input.click()
        await asyncio.sleep(0.5)
        await search_input.fill(query)
        print(f"    쿼리 입력 완료")
        await asyncio.sleep(1)

        # 파란색 화살표 버튼 (→) 클릭
        arrow_btn = await find_element(page, [
            'button[aria-label*="검색"]',
            'button[aria-label*="search"]',
            'button[type="submit"]',
            '.search-button',
            'button:has(svg)',  # 화살표 아이콘이 있는 버튼
        ])

        if arrow_btn:
            await safe_click(page, arrow_btn, "검색 실행")
        else:
            # Enter 키로 검색
            await search_input.press('Enter')
            print(f"    Enter 키로 검색")

        await asyncio.sleep(5)

        # 검색 결과에서 항목 선택
        # 체크박스 찾기
        await asyncio.sleep(3)
        checkboxes = await page.query_selector_all('input[type="checkbox"]:not([disabled])')

        if checkboxes:
            selected = 0
            for cb in checkboxes[:3]:  # 최대 3개
                try:
                    await cb.click()
                    selected += 1
                    await asyncio.sleep(0.5)
                except:
                    continue
            print(f"    {selected}개 항목 선택")

            # 삽입/추가 버튼 찾기
            add_btn = await find_element(page, [
                'button:has-text("삽입")',
                'button:has-text("추가")',
                'button:has-text("Insert")',
                'button:has-text("Add")',
            ])

            if add_btn:
                await safe_click(page, add_btn, "소스 추가")
                await asyncio.sleep(5)
                return True
        else:
            print(f"    검색 결과 없음")

    return False

async def wait_for_sources(page, min_count=1, timeout=30):
    """소스가 추가될 때까지 대기"""
    for i in range(timeout // 2):
        # 소스 개수 확인
        source_count = await page.query_selector('text=/소스 \\d+개/')
        if source_count:
            text = await source_count.text_content()
            if text:
                import re
                match = re.search(r'(\d+)', text)
                if match and int(match.group(1)) >= min_count:
                    print(f"  ✓ 소스 {match.group(1)}개 확인")
                    return True
        await asyncio.sleep(2)
    return False

async def main():
    from playwright.async_api import async_playwright

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    auth_dir = Path.home() / ".notebooklm-mcp-cli"
    user_data_dir = auth_dir / "browser_profile"

    print("="*60)
    print(f"[자동화 v3] {NOTEBOOK_TITLE}")
    print("="*60)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            downloads_path=str(DOWNLOAD_DIR),
            accept_downloads=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--start-maximized',
            ],
            ignore_default_args=['--enable-automation'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # 1. 노트북 열기
        print("\n[1/5] 노트북 열기...")
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"
        try:
            await page.goto(notebook_url, wait_until='domcontentloaded', timeout=30000)
        except:
            pass
        await asyncio.sleep(5)

        # 로그인 확인
        if 'accounts.google' in page.url:
            print("  ⚠️ 로그인 필요 - 대기 중...")
            for i in range(24):
                await asyncio.sleep(5)
                if 'accounts.google' not in page.url:
                    break

        await screenshot(page, "01_loaded")
        print("  ✓ 노트북 로드 완료")

        # 2. Fast Research로 소스 추가
        print("\n[2/5] 연구 자료 검색 및 추가...")

        for query in RESEARCH_QUERIES:
            await add_source_via_search(page, query)
            await asyncio.sleep(2)
            # ESC로 모달 닫기
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

        await screenshot(page, "02_sources_added")

        # 소스 확인
        await wait_for_sources(page, min_count=1, timeout=20)

        # 3. 슬라이드 생성
        print("\n[3/5] 슬라이드 생성...")

        # ESC로 모달 닫기
        await page.keyboard.press('Escape')
        await asyncio.sleep(2)

        await screenshot(page, "03_before_slides")

        # 스튜디오 패널에서 슬라이드 자료 클릭
        slide_btn = await find_element(page, [
            'text="슬라이드 자료"',
            'button:has-text("슬라이드")',
            'div:has-text("슬라이드 자료"):not(:has(div))',
            '[aria-label*="슬라이드"]',
            'text="Slide deck"',
        ])

        if slide_btn:
            await safe_click(page, slide_btn, "슬라이드 자료 선택")
            await asyncio.sleep(3)
            await screenshot(page, "04_slide_modal")

            # 커스텀 지시사항 입력
            textarea = await find_element(page, ['textarea'])
            if textarea:
                await textarea.fill(SLIDE_INSTRUCTION)
                print(f"  ✓ 지시사항 입력")
                await asyncio.sleep(1)

            # 생성 버튼
            gen_btn = await find_element(page, [
                'button:has-text("생성")',
                'button:has-text("Generate")',
                'button:has-text("만들기")',
            ])

            if gen_btn:
                await safe_click(page, gen_btn, "생성 시작")
                print("  슬라이드 생성 중... (최대 3분)")

                # 생성 완료 대기
                for i in range(36):
                    await asyncio.sleep(5)
                    # 완료 확인 (다운로드 버튼 또는 슬라이드 미리보기)
                    done = await find_element(page, [
                        'button:has-text("다운로드")',
                        'button:has-text("Download")',
                        '[aria-label*="다운로드"]',
                        '.slide-preview',
                    ], timeout=1000)
                    if done:
                        print(f"  ✓ 생성 완료! ({(i+1)*5}초)")
                        break
                    if i % 6 == 5:
                        print(f"    생성 중... {(i+1)*5}초")

                await screenshot(page, "05_generated")

        # 4. 다운로드
        print("\n[4/5] 다운로드...")

        downloaded = False

        # 다운로드 버튼 찾기
        download_btn = await find_element(page, [
            'button:has-text("다운로드")',
            'button:has-text("Download")',
            '[aria-label*="다운로드"]',
            '[aria-label*="Download"]',
        ])

        if download_btn:
            try:
                async with page.expect_download(timeout=60000) as download_info:
                    await download_btn.click()
                    await asyncio.sleep(3)

                    # PDF 선택 (옵션이 있으면)
                    pdf_btn = await find_element(page, [
                        'button:has-text("PDF")',
                        'text="PDF"',
                    ], timeout=3000)
                    if pdf_btn:
                        await pdf_btn.click()

                download = await download_info.value
                filename = f"slides_{NOTEBOOK_TITLE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                save_path = DOWNLOAD_DIR / filename
                await download.save_as(str(save_path))
                print(f"  ✓ 다운로드 완료: {save_path}")
                downloaded = True
            except Exception as e:
                print(f"  다운로드 오류: {e}")

        if not downloaded:
            await screenshot(page, "06_download_failed")
            print("  ⚠️ 자동 다운로드 실패")
            print("  수동 다운로드를 위해 브라우저 유지...")

        # 5. 완료
        print("\n[5/5] 완료")
        await screenshot(page, "07_final")
        print("="*60)

        if downloaded:
            print(f"\n✓ 다운로드 완료: {save_path}")
            print("\n브라우저를 10초 후 종료합니다...")
            await asyncio.sleep(10)
        else:
            print("\n브라우저를 60초간 유지합니다. 수동으로 다운로드하세요.")
            await asyncio.sleep(60)

        await context.close()

        print("\n작업 완료!")
        print(f"스크린샷: {SCREENSHOT_DIR}")
        print(f"다운로드: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
