#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Artifact에서 100개 슬라이드 프롬프트 추출
MCP Playwright 세션 활용
"""
import sys
import json
import asyncio
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 버퍼 비활성화
import functools
print = functools.partial(print, flush=True)

from playwright.async_api import async_playwright

URL = "https://claude.ai/public/artifacts/c0054e9c-3e09-41d7-9d4e-2396c3816d84"
BROWSER_PROFILE = Path.home() / '.notebooklm-mcp-cli' / 'browser_profile'

async def extract_prompts():
    prompts = []

    async with async_playwright() as p:
        # 일반 브라우저 (공개 아티팩트는 로그인 불필요)
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = await browser.new_page()
        await page.set_viewport_size({'width': 1920, 'height': 1080})

        print("페이지 로딩 중...")
        await page.goto(URL)
        await page.wait_for_timeout(5000)

        # iframe 찾기 - frame_locator 사용
        iframes = page.locator('iframe')
        iframe_count = await iframes.count()
        print(f"iframe 개수: {iframe_count}")

        if iframe_count == 0:
            print("iframe을 찾을 수 없습니다")
            await browser.close()
            return []

        # 첫 번째 iframe의 frame_locator
        frame = page.frame_locator('iframe').first

        # 모든 디자인 버튼 찾기 (main 영역 내)
        buttons = await frame.locator('main button').all()
        total = len(buttons)
        print(f"총 {total}개 디자인 발견")

        for i in range(total):
            try:
                # 버튼 다시 가져오기 (DOM 변경 대비)
                buttons = await frame.locator('main button').all()
                if i >= len(buttons):
                    print(f"[{i+1}] 버튼 인덱스 초과, 스킵")
                    continue

                btn = buttons[i]

                # 버튼 클릭
                await btn.click()
                await page.wait_for_timeout(600)

                # 프롬프트 (textbox)
                textbox = frame.locator('textbox')
                prompt = await textbox.input_value()

                if prompt:
                    # 프롬프트에서 이름과 카테고리 파싱
                    name = ""
                    category = ""

                    # ■ 스타일: 추출
                    if "■ 스타일:" in prompt:
                        style_start = prompt.find("■ 스타일:") + len("■ 스타일:")
                        style_end = prompt.find("■", style_start)
                        if style_end == -1:
                            style_end = prompt.find("\n", style_start)
                        name = prompt[style_start:style_end].strip()

                    # ■ 카테고리: 추출
                    if "■ 카테고리:" in prompt:
                        cat_start = prompt.find("■ 카테고리:") + len("■ 카테고리:")
                        cat_end = prompt.find("━", cat_start)
                        if cat_end == -1:
                            cat_end = prompt.find("\n", cat_start)
                        category = prompt[cat_start:cat_end].strip()

                    prompts.append({
                        "id": i + 1,
                        "name": name,
                        "category": category,
                        "prompt": prompt
                    })
                    print(f"[{i+1}/{total}] {name} ({category})")

                # 모달 닫기
                close_btn = frame.locator('button:has-text("✕")')
                await close_btn.click()
                await page.wait_for_timeout(300)

            except Exception as e:
                print(f"[{i+1}/{total}] 오류: {e}")
                try:
                    close_btn = frame.locator('button:has-text("✕")')
                    await close_btn.click()
                    await page.wait_for_timeout(300)
                except:
                    pass

        await browser.close()

    return prompts


async def main():
    print("=" * 60)
    print("  NotebookLM 슬라이드 프롬프트 추출기")
    print("=" * 60)

    prompts = await extract_prompts()

    # JSON 저장
    output = {
        "source": URL,
        "total": len(prompts),
        "styles": prompts
    }

    output_path = Path("slide_design_gallery/extracted_prompts.json")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n완료! {len(prompts)}개 프롬프트 추출")
    print(f"저장 위치: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
