#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Artifact에서 100개 슬라이드 프롬프트 추출
"""
import sys
import json
import asyncio
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

URL = "https://claude.ai/public/artifacts/c0054e9c-3e09-41d7-9d4e-2396c3816d84"

async def extract_prompts():
    prompts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("페이지 로딩 중...")
        await page.goto(URL)
        await page.wait_for_timeout(3000)

        # iframe 찾기
        frame = page.frame_locator('iframe[title="Claude 콘텐츠"]')

        # 모든 디자인 버튼 찾기
        buttons = await frame.locator('main button').all()
        total = len(buttons)
        print(f"총 {total}개 디자인 발견")

        for i in range(total):
            try:
                # 버튼 다시 가져오기 (DOM 변경 때문)
                buttons = await frame.locator('main button').all()
                btn = buttons[i]

                # 버튼 클릭
                await btn.click()
                await page.wait_for_timeout(400)

                # 프롬프트 (textarea 또는 input)
                prompt_el = frame.locator('textarea, input[type="text"]').first
                prompt = await prompt_el.input_value()

                if prompt:
                    # 프롬프트에서 이름과 카테고리 파싱
                    lines = prompt.split('\n')
                    name = ""
                    category = ""
                    for line in lines:
                        if "■ 스타일:" in line:
                            name = line.replace("■ 스타일:", "").strip()
                        elif "■ 카테고리:" in line:
                            category = line.replace("■ 카테고리:", "").strip()

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
                await page.wait_for_timeout(200)

            except Exception as e:
                print(f"[{i+1}/{total}] 오류: {e}")
                try:
                    close_btn = frame.locator('button:has-text("✕")')
                    await close_btn.click()
                    await page.wait_for_timeout(200)
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
