#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 자동 로그인 - 사용자 개입 없이 인증 갱신
공식 notebooklm-mcp-auth 도구를 사용하거나 Playwright로 쿠키 추출
"""
import asyncio
import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

AUTH_DIR = Path.home() / ".notebooklm-mcp-cli"
BROWSER_PROFILE = AUTH_DIR / "browser_profile"
ROOT_AUTH = AUTH_DIR / "auth.json"
PROFILE_DIR = AUTH_DIR / "profiles" / "default"
NLM_AUTH_EXE = Path.home() / "AppData/Roaming/Python/Python313/Scripts/notebooklm-mcp-auth.exe"


def run_official_auth(timeout: int = 120) -> bool:
    """
    공식 notebooklm-mcp-auth 도구 실행
    Chrome 브라우저 프로필을 사용하여 자동 인증
    """
    if not NLM_AUTH_EXE.exists():
        print(f"  ❌ 공식 인증 도구 없음: {NLM_AUTH_EXE}")
        return False

    print("  공식 인증 도구 실행...")

    try:
        result = subprocess.run(
            [str(NLM_AUTH_EXE)],
            capture_output=True,
            timeout=timeout,
            text=True
        )

        if "SUCCESS" in result.stdout:
            print("  ✓ 공식 도구 인증 성공")
            return True
        else:
            print(f"  ⚠️ 인증 결과 불확실")
            return "Cookies:" in result.stdout

    except subprocess.TimeoutExpired:
        print("  ⚠️ 인증 타임아웃")
        return False
    except Exception as e:
        print(f"  ❌ 인증 오류: {e}")
        return False


async def auto_login(headless: bool = True, timeout: int = 60) -> bool:
    """
    자동 로그인 - 브라우저 프로필의 저장된 세션 사용

    Args:
        headless: True면 백그라운드 실행, False면 브라우저 표시
        timeout: 최대 대기 시간 (초)

    Returns:
        성공 여부
    """
    from playwright.async_api import async_playwright

    print("=" * 50)
    print("NotebookLM 자동 로그인")
    print("=" * 50)

    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # 저장된 프로필로 브라우저 실행
        print(f"\n[1/4] 브라우저 시작 (headless={headless})...")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-first-run',
                '--no-default-browser-check',
            ],
            ignore_default_args=['--enable-automation'],
            viewport={'width': 1280, 'height': 800} if headless else None,
            no_viewport=not headless,
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # NotebookLM으로 이동
        print("[2/4] NotebookLM 접속...")
        try:
            await page.goto(
                "https://notebooklm.google.com",
                wait_until='domcontentloaded',
                timeout=30000
            )
        except Exception as e:
            print(f"  페이지 로드 중... ({e})")

        await asyncio.sleep(3)

        # 로그인 상태 확인 및 대기
        print("[3/4] 로그인 상태 확인...")

        logged_in = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            url = page.url

            # 로그인 페이지로 리다이렉트 되었는지 확인
            if 'accounts.google.com' in url:
                if headless:
                    print("  ⚠️ 로그인 필요 - headless 모드에서 불가")
                    print("  → headless=False로 재시도하거나 수동 로그인 필요")
                    await context.close()
                    return False
                else:
                    print("  로그인 페이지 감지 - 대기 중...")
                    await asyncio.sleep(5)
                    continue

            # NotebookLM 메인 페이지에 있는지 확인
            if 'notebooklm.google.com' in url and 'accounts.google' not in url:
                # 쿠키 확인
                cookies = await context.cookies()
                google_cookies = [c for c in cookies if 'google.com' in c.get('domain', '')]

                # 중요 쿠키 존재 확인
                cookie_names = {c['name'] for c in google_cookies}
                has_sid = 'SID' in cookie_names
                has_psid = '__Secure-1PSID' in cookie_names or '__Secure-3PSID' in cookie_names

                if has_sid and has_psid and len(google_cookies) > 10:
                    logged_in = True
                    print(f"  ✓ 로그인 확인 (쿠키 {len(google_cookies)}개)")
                    break

            await asyncio.sleep(2)
            elapsed = int(time.time() - start_time)
            print(f"\r  확인 중... {elapsed}초", end="", flush=True)

        if not logged_in:
            print("\n  ❌ 로그인 실패 또는 타임아웃")
            await context.close()
            return False

        # 쿠키 추출 및 저장
        print("\n[4/4] 인증 정보 저장...")

        cookies = await context.cookies()

        # 쿠키를 딕셔너리로 변환
        cookies_dict = {}
        for cookie in cookies:
            if 'google.com' in cookie.get('domain', ''):
                cookies_dict[cookie['name']] = cookie['value']

        # CSRF 토큰 생성
        sapisid = cookies_dict.get('SAPISID', cookies_dict.get('__Secure-3PAPISID', ''))
        csrf_token = f"{sapisid[:16]}:{int(time.time() * 1000)}" if sapisid else ""

        # 세션 ID 추출 (URL에서)
        session_id = ""
        current_url = page.url
        if '/notebook/' in current_url:
            parts = current_url.split('/notebook/')
            if len(parts) > 1:
                session_id = parts[1].split('/')[0].split('?')[0]

        # 루트 auth.json 저장
        auth_data = {
            "cookies": cookies_dict,
            "csrf_token": csrf_token,
            "session_id": session_id,
            "extracted_at": time.time(),
            "auto_login": True
        }

        with open(ROOT_AUTH, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2)

        # 프로필 디렉토리에 동기화
        sync_to_profile(auth_data)

        print(f"  ✓ 저장 완료")
        print(f"    쿠키: {len(cookies_dict)}개")
        print(f"    파일: {ROOT_AUTH}")

        await context.close()

    print("\n" + "=" * 50)
    print("자동 로그인 완료!")
    print("=" * 50)

    return True


def sync_to_profile(auth_data: dict):
    """프로필 디렉토리에 인증 정보 동기화"""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # cookies.json (리스트 형식)
    cookies_list = [
        {
            "name": name,
            "value": value,
            "domain": ".google.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        }
        for name, value in auth_data.get('cookies', {}).items()
    ]

    with open(PROFILE_DIR / "cookies.json", "w") as f:
        json.dump(cookies_list, f, indent=2)

    # metadata.json
    with open(PROFILE_DIR / "metadata.json", "w") as f:
        json.dump({
            "csrf_token": auth_data.get("csrf_token", ""),
            "session_id": auth_data.get("session_id", ""),
            "email": "",
            "last_validated": datetime.now().isoformat()
        }, f, indent=2)

    # auth.json
    with open(PROFILE_DIR / "auth.json", "w") as f:
        json.dump(auth_data, f, indent=2)


async def ensure_logged_in() -> bool:
    """
    로그인 상태 확인 및 필요시 자동 로그인
    1. 공식 도구 시도 (Chrome 프로필 사용)
    2. 실패시 Playwright headless
    3. 실패시 Playwright 브라우저 표시

    Returns:
        로그인 성공 여부
    """
    # 1. 공식 도구로 시도 (가장 안정적)
    print("자동 로그인 시도...")
    if run_official_auth(timeout=60):
        sync_to_profile_from_root()
        return True

    # 2. Playwright headless로 시도
    print("\n공식 도구 실패. Playwright로 재시도...")
    if await auto_login(headless=True, timeout=30):
        return True

    # 3. 브라우저 표시하여 재시도
    print("\n백그라운드 실패. 브라우저로 재시도...")
    return await auto_login(headless=False, timeout=120)


def sync_to_profile_from_root():
    """루트 auth.json을 프로필 디렉토리에 동기화"""
    if not ROOT_AUTH.exists():
        return False

    with open(ROOT_AUTH) as f:
        auth_data = json.load(f)

    sync_to_profile(auth_data)
    return True


def run_auto_login(headless: bool = True) -> bool:
    """동기 버전"""
    return asyncio.run(auto_login(headless=headless))


def run_ensure_logged_in() -> bool:
    """동기 버전"""
    return asyncio.run(ensure_logged_in())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='NotebookLM 자동 로그인')
    parser.add_argument('--show', action='store_true', help='브라우저 표시')
    args = parser.parse_args()

    success = run_auto_login(headless=not args.show)

    if success:
        print("\n✓ 인증 성공!")
    else:
        print("\n❌ 인증 실패")
        sys.exit(1)
