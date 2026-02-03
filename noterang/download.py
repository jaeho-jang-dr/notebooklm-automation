#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 다운로드 모듈
- 브라우저 기반 다운로드 (CLI 403 오류 우회)
- 다양한 다운로드 방법 지원
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .config import get_config


async def download_via_browser(
    notebook_id: str,
    output_dir: Path = None,
    artifact_type: str = "slides",
    timeout: int = 60
) -> Optional[Path]:
    """
    브라우저를 통한 다운로드 (CLI 버그 우회)

    Args:
        notebook_id: 노트북 ID
        output_dir: 출력 디렉토리
        artifact_type: "slides" 또는 "infographic"
        timeout: 다운로드 대기 시간 (초)

    Returns:
        다운로드된 파일 경로 또는 None
    """
    from playwright.async_api import async_playwright

    config = get_config()
    output_path = Path(output_dir) if output_dir else config.download_dir
    output_path.mkdir(parents=True, exist_ok=True)

    downloaded_path = None

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(config.browser_profile),
            headless=config.browser_headless,
            downloads_path=str(output_path),
            accept_downloads=True,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={
                'width': config.browser_viewport_width,
                'height': config.browser_viewport_height
            },
        )

        page = context.pages[0] if context.pages else await context.new_page()
        notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"

        try:
            await page.goto(notebook_url, wait_until='domcontentloaded', timeout=30000)
        except Exception as e:
            print(f"  페이지 로드 중... ({e})")

        # 페이지 로드 대기
        await asyncio.sleep(8)

        # 방법 1: aria-haspopup 메뉴 버튼 찾기
        downloaded_path = await _try_menu_download(page, output_path, artifact_type)

        # 방법 2: 좌표 기반 클릭 (백업)
        if not downloaded_path:
            downloaded_path = await _try_coordinate_download(page, output_path, artifact_type)

        # 방법 3: 파일 감시
        if not downloaded_path:
            downloaded_path = await _wait_for_new_file(output_path, timeout=30)

        await asyncio.sleep(2)
        await context.close()

    return downloaded_path


async def _try_menu_download(page, output_path: Path, artifact_type: str) -> Optional[Path]:
    """메뉴 버튼을 통한 다운로드 시도"""
    try:
        # 메뉴 버튼 찾기
        menu_btns = await page.query_selector_all('[aria-haspopup="menu"], button[aria-label*="more"], button[aria-label*="More"]')

        for menu_btn in menu_btns[-10:]:  # 마지막 10개 시도
            try:
                await menu_btn.click(force=True)
                await asyncio.sleep(1)

                # 다운로드 메뉴 아이템 찾기 (한글/영어)
                dl_item = await page.query_selector(
                    '[role="menuitem"]:has-text("다운로드"), '
                    '[role="menuitem"]:has-text("Download"), '
                    '[role="menuitem"]:has-text("download")'
                )

                if dl_item:
                    # 다운로드 이벤트 대기
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{artifact_type}_{timestamp}.pdf"

                    async with page.expect_download(timeout=30000) as download_info:
                        await dl_item.click()

                    download = await download_info.value
                    downloaded_path = output_path / filename
                    await download.save_as(str(downloaded_path))
                    print(f"  ✓ 다운로드 완료: {filename}")
                    return downloaded_path

                # 메뉴 닫기
                await page.keyboard.press('Escape')

            except Exception as e:
                try:
                    await page.keyboard.press('Escape')
                except:
                    pass
                continue

    except Exception as e:
        print(f"  메뉴 다운로드 실패: {e}")

    return None


async def _try_coordinate_download(page, output_path: Path, artifact_type: str) -> Optional[Path]:
    """좌표 기반 다운로드 시도 (백업 방법)"""
    config = get_config()

    # 스튜디오 패널의 더보기 버튼 좌표 (1920x1080 기준)
    # 화면 비율에 따라 조정
    ratio_x = config.browser_viewport_width / 1920
    ratio_y = config.browser_viewport_height / 1080

    coordinates = [
        (int(1846 * ratio_x), int(365 * ratio_y)),  # 스튜디오 패널 more 버튼
        (int(1800 * ratio_x), int(350 * ratio_y)),  # 대체 위치
    ]

    for x, y in coordinates:
        try:
            await page.mouse.click(x, y)
            await asyncio.sleep(1)

            dl_item = await page.query_selector(
                '[role="menuitem"]:has-text("다운로드"), '
                '[role="menuitem"]:has-text("Download")'
            )

            if dl_item:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{artifact_type}_{timestamp}.pdf"

                async with page.expect_download(timeout=30000) as download_info:
                    await dl_item.click()

                download = await download_info.value
                downloaded_path = output_path / filename
                await download.save_as(str(downloaded_path))
                print(f"  ✓ 좌표 클릭으로 다운로드: {filename}")
                return downloaded_path

            await page.keyboard.press('Escape')

        except Exception:
            try:
                await page.keyboard.press('Escape')
            except:
                pass
            continue

    return None


async def _wait_for_new_file(output_path: Path, timeout: int = 30) -> Optional[Path]:
    """새 파일이 생성될 때까지 대기"""
    import time

    # 기존 파일 목록
    before_files = set(output_path.glob("*.pdf"))
    start_time = time.time()

    print("  파일 생성 대기 중...")

    while time.time() - start_time < timeout:
        current_files = set(output_path.glob("*.pdf"))
        new_files = current_files - before_files

        if new_files:
            new_file = max(new_files, key=lambda f: f.stat().st_mtime)
            print(f"  ✓ 새 파일 감지: {new_file.name}")
            return new_file

        await asyncio.sleep(2)

    return None


async def download_with_retries(
    notebook_id: str,
    output_dir: Path = None,
    artifact_type: str = "slides",
    max_retries: int = 3
) -> Optional[Path]:
    """
    재시도를 포함한 다운로드

    Args:
        notebook_id: 노트북 ID
        output_dir: 출력 디렉토리
        artifact_type: 아티팩트 타입
        max_retries: 최대 재시도 횟수

    Returns:
        다운로드된 파일 경로 또는 None
    """
    for attempt in range(max_retries):
        print(f"\n  다운로드 시도 {attempt + 1}/{max_retries}...")

        result = await download_via_browser(
            notebook_id,
            output_dir,
            artifact_type
        )

        if result:
            return result

        if attempt < max_retries - 1:
            print(f"  실패 - {5}초 후 재시도...")
            await asyncio.sleep(5)

    print("  ❌ 모든 다운로드 시도 실패")
    return None


async def take_screenshot(notebook_id: str, output_path: Path = None) -> Optional[Path]:
    """디버그용 스크린샷 촬영"""
    from playwright.async_api import async_playwright

    config = get_config()

    if not config.save_screenshots:
        return None

    screenshot_path = output_path or (config.download_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(config.browser_profile),
            headless=True,
            viewport={'width': config.browser_viewport_width, 'height': config.browser_viewport_height},
        )

        page = context.pages[0] if context.pages else await context.new_page()
        notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"

        try:
            await page.goto(notebook_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)
            await page.screenshot(path=str(screenshot_path))
            print(f"  스크린샷 저장: {screenshot_path}")
        except Exception as e:
            print(f"  스크린샷 실패: {e}")
            screenshot_path = None

        await context.close()

    return screenshot_path


# 동기 버전
def download_sync(notebook_id: str, output_dir: Path = None, artifact_type: str = "slides") -> Optional[Path]:
    """동기 다운로드"""
    return asyncio.run(download_via_browser(notebook_id, output_dir, artifact_type))
