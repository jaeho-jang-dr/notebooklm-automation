#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""브라우저를 통해 슬라이드 직접 다운로드"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

NOTEBOOK_ID = "9204bd03-cddb-4866-8f7d-bcffcf7aff97"
DOWNLOAD_DIR = Path("D:/Entertainments/DevEnvironment/notebooklm")

async def main():
    from playwright.async_api import async_playwright

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    auth_dir = Path.home() / ".notebooklm-mcp-cli"
    user_data_dir = auth_dir / "browser_profile"

    print("브라우저로 슬라이드 다운로드")
    print("=" * 50)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            downloads_path=str(DOWNLOAD_DIR),
            accept_downloads=True,
            args=['--disable-blink-features=AutomationControlled', '--start-maximized'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # 노트북 열기
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"
        print(f"\n1. 노트북 열기...")

        try:
            await page.goto(notebook_url, wait_until='domcontentloaded', timeout=30000)
        except:
            pass

        await asyncio.sleep(8)  # 페이지 완전 로드 대기

        # 스크린샷
        screenshot_path = DOWNLOAD_DIR / "page_state.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"   스크린샷: {screenshot_path}")

        # 스튜디오 패널 확인 및 슬라이드 찾기
        print("\n2. 슬라이드 찾기...")

        # 모든 텍스트 중 "슬라이드" 또는 "Slide" 포함 요소 찾기
        all_text = await page.inner_text('body')
        has_slides = '슬라이드' in all_text or 'Slide' in all_text or 'slide' in all_text
        print(f"   슬라이드 관련 텍스트 존재: {has_slides}")

        # 다운로드 시도
        downloaded = False
        download_path = None

        # 스튜디오 패널의 아티팩트 카드에서 다운로드 버튼 찾기
        print("\n3. 다운로드 버튼 찾기...")

        # 다양한 다운로드 버튼 셀렉터 시도
        selectors = [
            'button[aria-label*="다운로드"]',
            'button[aria-label*="Download"]',
            'button:has-text("다운로드")',
            'button:has-text("Download")',
            '[role="button"]:has-text("다운로드")',
            '[role="button"]:has-text("Download")',
        ]

        for selector in selectors:
            btns = await page.query_selector_all(selector)
            if btns:
                print(f"   발견: {selector} ({len(btns)}개)")
                for btn in btns:
                    try:
                        # 다운로드 이벤트 리스너 설정
                        async with page.expect_download(timeout=30000) as download_info:
                            await btn.click()
                            await asyncio.sleep(2)

                            # PDF 옵션 있으면 클릭
                            pdf_opt = await page.query_selector('button:has-text("PDF"), text="PDF"')
                            if pdf_opt:
                                await pdf_opt.click()

                        download = await download_info.value
                        filename = f"견관절회전근개파열_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        download_path = DOWNLOAD_DIR / filename
                        await download.save_as(str(download_path))
                        print(f"\n✓ 다운로드 성공: {download_path}")
                        downloaded = True
                        break
                    except Exception as e:
                        print(f"   시도 실패: {str(e)[:50]}")
                        continue

                if downloaded:
                    break

        if not downloaded:
            print("\n4. 메뉴를 통한 다운로드 시도...")

            # 더보기 메뉴 (⋮) 찾기
            menu_selectors = [
                'button[aria-label*="더보기"]',
                'button[aria-label*="옵션"]',
                'button[aria-label*="more"]',
                'button[aria-label*="options"]',
                '[aria-haspopup="menu"]',
            ]

            for selector in menu_selectors:
                menu_btns = await page.query_selector_all(selector)
                if menu_btns:
                    print(f"   메뉴 버튼 발견: {len(menu_btns)}개")
                    for menu_btn in menu_btns[-5:]:  # 최근 것부터
                        try:
                            await menu_btn.click(force=True)
                            await asyncio.sleep(1)

                            # 메뉴에서 다운로드 항목 찾기
                            dl_item = await page.query_selector('[role="menuitem"]:has-text("다운로드"), [role="menuitem"]:has-text("Download")')
                            if dl_item:
                                async with page.expect_download(timeout=30000) as download_info:
                                    await dl_item.click()

                                download = await download_info.value
                                filename = f"견관절회전근개파열_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                download_path = DOWNLOAD_DIR / filename
                                await download.save_as(str(download_path))
                                print(f"\n✓ 다운로드 성공: {download_path}")
                                downloaded = True
                                break
                        except:
                            await page.keyboard.press('Escape')
                            await asyncio.sleep(0.5)

                    if downloaded:
                        break

        if not downloaded:
            print("\n❌ 자동 다운로드 실패")
            print("\n수동 다운로드 안내:")
            print("1. 오른쪽 '스튜디오' 패널 확인")
            print("2. 생성된 슬라이드 카드의 메뉴(⋮) 클릭")
            print("3. '다운로드' → 'PDF' 선택")
            print(f"\n저장 위치: {DOWNLOAD_DIR}")
            print("\n60초 대기 후 자동 종료...")
            await asyncio.sleep(60)
        else:
            print(f"\n✓ 파일 저장됨: {download_path}")
            await asyncio.sleep(5)

        await context.close()
        print("\n완료!")

        if downloaded:
            return str(download_path)
        return None

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\n결과: {result}")
