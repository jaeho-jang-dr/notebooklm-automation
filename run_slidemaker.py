#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
족저근막염 슬라이드 생성 스크립트
- 미니멀 젠 디자인
- 15장 한글 슬라이드
- PDF 다운로드 → PPTX 변환
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

# 설정
NOTEBOOK_TITLE = "족저근막염"
DESIGN_NAME = "미니멀 젠"
SLIDE_COUNT = 15
DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")
BROWSER_PROFILE = Path.home() / '.notebooklm-mcp-cli' / 'browser_profile'

# 미니멀 젠 디자인 프롬프트
DESIGN_PROMPT = """미니멀 젠 스타일로 만들어주세요: 깔끔하고 간결한 레이아웃, 충분한 여백, 차분한 색상, 핵심만 전달하는 심플한 디자인"""


async def main():
    print("\n" + "=" * 60)
    print(f"  🎯 노트랑 슬라이드 생성")
    print(f"  노트북: {NOTEBOOK_TITLE}")
    print(f"  디자인: {DESIGN_NAME}")
    print("=" * 60)

    p = await async_playwright().start()

    # 브라우저 프로필로 시작
    print("\n[1/6] 브라우저 시작...")
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=str(BROWSER_PROFILE),
        headless=False,
        args=['--disable-blink-features=AutomationControlled'],
        viewport={'width': 1920, 'height': 1080}
    )

    page = browser.pages[0] if browser.pages else await browser.new_page()

    try:
        # NotebookLM 접속
        print("\n[2/6] NotebookLM 접속...")
        await page.goto('https://notebooklm.google.com/')
        await page.wait_for_timeout(5000)

        url = page.url
        if 'accounts.google' in url or 'signin' in url.lower():
            print("  ⚠️ 로그인이 필요합니다. 브라우저에서 로그인 후 Enter를 누르세요...")
            input()
            await page.goto('https://notebooklm.google.com/')
            await page.wait_for_timeout(5000)

        print(f"  ✓ NotebookLM 접속 완료")

        # 노트북 찾기 및 클릭
        print(f"\n[3/6] 노트북 '{NOTEBOOK_TITLE}' 열기...")
        await page.wait_for_timeout(2000)

        # 노트북 목록에서 찾기 - 여러 방법 시도
        notebook_clicked = False

        # 방법 1: get_by_text 사용
        try:
            notebook_row = page.get_by_text(NOTEBOOK_TITLE, exact=False).first
            await notebook_row.click(timeout=10000)
            notebook_clicked = True
            print(f"  ✓ 노트북 클릭 (get_by_text)")
        except Exception as e:
            print(f"  방법1 실패: {e}")

        # 방법 2: 모든 링크에서 텍스트 확인
        if not notebook_clicked:
            try:
                links = await page.query_selector_all('a')
                for link in links:
                    text = await link.inner_text()
                    if NOTEBOOK_TITLE in text:
                        await link.click()
                        notebook_clicked = True
                        print(f"  ✓ 노트북 클릭 (링크 검색)")
                        break
            except Exception as e:
                print(f"  방법2 실패: {e}")

        # 방법 3: 테이블 행에서 찾기
        if not notebook_clicked:
            try:
                rows = await page.query_selector_all('tr, [role="row"]')
                for row in rows:
                    text = await row.inner_text()
                    if NOTEBOOK_TITLE in text:
                        await row.click()
                        notebook_clicked = True
                        print(f"  ✓ 노트북 클릭 (행 검색)")
                        break
            except Exception as e:
                print(f"  방법3 실패: {e}")

        # 방법 4: 첫 번째 노트북 클릭 (족저근막염이 첫 번째라면)
        if not notebook_clicked:
            print("  첫 번째 노트북을 클릭합니다...")
            try:
                first_notebook = await page.query_selector('a[href*="notebook"]')
                if first_notebook:
                    await first_notebook.click()
                    notebook_clicked = True
                    print(f"  ✓ 첫 번째 노트북 클릭")
            except Exception as e:
                print(f"  방법4 실패: {e}")

        if not notebook_clicked:
            print("  ⚠️ 노트북을 자동으로 찾지 못했습니다.")
            print(f"  브라우저에서 '{NOTEBOOK_TITLE}' 노트북을 직접 클릭해주세요.")
            input("  클릭 후 Enter...")

        # 노트북 로딩 대기 - URL이 변경될 때까지
        await page.wait_for_timeout(5000)

        # 노트북이 제대로 열렸는지 확인
        current_url = page.url
        if 'notebook' not in current_url:
            print(f"  ⚠️ 노트북이 열리지 않았습니다. URL: {current_url}")
            # 다시 시도
            await page.goto('https://notebooklm.google.com/')
            await page.wait_for_timeout(3000)
            notebook_row = page.locator(f'text="{NOTEBOOK_TITLE}"').first
            await notebook_row.click()
            await page.wait_for_timeout(5000)

        await page.screenshot(path="debug_notebook_open.png")
        print(f"  디버그: debug_notebook_open.png")

        # 스튜디오 패널에서 "슬라이드 자료" 찾기
        print("\n[4/6] 슬라이드 자료 생성...")

        # 스튜디오 패널이 있는지 확인
        studio_panel = page.locator('text="스튜디오"')
        if await studio_panel.count() == 0:
            # Studio 버튼이 있다면 클릭
            studio_btn = page.locator('text="Studio"')
            if await studio_btn.count() > 0:
                await studio_btn.first.click()
                await page.wait_for_timeout(2000)

        # "슬라이드 자료" 버튼 클릭
        slides_btn = page.locator('text="슬라이드 자료"')
        if await slides_btn.count() > 0:
            await slides_btn.first.click()
            print("  ✓ '슬라이드 자료' 클릭")
            await page.wait_for_timeout(3000)
        else:
            # 영어 UI일 경우
            slides_btn = page.locator('text="Slides"')
            if await slides_btn.count() > 0:
                await slides_btn.first.click()
                print("  ✓ 'Slides' 클릭")
                await page.wait_for_timeout(3000)

        await page.screenshot(path="debug_slides_panel.png")
        print(f"  디버그: debug_slides_panel.png")

        # 슬라이드 생성 다이얼로그/패널 처리
        print("\n[5/6] 슬라이드 설정...")

        # Customize 버튼 찾기
        customize_btn = page.locator('text="Customize"')
        if await customize_btn.count() > 0:
            await customize_btn.first.click()
            print("  ✓ Customize 클릭")
            await page.wait_for_timeout(2000)

        # "맞춤설정" (한글 UI)
        customize_btn_kr = page.locator('text="맞춤설정"')
        if await customize_btn_kr.count() > 0:
            await customize_btn_kr.first.click()
            print("  ✓ 맞춤설정 클릭")
            await page.wait_for_timeout(2000)

        await page.screenshot(path="debug_customize_panel.png")

        # 언어 선택 - Korean
        # 드롭다운 찾기 (언어 선택 영역)
        try:
            lang_dropdown = page.locator('select').first
            if await lang_dropdown.count() > 0:
                await lang_dropdown.select_option(label="Korean")
                print("  ✓ Korean 선택 (select)")
            else:
                # 커스텀 드롭다운인 경우
                lang_btn = page.locator('[aria-haspopup="listbox"]').first
                if await lang_btn.count() > 0:
                    await lang_btn.click()
                    await page.wait_for_timeout(500)
                    korean = page.locator('text="Korean"')
                    if await korean.count() > 0:
                        await korean.first.click()
                        print("  ✓ Korean 선택")
        except Exception as e:
            print(f"  ⚠️ 언어 선택: {e}")

        # 슬라이드 수 설정
        try:
            num_input = page.locator('input[type="number"]')
            if await num_input.count() > 0:
                await num_input.first.fill(str(SLIDE_COUNT))
                print(f"  ✓ 슬라이드 수: {SLIDE_COUNT}")
        except Exception as e:
            print(f"  ⚠️ 슬라이드 수 설정: {e}")

        # 프롬프트 입력 (있는 경우)
        try:
            prompt_area = page.locator('textarea')
            if await prompt_area.count() > 0:
                first_textarea = prompt_area.first
                if await first_textarea.is_visible() and await first_textarea.is_enabled():
                    await first_textarea.fill(DESIGN_PROMPT)
                    print("  ✓ 디자인 프롬프트 입력")
        except Exception as e:
            print(f"  ⚠️ 프롬프트: {e}")

        await page.screenshot(path="debug_before_generate.png")

        # Generate/만들기 버튼 클릭
        print("\n  Generate 버튼 찾는 중...")
        generate_clicked = False

        # 여러 가지 버튼 텍스트 시도
        for btn_text in ["Generate", "Create", "만들기", "생성"]:
            btn = page.locator(f'button:has-text("{btn_text}")')
            if await btn.count() > 0:
                try:
                    await btn.first.click()
                    generate_clicked = True
                    print(f"  ✓ '{btn_text}' 버튼 클릭")
                    break
                except:
                    continue

        if not generate_clicked:
            print("  ⚠️ Generate 버튼을 자동으로 찾지 못했습니다.")
            print("  브라우저에서 수동으로 'Generate' 또는 '만들기' 버튼을 클릭해주세요.")
            input("  클릭 후 Enter를 누르세요...")

        # 생성 완료 대기
        print("\n[6/6] 슬라이드 생성 대기...")
        download_ready = False

        for i in range(60):  # 최대 10분 대기
            await page.wait_for_timeout(10000)

            # 진행 상황 스크린샷 (3회마다)
            if i % 3 == 0:
                await page.screenshot(path=f"debug_gen_{i}.png")

            # Download 버튼 확인
            download_btn = page.locator('button:has-text("Download"), button:has-text("다운로드")')
            if await download_btn.count() > 0:
                try:
                    if await download_btn.first.is_visible() and await download_btn.first.is_enabled():
                        print(f"\n  ✓ 슬라이드 생성 완료! ({(i+1)*10}초)")
                        download_ready = True
                        break
                except:
                    pass

            # PDF 미리보기 확인 (슬라이드가 생성되면 나타남)
            pdf_preview = page.locator('[class*="preview"], [class*="slide"]')
            if await pdf_preview.count() > 0:
                print(f"  ... 슬라이드 렌더링 중 ({(i+1)*10}초)")
            else:
                print(f"  ... 생성 중 ({(i+1)*10}초)")

        if not download_ready:
            print("\n  ⚠️ 자동 감지 실패 - 수동으로 확인해주세요")
            input("  다운로드 준비되면 Enter...")

        # PDF 다운로드
        print("\n[다운로드] PDF 다운로드...")
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"{NOTEBOOK_TITLE}_{DESIGN_NAME}_{timestamp}.pdf"
        pdf_path = DOWNLOAD_DIR / pdf_filename

        try:
            async with page.expect_download(timeout=60000) as download_info:
                download_btn = page.locator('button:has-text("Download"), button:has-text("다운로드")').first
                await download_btn.click()

            download = await download_info.value
            await download.save_as(str(pdf_path))
            print(f"  ✓ PDF 저장: {pdf_path}")

        except Exception as e:
            print(f"  ⚠️ 자동 다운로드 실패: {e}")
            print(f"  브라우저에서 Download 버튼을 클릭하고,")
            print(f"  파일을 {DOWNLOAD_DIR}에 저장해주세요.")
            input("  저장 완료 후 Enter...")

            # 최근 다운로드 파일 찾기
            downloads = list(DOWNLOAD_DIR.glob("*.pdf"))
            if downloads:
                latest = max(downloads, key=lambda x: x.stat().st_mtime)
                pdf_path = latest
                print(f"  ✓ 최근 PDF 발견: {pdf_path}")

        # PPTX 변환
        if pdf_path.exists():
            print("\n[변환] PDF → PPTX...")
            from noterang.converter import pdf_to_pptx

            pptx_path = pdf_path.with_suffix('.pptx')
            if pdf_to_pptx(str(pdf_path), str(pptx_path)):
                print(f"  ✓ PPTX 저장: {pptx_path}")

            print("\n" + "=" * 60)
            print("  ✅ 완료!")
            print(f"  PDF:  {pdf_path}")
            print(f"  PPTX: {pptx_path}")
            print("=" * 60)
        else:
            print(f"\n  ⚠️ PDF 파일 없음: {pdf_path}")

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        await page.screenshot(path="debug_error.png")

    finally:
        print("\n브라우저를 닫으시겠습니까? (y/n): ", end="")
        try:
            if input().lower() == 'y':
                await browser.close()
                await p.stop()
        except:
            await browser.close()
            await p.stop()


if __name__ == "__main__":
    asyncio.run(main())
