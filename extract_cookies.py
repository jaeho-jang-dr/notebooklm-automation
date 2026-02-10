#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""브라우저 프로필에서 쿠키 추출하여 nlm CLI 인증 설정"""
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

AUTH_DIR = Path.home() / ".notebooklm-mcp-cli"
PERSISTENT_PROFILE = AUTH_DIR / "persistent_browser"
PROFILE_DIR = AUTH_DIR / "profiles" / "default"


async def extract_and_save():
    from playwright.async_api import async_playwright

    print("브라우저 프로필에서 쿠키 추출 중...")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PERSISTENT_PROFILE),
            headless=True,
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # NotebookLM 방문하여 쿠키 활성화
        await page.goto("https://notebooklm.google.com/", timeout=30000)
        await asyncio.sleep(3)

        # 쿠키 추출
        cookies = await context.cookies()
        await context.close()

    # 쿠키를 딕셔너리로 변환
    cookies_dict = {}
    for cookie in cookies:
        if 'google.com' in cookie.get('domain', ''):
            cookies_dict[cookie['name']] = cookie['value']

    print(f"쿠키 {len(cookies_dict)}개 추출됨")

    if len(cookies_dict) < 10:
        print("⚠️ 쿠키가 부족합니다. 브라우저에서 로그인이 필요합니다.")
        return False

    # CSRF 토큰
    sapisid = cookies_dict.get('SAPISID', cookies_dict.get('__Secure-3PAPISID', ''))
    csrf_token = f"{sapisid[:16]}:{int(time.time() * 1000)}" if sapisid else ""

    # auth.json 저장
    auth_data = {
        "cookies": cookies_dict,
        "csrf_token": csrf_token,
        "session_id": "",
        "extracted_at": time.time(),
    }

    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with open(AUTH_DIR / "auth.json", 'w') as f:
        json.dump(auth_data, f, indent=2)

    # 프로필 디렉토리
    cookies_list = [
        {"name": n, "value": v, "domain": ".google.com", "path": "/",
         "expires": -1, "httpOnly": False, "secure": True, "sameSite": "Lax"}
        for n, v in cookies_dict.items()
    ]

    with open(PROFILE_DIR / "cookies.json", "w") as f:
        json.dump(cookies_list, f, indent=2)

    with open(PROFILE_DIR / "metadata.json", "w") as f:
        json.dump({
            "csrf_token": csrf_token,
            "last_validated": datetime.now().isoformat()
        }, f, indent=2)

    with open(PROFILE_DIR / "auth.json", "w") as f:
        json.dump(auth_data, f, indent=2)

    print(f"✓ 인증 저장 완료")
    print(f"  - {AUTH_DIR / 'auth.json'}")
    print(f"  - {PROFILE_DIR}")
    return True


if __name__ == "__main__":
    asyncio.run(extract_and_save())
