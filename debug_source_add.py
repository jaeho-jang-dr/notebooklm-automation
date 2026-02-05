#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""소스 추가 UI 디버깅"""
import asyncio
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang.browser import NotebookLMBrowser


async def debug():
    browser = NotebookLMBrowser()
    browser.config.browser_headless = False

    await browser.start()

    print("[1] Login...")
    await browser.ensure_logged_in()

    print("[2] Create notebook...")
    notebook_id = await browser.create_notebook("테스트_아킬레스건염")
    print(f"    ID: {notebook_id}")

    if notebook_id:
        await asyncio.sleep(2)

        # 스크린샷
        await browser.page.screenshot(path="G:/내 드라이브/notebooklm/debug_source_dialog.png")
        print("    Screenshot saved")

        # 모든 input 찾기
        print("\n[3] All inputs on page:")
        inputs = await browser.page.query_selector_all('input')
        for i, inp in enumerate(inputs[:10]):
            placeholder = await inp.get_attribute('placeholder')
            inp_type = await inp.get_attribute('type')
            print(f"    {i+1}. type={inp_type} placeholder='{placeholder}'")

        # Fast Research 버튼 찾기
        print("\n[4] Looking for Fast Research...")
        fr_btn = await browser.page.query_selector('button:has-text("Fast Research")')
        if fr_btn:
            print("    Found Fast Research button")
            await fr_btn.click()
            await asyncio.sleep(2)
            await browser.page.screenshot(path="G:/내 드라이브/notebooklm/debug_fast_research.png")

        # 소스 추가 버튼 클릭 시도
        print("\n[5] Looking for Add Source...")
        add_btn = await browser.page.query_selector('button:has-text("소스 추가"), [aria-label*="출처 추가"]')
        if add_btn:
            print("    Found Add Source button")
            await add_btn.click()
            await asyncio.sleep(2)
            await browser.page.screenshot(path="G:/내 드라이브/notebooklm/debug_add_source.png")

        print("\n[6] Waiting 20 seconds...")
        await asyncio.sleep(20)

    await browser.close()
    print("\nDone")


if __name__ == "__main__":
    asyncio.run(debug())
