#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""족저근막염 노트북에서 슬라이드 다운로드"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang.browser import NotebookLMBrowser
from noterang.convert import pdf_to_pptx


async def main():
    output_dir = Path(r"G:\내 드라이브\notebooklm")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🔍 NotebookLM 브라우저 시작...")

    async with NotebookLMBrowser() as browser:
        # 로그인 확인
        print("🔑 로그인 확인 중...")
        if not await browser.ensure_logged_in():
            print("❌ 로그인 필요합니다. 브라우저에서 직접 로그인하세요.")
            return

        print("✅ 로그인 완료!")

        # NotebookLM 메인 페이지로 이동
        print("📚 노트북 목록 페이지로 이동...")
        await browser.page.goto("https://notebooklm.google.com", wait_until='domcontentloaded')
        await asyncio.sleep(5)

        # 족저근막염 노트북 찾기 (텍스트로 검색)
        print("🔍 족저근막염 노트북 찾는 중...")

        # 테이블 행에서 족저근막염 찾기
        rows = await browser.page.query_selector_all('tr, [role="row"], a[href*="/notebook/"]')
        print(f"  테이블 행 {len(rows)}개 발견")

        target_link = None
        for row in rows:
            text = await row.inner_text()
            if '족저근막염' in text:
                print(f"  ✅ 찾음: {text[:50]}...")
                # 링크나 클릭 가능한 요소 찾기
                link = await row.query_selector('a[href*="/notebook/"]')
                if link:
                    target_link = link
                    break
                # 행 자체가 클릭 가능할 수 있음
                target_link = row
                break

        # 다른 방법: 직접 텍스트로 찾기
        if not target_link:
            print("  대체 방법으로 검색 중...")
            target_link = await browser.page.query_selector('text="족저근막염"')

        if not target_link:
            # 전체 링크에서 찾기
            all_links = await browser.page.query_selector_all('a')
            for link in all_links:
                text = await link.inner_text()
                if '족저근막염' in text:
                    target_link = link
                    print(f"  ✅ 링크에서 찾음: {text[:50]}...")
                    break

        if not target_link:
            print("❌ 족저근막염 노트북을 찾을 수 없습니다.")
            await browser.screenshot(output_dir / "debug_not_found.png")
            return

        # 노트북 클릭
        print("📖 노트북 열기...")
        await target_link.click()
        await asyncio.sleep(8)

        # 현재 URL 확인
        current_url = browser.page.url
        print(f"  현재 URL: {current_url}")

        # 슬라이드/아티팩트 찾기
        print("🎨 슬라이드 찾는 중...")

        # 저장된 응답/슬라이드 섹션 찾기
        # NotebookLM에서 슬라이드는 보통 "저장된 응답" 또는 "Saved responses"에 있음
        await asyncio.sleep(3)

        # 먼저 스크린샷 저장
        await browser.screenshot(output_dir / "debug_notebook_page.png")

        # 슬라이드 관련 버튼/요소 찾기
        slide_selectors = [
            'button:has-text("슬라이드")',
            'button:has-text("Slides")',
            '[aria-label*="slide"]',
            '[aria-label*="presentation"]',
            'button:has-text("프레젠테이션")',
            # 저장된 응답 영역
            '[class*="saved"]',
            '[class*="artifact"]',
        ]

        slide_elem = None
        for sel in slide_selectors:
            slide_elem = await browser.page.query_selector(sel)
            if slide_elem:
                print(f"  슬라이드 요소 발견: {sel}")
                break

        # 다운로드 시도
        print("💾 다운로드 시도 중...")

        # 더보기 메뉴에서 다운로드 찾기
        menu_buttons = await browser.page.query_selector_all('button[aria-haspopup="menu"], button[aria-label*="more"], button[aria-label*="더"]')
        print(f"  메뉴 버튼 {len(menu_buttons)}개 발견")

        downloaded = False
        for i, menu_btn in enumerate(menu_buttons[-15:]):  # 최근 15개만
            try:
                # 버튼 정보 출력
                label = await menu_btn.get_attribute('aria-label') or ''
                print(f"  메뉴 버튼 {i}: {label[:30]}...")

                await menu_btn.click(force=True)
                await asyncio.sleep(1)

                # 다운로드 메뉴 아이템 찾기
                dl_item = await browser.page.query_selector(
                    '[role="menuitem"]:has-text("다운로드"), '
                    '[role="menuitem"]:has-text("Download"), '
                    '[role="menuitem"]:has-text("내보내기"), '
                    '[role="menuitem"]:has-text("Export")'
                )

                if dl_item:
                    print("  ✅ 다운로드 메뉴 발견!")

                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"족저근막염_clay3d_{timestamp}.pdf"

                    try:
                        async with browser.page.expect_download(timeout=30000) as download_info:
                            await dl_item.click()

                        download = await download_info.value
                        downloaded_path = output_dir / filename
                        await download.save_as(str(downloaded_path))
                        print(f"  ✅ 다운로드 완료: {downloaded_path}")

                        # PPTX 변환
                        print("🔄 PPTX 변환 중...")
                        pptx_path = downloaded_path.with_suffix('.pptx')
                        result_path, slide_count = pdf_to_pptx(downloaded_path, pptx_path)

                        if result_path:
                            print(f"✅ 변환 완료: {result_path} ({slide_count} 슬라이드)")
                        else:
                            print("❌ PPTX 변환 실패")

                        downloaded = True
                        break
                    except Exception as e:
                        print(f"  다운로드 실패: {e}")

                # 메뉴 닫기
                await browser.page.keyboard.press('Escape')
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"  메뉴 처리 오류: {e}")
                try:
                    await browser.page.keyboard.press('Escape')
                except:
                    pass

        if not downloaded:
            print("\n⚠️ 자동 다운로드 실패. 수동 다운로드 방법:")
            print("  1. 노트북의 '저장된 응답' 섹션 확인")
            print("  2. Clay 3D 슬라이드 옆 ... 메뉴 클릭")
            print("  3. '다운로드' 선택")

            # 최종 스크린샷
            await browser.screenshot(output_dir / "debug_final.png")
            print(f"\n  스크린샷 저장됨: {output_dir / 'debug_final.png'}")


if __name__ == "__main__":
    asyncio.run(main())
