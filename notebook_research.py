#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 브라우저 자동화 - 연구 자료 수집 및 슬라이드 생성
Conductor가 NotebookLM을 지휘하여 자료 수집 및 슬라이드 생성
"""
import asyncio
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

NOTEBOOK_ID = "9204bd03-cddb-4866-8f7d-bcffcf7aff97"
NOTEBOOK_TITLE = "견관절회전근개 파열"

# 연구 주제 (한글)
RESEARCH_QUERY = "견관절 회전근개 파열 병인 치료 수술 비수술 재활"

async def wait_for_login(page, timeout=120):
    """로그인 완료 대기"""
    print("로그인 상태 확인 중...")
    for i in range(timeout // 5):
        url = page.url
        if 'notebooklm.google.com' in url and 'accounts.google' not in url:
            if '/notebook/' in url or url.endswith('.com/'):
                print("로그인 확인됨!")
                return True
        await asyncio.sleep(5)
        print(f"  대기 중... {(i+1)*5}초")
    return False

async def click_if_exists(page, selector, timeout=5000):
    """요소가 있으면 클릭"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            return True
    except:
        pass
    return False

async def main():
    from playwright.async_api import async_playwright

    auth_dir = Path.home() / ".notebooklm-mcp-cli"
    user_data_dir = auth_dir / "browser_profile"
    user_data_dir.mkdir(exist_ok=True)

    print("="*60)
    print(f"NotebookLM 컨덕터: {NOTEBOOK_TITLE}")
    print("="*60)
    print()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--start-maximized',
                '--no-first-run',
                '--no-default-browser-check',
            ],
            ignore_default_args=['--enable-automation'],
            viewport=None,
            no_viewport=True,
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # NotebookLM 노트북으로 이동
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"
        print(f"[1/5] 노트북 열기: {notebook_url}")

        try:
            await page.goto(notebook_url, wait_until='networkidle', timeout=60000)
        except Exception as e:
            print(f"  페이지 로드 중... (타임아웃 무시)")

        # 로그인 확인
        print("\n[2/5] 로그인 확인")
        logged_in = await wait_for_login(page, timeout=60)
        if not logged_in:
            print("  로그인이 필요합니다. 브라우저에서 로그인 해주세요.")
            await wait_for_login(page, timeout=300)

        await asyncio.sleep(3)

        # 연구 시작 안내
        print("\n[3/5] 연구 자료 수집")
        print("="*60)
        print("NotebookLM에서 다음 작업을 수행해 주세요:")
        print()
        print("1. 왼쪽 패널에서 '+ Add source' 클릭")
        print("2. 'Website' 또는 'Research' 선택")
        print("3. 다음 주제로 검색:")
        print(f"   '{RESEARCH_QUERY}'")
        print()
        print("4. 관련 자료들을 선택하여 추가")
        print("   - 병인/원인에 대한 자료")
        print("   - 수술적 치료 방법")
        print("   - 비수술적 치료 방법")
        print("   - 재활 운동/물리치료")
        print()
        print("⚠️  모든 자료는 한글 소스를 우선 선택하세요")
        print("="*60)

        input("\n자료 추가 완료 후 Enter를 누르세요...")

        # 슬라이드 생성
        print("\n[4/5] 슬라이드 생성")
        print("="*60)
        print("NotebookLM Studio에서 슬라이드를 생성해 주세요:")
        print()
        print("1. 오른쪽 'Studio' 패널 열기")
        print("2. 'Slide deck' 선택")
        print("3. 커스텀 지시사항에 다음 입력:")
        print()
        print('   "모든 내용을 한글로 작성해주세요. ')
        print('    병인, 치료방법, 재활법 순서로 구성해주세요."')
        print()
        print("4. 'Generate' 클릭하여 생성")
        print("="*60)

        input("\n슬라이드 생성 완료 후 Enter를 누르세요...")

        # 다운로드 안내
        print("\n[5/5] 슬라이드 다운로드")
        print("="*60)
        print("생성된 슬라이드를 다운로드해 주세요:")
        print()
        print("1. 생성된 슬라이드 옆 '⋮' 메뉴 클릭")
        print("2. 'Download as PDF' 선택")
        print("3. 저장 위치: D:/Entertainments/DevEnvironment/notebooklm/")
        print("="*60)

        input("\n다운로드 완료 후 Enter를 누르세요...")

        print("\n브라우저를 종료합니다...")
        await asyncio.sleep(2)
        await context.close()

        print("\n" + "="*60)
        print("작업 완료!")
        print("="*60)
        print()
        print("다음 단계:")
        print("- Claude가 다운로드된 PDF를 PPTX로 변환합니다")
        print("- 필요시 여러 슬라이드를 병합합니다")

if __name__ == "__main__":
    asyncio.run(main())
