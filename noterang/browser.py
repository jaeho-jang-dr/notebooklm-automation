#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 브라우저 모듈
- Playwright 기반 NotebookLM 직접 제어
- nlm CLI 버그 우회
"""
import asyncio
import json
import sys
import time
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .config import get_config


class NotebookLMBrowser:
    """
    NotebookLM 브라우저 자동화 클래스
    Playwright를 사용하여 직접 NotebookLM 제어
    """

    def __init__(self):
        self.config = get_config()
        self.base_url = "https://notebooklm.google.com"
        self.context = None
        self.page = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """브라우저 시작"""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.config.browser_profile),
            headless=self.config.browser_headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ],
            viewport={
                'width': self.config.browser_viewport_width,
                'height': self.config.browser_viewport_height
            },
            accept_downloads=True,
            downloads_path=str(self.config.download_dir),
        )
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

    async def close(self):
        """브라우저 종료"""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def ensure_logged_in(self) -> bool:
        """로그인 확인 (완전 자동 로그인 포함)"""
        await self.page.goto(self.base_url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)

        # 로그인 페이지로 리다이렉트 되었는지 확인
        if 'accounts.google.com' in self.page.url:
            print("  로그인 필요 - 완전 자동 로그인 시작...")

            # 완전 자동 로그인 시도 (TOTP 포함)
            try:
                from .auto_login import full_auto_login, BROWSER_PROFILE
                success = await full_auto_login(headless=self.config.browser_headless)

                if success:
                    # 자동 로그인 성공 후 브라우저 재시작
                    await self.close()
                    from playwright.async_api import async_playwright
                    self.playwright = await async_playwright().start()
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir=str(BROWSER_PROFILE),
                        headless=self.config.browser_headless,
                        args=['--disable-blink-features=AutomationControlled'],
                        viewport={
                            'width': self.config.browser_viewport_width,
                            'height': self.config.browser_viewport_height
                        },
                        accept_downloads=True,
                        downloads_path=str(self.config.download_dir),
                    )
                    self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
                    await self.page.goto(self.base_url, timeout=30000)
                    await asyncio.sleep(3)
                    return True
            except Exception as e:
                print(f"  완전 자동 로그인 실패: {e}")

            # 폴백: 수동 대기
            start = time.time()
            while time.time() - start < 120:
                if 'notebooklm.google.com' in self.page.url and 'accounts.google' not in self.page.url:
                    break
                await asyncio.sleep(2)

        return 'notebooklm.google.com' in self.page.url and 'accounts.google' not in self.page.url

    async def _try_app_password(self):
        """앱 비밀번호 입력 시도"""
        try:
            password_input = await self.page.query_selector('input[type="password"]')
            if password_input:
                clean_password = self.config.notebooklm_app_password.replace(' ', '')
                await password_input.fill(clean_password)
                await asyncio.sleep(0.5)

                next_btn = await self.page.query_selector('button:has-text("Next"), button:has-text("다음")')
                if next_btn:
                    await next_btn.click()
                    await asyncio.sleep(3)
        except Exception as e:
            print(f"  앱 비밀번호 입력 실패: {e}")

    async def list_notebooks(self) -> List[Dict]:
        """노트북 목록 조회"""
        await self.page.goto(self.base_url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)

        notebooks = []

        # 노트북 카드 찾기
        cards = await self.page.query_selector_all('[data-notebook-id], .notebook-card, [class*="notebook"]')

        for card in cards:
            try:
                notebook_id = await card.get_attribute('data-notebook-id')
                title_elem = await card.query_selector('h3, [class*="title"]')
                title = await title_elem.inner_text() if title_elem else "Untitled"

                if notebook_id:
                    notebooks.append({
                        'id': notebook_id,
                        'title': title.strip()
                    })
            except:
                continue

        # 대체 방법: URL에서 노트북 ID 추출
        if not notebooks:
            links = await self.page.query_selector_all('a[href*="/notebook/"]')
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    if '/notebook/' in href:
                        notebook_id = href.split('/notebook/')[-1].split('/')[0].split('?')[0]
                        title_elem = await link.query_selector('h3, span, [class*="title"]')
                        title = await title_elem.inner_text() if title_elem else notebook_id[:8]

                        if notebook_id and len(notebook_id) > 10:
                            notebooks.append({
                                'id': notebook_id,
                                'title': title.strip()
                            })
                except:
                    continue

        return notebooks

    async def find_notebook(self, title: str) -> Optional[Dict]:
        """제목으로 노트북 찾기"""
        notebooks = await self.list_notebooks()
        for nb in notebooks:
            if nb.get('title') == title:
                return nb
        return None

    async def create_notebook(self, title: str) -> Optional[str]:
        """새 노트북 생성 (2026 UI 대응)"""
        await self.page.goto(self.base_url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)

        # "새로 만들기" 버튼 찾기 (2026 UI: aria-label="새 노트 만들기")
        create_btn = await self.page.query_selector(
            '[aria-label="새 노트 만들기"], '
            'button:has-text("새로 만들기"), '
            'button:has-text("만들기"), '
            'button:has-text("Create"), '
            'button:has-text("New"), '
            '[aria-label*="Create"], '
            '[aria-label*="새 노트북"]'
        )

        if create_btn:
            await create_btn.click()
            await asyncio.sleep(5)  # 노트북 생성 대기

            # 현재 URL에서 노트북 ID 추출 (바로 생성됨)
            current_url = self.page.url
            if '/notebook/' in current_url:
                notebook_id = current_url.split('/notebook/')[-1].split('/')[0].split('?')[0]

                # 모달 닫기 시도 (소스 추가 다이얼로그)
                await self._close_modal()
                await asyncio.sleep(2)

                # 노트북 제목 변경 시도
                await self._rename_notebook(title)

                return notebook_id

        return None

    async def _close_modal(self):
        """모달/다이얼로그 닫기"""
        try:
            # 방법 1: X 버튼 클릭 (close 아이콘)
            close_selectors = [
                'button[aria-label="닫기"]',
                'button[aria-label="Close"]',
                'button:has-text("close")',
                '[aria-label="닫기"]',
                '.cdk-overlay-pane button[aria-label*="닫기"]',
                'mat-dialog-container button[aria-label*="close"]',
            ]
            for sel in close_selectors:
                close_btn = await self.page.query_selector(sel)
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(1)
                    return

            # 방법 2: 오버레이 바깥 클릭
            overlay = await self.page.query_selector('.cdk-overlay-backdrop')
            if overlay:
                await overlay.click(force=True)
                await asyncio.sleep(1)
                return

            # 방법 3: ESC 키
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(1)

            # 방법 4: 다시 ESC (여러 번 필요할 수 있음)
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(1)

        except Exception as e:
            print(f"  모달 닫기 실패 (무시): {e}")

    async def _rename_notebook(self, new_title: str):
        """노트북 제목 변경"""
        try:
            # 제목 영역 클릭 (Untitled notebook)
            title_elem = await self.page.query_selector(
                'h1:has-text("Untitled"), '
                '[class*="title"]:has-text("Untitled"), '
                'input[value*="Untitled"], '
                '[contenteditable="true"]'
            )
            if title_elem:
                await title_elem.click()
                await asyncio.sleep(0.5)
                await self.page.keyboard.press('Control+a')
                await self.page.keyboard.type(new_title)
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(1)
        except Exception as e:
            print(f"  제목 변경 실패 (무시): {e}")

    async def add_source_via_search(self, search_query: str) -> bool:
        """웹 검색으로 소스 추가 (Fast Research) - 2026 UI"""
        try:
            # 왼쪽 패널의 검색창 찾기
            search_input = await self.page.query_selector(
                'input[placeholder*="웹에서 새 소스를 검색"]'
            )

            if not search_input:
                # 다른 placeholder로 시도
                search_input = await self.page.query_selector(
                    '[class*="search"] input, '
                    'input[placeholder*="검색"], '
                    'input[placeholder*="search"]'
                )

            if search_input:
                # 검색창 클릭 및 검색어 입력
                await search_input.click()
                await asyncio.sleep(0.5)
                await search_input.fill(search_query)
                await asyncio.sleep(1)

                # 검색 실행 (제출 버튼 또는 Enter)
                submit_btn = await self.page.query_selector(
                    'button[aria-label="제출"], '
                    'button[aria-label*="submit"], '
                    '[aria-label="제출"]'
                )
                if submit_btn:
                    await submit_btn.click()
                else:
                    await self.page.keyboard.press('Enter')

                # 검색 결과 대기 (Fast Research)
                print(f"  웹 검색 중: {search_query}")

                # 로딩 완료 대기 (최대 90초)
                for i in range(18):
                    await asyncio.sleep(5)
                    # 소스가 추가되었는지 확인 (왼쪽 패널)
                    source_items = await self.page.query_selector_all(
                        '[class*="source-item"], '
                        '[class*="source-card"], '
                        '[data-source], '
                        '.source-list-item'
                    )
                    if len(source_items) > 0:
                        print(f"  ✓ {len(source_items)}개 소스 추가됨")
                        return True

                    # 로딩 중인지 확인
                    loading = await self.page.query_selector('[class*="loading"], [class*="spinner"]')
                    if not loading and i > 6:
                        # 로딩 완료되었지만 소스가 없음
                        break

                print("  ⚠️ 소스 추가 타임아웃")
                return True  # 타임아웃이어도 계속 진행

        except Exception as e:
            print(f"  웹 검색 실패: {e}")

        return False

    async def open_notebook(self, notebook_id: str):
        """노트북 열기"""
        url = f"{self.base_url}/notebook/{notebook_id}"
        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)

    async def delete_notebook(self, notebook_id: str) -> bool:
        """노트북 삭제"""
        await self.open_notebook(notebook_id)
        await asyncio.sleep(2)

        # 설정/메뉴 버튼 찾기
        menu_btn = await self.page.query_selector(
            '[aria-label*="설정"], '
            '[aria-label*="Settings"], '
            '[aria-label*="More"], '
            'button[aria-haspopup="menu"]'
        )

        if menu_btn:
            await menu_btn.click()
            await asyncio.sleep(1)

            # 삭제 옵션 찾기
            delete_btn = await self.page.query_selector(
                '[role="menuitem"]:has-text("삭제"), '
                '[role="menuitem"]:has-text("Delete")'
            )

            if delete_btn:
                await delete_btn.click()
                await asyncio.sleep(1)

                # 확인 버튼
                confirm_btn = await self.page.query_selector(
                    'button:has-text("삭제"), '
                    'button:has-text("Delete"), '
                    'button:has-text("확인")'
                )

                if confirm_btn:
                    await confirm_btn.click()
                    await asyncio.sleep(2)
                    return True

        return False

    async def add_source_url(self, notebook_id: str, url: str) -> bool:
        """URL 소스 추가"""
        await self.open_notebook(notebook_id)
        await asyncio.sleep(2)

        # 소스 추가 버튼 찾기
        add_btn = await self.page.query_selector(
            'button:has-text("소스 추가"), '
            'button:has-text("Add source"), '
            '[aria-label*="Add source"]'
        )

        if add_btn:
            await add_btn.click()
            await asyncio.sleep(1)

            # URL 옵션 선택
            url_option = await self.page.query_selector(
                'button:has-text("웹사이트"), '
                'button:has-text("Website"), '
                'button:has-text("Link")'
            )

            if url_option:
                await url_option.click()
                await asyncio.sleep(1)

                # URL 입력
                url_input = await self.page.query_selector('input[type="url"], input[placeholder*="URL"]')
                if url_input:
                    await url_input.fill(url)
                    await asyncio.sleep(0.5)

                    # 확인 버튼
                    submit_btn = await self.page.query_selector('button[type="submit"], button:has-text("추가")')
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(3)
                        return True

        return False

    async def create_slides(self, notebook_id: str, language: str = "ko") -> bool:
        """슬라이드 생성 - 2026 UI"""
        await self.open_notebook(notebook_id)
        await asyncio.sleep(3)

        # 모달이 열려있으면 먼저 닫기
        await self._close_modal()
        await asyncio.sleep(2)

        print("  슬라이드 버튼 찾는 중...", end="")

        # locator로 "슬라이드 자료" 텍스트 찾기 (가장 신뢰성 높음)
        try:
            slide_locator = self.page.locator('text=슬라이드 자료')
            count = await slide_locator.count()
            if count > 0:
                print(f" 발견! ({count}개)")
                await slide_locator.first.click()
                await asyncio.sleep(3)
            else:
                print(" 미발견")
                await self.page.screenshot(path="G:/내 드라이브/notebooklm/debug_slides_fail.png")
                return False
        except Exception as e:
            print(f" 오류: {e}")
            await self.page.screenshot(path="G:/내 드라이브/notebooklm/debug_slides_fail.png")
            return False

        # 스크린샷 (디버깅용)
        await self.page.screenshot(path="G:/내 드라이브/notebooklm/debug_after_slide_click.png")

        # 언어 선택 및 생성 (모달이 열렸을 경우)
        if language == "ko":
            # 한국어 선택 시도
            lang_dropdown = await self.page.query_selector(
                'button:has-text("English"), '
                '[aria-label*="language"], '
                'select'
            )
            if lang_dropdown:
                await lang_dropdown.click()
                await asyncio.sleep(1)
                ko_option = await self.page.query_selector(
                    '[role="option"]:has-text("한국어"), '
                    'option:has-text("Korean"), '
                    'li:has-text("한국어")'
                )
                if ko_option:
                    await ko_option.click()
                    await asyncio.sleep(1)

        # 생성 버튼 클릭
        gen_btn = await self.page.query_selector(
            'button:has-text("생성"), '
            'button:has-text("Generate"), '
            'button:has-text("Create"), '
            'button[type="submit"]'
        )
        if gen_btn:
            await gen_btn.click()
            await asyncio.sleep(5)

        return True

    async def check_slides_ready(self, notebook_id: str) -> Tuple[bool, str]:
        """슬라이드 생성 상태 확인"""
        await self.open_notebook(notebook_id)
        await asyncio.sleep(3)

        # 스튜디오 패널 확인
        status_elem = await self.page.query_selector(
            '[class*="status"], '
            '[class*="progress"], '
            '[aria-label*="status"]'
        )

        if status_elem:
            status_text = await status_elem.inner_text()
            if '완료' in status_text or 'complete' in status_text.lower() or 'ready' in status_text.lower():
                return True, "completed"
            elif '진행' in status_text or 'progress' in status_text.lower() or 'generating' in status_text.lower():
                return False, "in_progress"
            elif '실패' in status_text or 'fail' in status_text.lower() or 'error' in status_text.lower():
                return False, "failed"

        # 다운로드 버튼이 있으면 완료된 것
        download_btn = await self.page.query_selector(
            'button:has-text("다운로드"), '
            'button:has-text("Download"), '
            '[aria-label*="download"]'
        )
        if download_btn:
            return True, "completed"

        return False, "unknown"

    async def wait_for_slides(self, notebook_id: str, timeout: int = None) -> bool:
        """슬라이드 생성 완료 대기"""
        max_wait = timeout or self.config.timeout_slides
        start = time.time()

        while time.time() - start < max_wait:
            ready, status = await self.check_slides_ready(notebook_id)

            if ready:
                print(f"  ✓ 슬라이드 생성 완료")
                return True
            elif status == "failed":
                print(f"  ❌ 슬라이드 생성 실패")
                return False

            elapsed = int(time.time() - start)
            print(f"\r  생성 중... {elapsed}초", end="", flush=True)
            await asyncio.sleep(10)

        print(f"\n  ⏰ 타임아웃 ({max_wait}초)")
        return False

    async def download_slides(self, notebook_id: str) -> Optional[Path]:
        """슬라이드 다운로드"""
        await self.open_notebook(notebook_id)
        await asyncio.sleep(5)

        # 다양한 다운로드 방법 시도
        methods = [
            self._download_via_menu,
            self._download_via_button,
            self._download_via_keyboard,
        ]

        for method in methods:
            result = await method()
            if result:
                return result

        return None

    async def _download_via_menu(self) -> Optional[Path]:
        """메뉴를 통한 다운로드"""
        menu_btns = await self.page.query_selector_all('[aria-haspopup="menu"], button[aria-label*="more"]')

        for menu_btn in menu_btns[-10:]:
            try:
                await menu_btn.click(force=True)
                await asyncio.sleep(1)

                dl_item = await self.page.query_selector(
                    '[role="menuitem"]:has-text("다운로드"), '
                    '[role="menuitem"]:has-text("Download")'
                )

                if dl_item:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"slides_{timestamp}.pdf"

                    async with self.page.expect_download(timeout=30000) as download_info:
                        await dl_item.click()

                    download = await download_info.value
                    downloaded_path = self.config.download_dir / filename
                    await download.save_as(str(downloaded_path))
                    return downloaded_path

                await self.page.keyboard.press('Escape')

            except Exception:
                try:
                    await self.page.keyboard.press('Escape')
                except:
                    pass

        return None

    async def _download_via_button(self) -> Optional[Path]:
        """다운로드 버튼 직접 클릭"""
        dl_btn = await self.page.query_selector(
            'button:has-text("다운로드"), '
            'button:has-text("Download"), '
            '[aria-label*="download"]'
        )

        if dl_btn:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"slides_{timestamp}.pdf"

            try:
                async with self.page.expect_download(timeout=30000) as download_info:
                    await dl_btn.click()

                download = await download_info.value
                downloaded_path = self.config.download_dir / filename
                await download.save_as(str(downloaded_path))
                return downloaded_path
            except:
                pass

        return None

    async def _download_via_keyboard(self) -> Optional[Path]:
        """키보드 단축키로 다운로드"""
        try:
            # Ctrl+S 시도
            await self.page.keyboard.press('Control+s')
            await asyncio.sleep(2)
            # 취소하고 다른 방법 시도
        except:
            pass

        return None

    async def screenshot(self, path: Path = None) -> Path:
        """스크린샷 저장"""
        if not path:
            path = self.config.download_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(path))
        return path


async def run_with_browser(callback):
    """브라우저 컨텍스트에서 콜백 실행"""
    async with NotebookLMBrowser() as browser:
        return await callback(browser)
