#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 완전 자동 로그인 모듈
- Google 2FA TOTP 자동 생성
- 브라우저 자동화로 NotebookLM 로그인
"""
import asyncio
import os
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import pyotp
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# .env.local 파일 로드
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

# 인증 정보 (환경 변수에서 로드)
EMAIL = os.getenv('GOOGLE_EMAIL', '')
PASSWORD = os.getenv('GOOGLE_PASSWORD', '')
TOTP_SECRET = os.getenv('GOOGLE_2FA_SECRET', '')
APP_PASSWORD = os.getenv('NOTEBOOKLM_APP_PASSWORD', '')
APIFY_API_KEY = os.getenv('APIFY_API_KEY', '')

# 브라우저 프로필 경로
BROWSER_PROFILE = Path.home() / '.notebooklm-auto-v3'


def get_totp_code() -> str:
    """현재 TOTP 코드 생성"""
    totp = pyotp.TOTP(TOTP_SECRET.upper())
    return totp.now()


async def full_auto_login(headless: bool = False) -> bool:
    """
    완전 자동 로그인

    Args:
        headless: True면 백그라운드 실행

    Returns:
        로그인 성공 여부
    """
    print("=" * 50)
    print("NotebookLM 완전 자동 로그인")
    print("=" * 50)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ],
            viewport={'width': 1280, 'height': 900},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # 1. NotebookLM 접속
        print("\n[1/4] NotebookLM 접속...")
        await page.goto('https://notebooklm.google.com/', timeout=60000)
        await asyncio.sleep(3)

        # 이미 로그인된 경우
        if 'notebooklm.google.com' in page.url and 'accounts' not in page.url:
            print("  ✓ 이미 로그인되어 있습니다.")
            await context.close()
            return True

        # 2. 이메일 입력
        if 'accounts.google.com' in page.url:
            print("[2/4] 이메일 입력...")
            try:
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                await page.fill('input[type="email"]', EMAIL)
                await page.click('#identifierNext')
                await asyncio.sleep(4)
                print("  ✓ 이메일 입력 완료")
            except Exception as e:
                print(f"  ❌ 이메일 입력 실패: {e}")
                await context.close()
                return False

        # 3. 비밀번호 입력
        print("[3/4] 비밀번호 입력...")
        try:
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('#passwordNext')
            await asyncio.sleep(4)
            print("  ✓ 비밀번호 입력 완료")
        except Exception as e:
            print(f"  ❌ 비밀번호 입력 실패: {e}")
            await context.close()
            return False

        # 4. 2FA TOTP 입력
        print("[4/4] 2FA 코드 입력...")
        try:
            await asyncio.sleep(2)

            # 먼저 TOTP 입력 필드가 있는지 확인
            totp_input = await page.query_selector(
                'input[name="totpPin"], input[type="tel"][autocomplete="one-time-code"], input[id="totpPin"]'
            )

            # TOTP 필드가 없으면 "다른 방법 시도" 클릭
            if not totp_input:
                print("  Push 알림 방식 감지, OTP 방식으로 전환...")

                # "다른 방법 시도" 클릭 - 텍스트로 직접 찾기
                try:
                    await page.click('text=다른 방법 시도', timeout=5000)
                    await asyncio.sleep(2)
                    print("  ✓ 다른 방법 시도 클릭")
                except:
                    try:
                        await page.click('text=Try another way', timeout=3000)
                        await asyncio.sleep(2)
                    except:
                        pass

                # OTP/Authenticator 앱 옵션 선택
                try:
                    # Google OTP 앱 옵션 찾기
                    otp_options = [
                        'text=Google OTP',
                        'text=Authenticator',
                        'text=인증 앱',
                        'text=OTP 앱',
                        '[data-challengetype="6"]',  # TOTP
                        '[data-challengetype="5"]',
                    ]
                    for selector in otp_options:
                        try:
                            await page.click(selector, timeout=2000)
                            print(f"  ✓ OTP 방식 선택: {selector}")
                            await asyncio.sleep(3)
                            break
                        except:
                            continue
                except Exception as e:
                    print(f"  OTP 옵션 선택 실패: {e}")

                # 다시 TOTP 필드 찾기
                try:
                    totp_input = await page.wait_for_selector(
                        'input[name="totpPin"], input[type="tel"], input[id="totpPin"], input[autocomplete="one-time-code"]',
                        timeout=10000
                    )
                except:
                    pass

            if totp_input:
                # TOTP 코드 생성
                code = get_totp_code()
                print(f"  생성된 코드: {code}")

                await totp_input.fill(code)
                await asyncio.sleep(1)

                # 다음 버튼 클릭
                next_btn = await page.query_selector(
                    '#totpNext, button:has-text("다음"), button:has-text("Next")'
                )
                if next_btn:
                    await next_btn.click()
                    await asyncio.sleep(5)
                    print("  ✓ 2FA 코드 입력 완료")
            else:
                print("  ⚠️ TOTP 입력 필드를 찾지 못함")

        except Exception as e:
            print(f"  2FA 입력 건너뜀 (이미 인증됨 또는 불필요): {e}")

        # 로그인 결과 확인
        print("\n로그인 결과 확인...")
        for i in range(10):
            await asyncio.sleep(2)
            if 'notebooklm.google.com' in page.url and 'accounts' not in page.url:
                print("✓ 로그인 성공!")
                await context.close()
                return True
            print(f"  대기 중... {(i+1)*2}초")

        print("❌ 로그인 실패")
        await page.screenshot(path='login_failed.png')
        await context.close()
        return False


async def login_and_get_context():
    """
    로그인 후 브라우저 컨텍스트 반환 (다른 작업용)
    """
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            viewport={'width': 1280, 'height': 900},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto('https://notebooklm.google.com/', timeout=60000)
        await asyncio.sleep(3)

        # 로그인 필요시
        if 'accounts.google.com' in page.url:
            success = await full_auto_login(headless=False)
            if not success:
                await context.close()
                return None, None

            # 다시 컨텍스트 열기
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE),
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                viewport={'width': 1280, 'height': 900},
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto('https://notebooklm.google.com/', timeout=60000)
            await asyncio.sleep(3)

        return context, page


# CLI 실행
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='NotebookLM 자동 로그인')
    parser.add_argument('--headless', action='store_true', help='백그라운드 실행')
    parser.add_argument('--test-totp', action='store_true', help='TOTP 코드만 테스트')
    args = parser.parse_args()

    if args.test_totp:
        print(f"현재 TOTP 코드: {get_totp_code()}")
    else:
        result = asyncio.run(full_auto_login(headless=args.headless))
        print(f"\n결과: {'성공' if result else '실패'}")
