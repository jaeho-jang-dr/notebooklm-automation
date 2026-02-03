#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM 인증 동기화
notebooklm-mcp-auth 실행 후 자동으로 프로필 디렉토리에 동기화
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

AUTH_DIR = Path.home() / ".notebooklm-mcp-cli"
ROOT_AUTH = AUTH_DIR / "auth.json"
PROFILE_DIR = AUTH_DIR / "profiles" / "default"

def sync_auth():
    """루트 auth.json을 프로필 디렉토리에 동기화"""
    if not ROOT_AUTH.exists():
        print("❌ 루트 auth.json 없음")
        return False

    with open(ROOT_AUTH) as f:
        root_data = json.load(f)

    # cookies.json (리스트 형식으로 변환)
    cookies_dict = root_data.get('cookies', {})
    cookies_list = []
    for name, value in cookies_dict.items():
        cookies_list.append({
            "name": name,
            "value": value,
            "domain": ".google.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        })

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # cookies.json
    with open(PROFILE_DIR / "cookies.json", "w") as f:
        json.dump(cookies_list, f, indent=2)

    # metadata.json
    metadata = {
        "csrf_token": root_data.get("csrf_token", ""),
        "session_id": root_data.get("session_id", ""),
        "email": root_data.get("email", ""),
        "last_validated": datetime.now().isoformat()
    }
    with open(PROFILE_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # auth.json
    with open(PROFILE_DIR / "auth.json", "w") as f:
        json.dump(root_data, f, indent=2)

    print(f"✓ 프로필 동기화 완료")
    print(f"  쿠키: {len(cookies_list)}개")
    print(f"  세션: {root_data.get('session_id', 'N/A')[:20]}...")
    return True

def run_auth_and_sync():
    """인증 실행 후 동기화"""
    print("=" * 50)
    print("NotebookLM 인증 및 동기화")
    print("=" * 50)

    # notebooklm-mcp-auth 실행
    auth_exe = Path.home() / "AppData/Roaming/Python/Python313/Scripts/notebooklm-mcp-auth.exe"
    if not auth_exe.exists():
        # pip로 설치된 경우 다른 경로 시도
        auth_exe = "notebooklm-mcp-auth"

    print("\n1. 인증 실행 중...")
    try:
        result = subprocess.run(
            [str(auth_exe)],
            capture_output=False,
            timeout=300
        )
        if result.returncode != 0:
            print("⚠️ 인증 실행 오류")
    except Exception as e:
        print(f"⚠️ 인증 실행 실패: {e}")

    # 동기화
    print("\n2. 프로필 동기화 중...")
    sync_auth()

    # 테스트
    print("\n3. 인증 테스트...")
    nlm_exe = Path.home() / "AppData/Roaming/Python/Python313/Scripts/nlm.exe"
    try:
        result = subprocess.run(
            [str(nlm_exe), "login", "--check"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if "valid" in result.stdout.lower():
            print("✓ 인증 유효!")
        else:
            print(f"⚠️ 인증 상태: {result.stdout[:100]}")
    except Exception as e:
        print(f"테스트 실패: {e}")

    print("\n" + "=" * 50)
    print("완료!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sync-only":
        sync_auth()
    else:
        run_auth_and_sync()
