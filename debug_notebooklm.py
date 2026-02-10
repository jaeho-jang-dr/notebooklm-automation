#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NotebookLM UI 디버깅"""
import asyncio
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang.browser import NotebookLMBrowser


async def debug():
    """UI 상태 확인 및 스크린샷"""
    browser = NotebookLMBrowser()
    browser.config.browser_headless = False  # 화면 표시

    await browser.start()

    print("[1] 로그인 확인...")
    logged_in = await browser.ensure_logged_in()
    print(f"    로그인 상태: {logged_in}")

    # 스크린샷 1: 메인 페이지
    screenshot_path = Path("G:/내 드라이브/notebooklm/debug_main_page.png")
    await browser.page.screenshot(path=str(screenshot_path))
    print(f"    스크린샷: {screenshot_path}")

    # 현재 페이지의 모든 버튼 텍스트 출력
    print("\n[2] 페이지의 모든 버튼:")
    buttons = await browser.page.query_selector_all('button')
    for i, btn in enumerate(buttons[:20]):
        try:
            text = await btn.inner_text()
            aria = await btn.get_attribute('aria-label')
            print(f"    {i+1}. text='{text.strip()[:30]}' aria='{aria}'")
        except:
            pass

    # 노트북 생성 버튼 시도
    print("\n[3] 노트북 생성 버튼 찾기...")

    # 다양한 셀렉터 시도
    selectors = [
        'button:has-text("새 노트북")',
        'button:has-text("Create")',
        'button:has-text("New")',
        'button:has-text("만들기")',
        '[aria-label*="Create"]',
        '[aria-label*="New"]',
        '[aria-label*="노트북"]',
        'a:has-text("새 노트북")',
        'a:has-text("Create")',
        '.create-button',
        '[data-testid*="create"]',
    ]

    for sel in selectors:
        try:
            elem = await browser.page.query_selector(sel)
            if elem:
                print(f"    FOUND: {sel}")
                # 클릭 시도
                await elem.click()
                await asyncio.sleep(3)

                # 스크린샷 2: 클릭 후
                screenshot_path2 = Path("G:/내 드라이브/notebooklm/debug_after_click.png")
                await browser.page.screenshot(path=str(screenshot_path2))
                print(f"    스크린샷 (클릭 후): {screenshot_path2}")
                break
        except Exception as e:
            pass
    else:
        print("    생성 버튼을 찾지 못함")

    # 페이지 HTML 일부 저장
    html = await browser.page.content()
    html_path = Path("G:/내 드라이브/notebooklm/debug_page.html")
    html_path.write_text(html[:50000], encoding='utf-8')
    print(f"\n[4] HTML 저장: {html_path}")

    print("\n[5] 30초 대기 (브라우저 확인)...")
    await asyncio.sleep(30)

    await browser.close()
    print("\n완료")


if __name__ == "__main__":
    asyncio.run(debug())
