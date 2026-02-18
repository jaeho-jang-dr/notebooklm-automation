#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 완전 자동 로그인 모듈
- Google 2FA TOTP 자동 생성
- 브라우저 자동화로 NotebookLM 로그인
"""
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import pyotp
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

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
    if not TOTP_SECRET:
        raise ValueError(
            "GOOGLE_2FA_SECRET 환경 변수가 설정되지 않았습니다. "
            ".env.local 파일을 확인하세요."
        )
    try:
        totp = pyotp.TOTP(TOTP_SECRET.upper())
        code = totp.now()
        if not code or len(code) != 6:
            raise ValueError(f"유효하지 않은 TOTP 코드 생성됨: '{code}'")
        return code
    except Exception as e:
        raise RuntimeError(f"TOTP 코드 생성 실패: {e}") from e


_LOCKOUT_INDICATORS = [
    "계정이 일시적으로 사용 중지",
    "too many failed attempts",
    "account has been disabled",
    "suspicious activity",
    "verify it's you",
    "계정을 확인해야",
]


def _check_credentials() -> None:
    """필수 인증 정보가 설정되어 있는지 검증"""
    missing = []
    if not EMAIL:
        missing.append("GOOGLE_EMAIL")
    if not PASSWORD:
        missing.append("GOOGLE_PASSWORD")
    if not TOTP_SECRET:
        missing.append("GOOGLE_2FA_SECRET")
    if missing:
        raise ValueError(
            f"필수 환경 변수 누락: {', '.join(missing)}. "
            ".env.local 파일을 확인하세요."
        )


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

    try:
        _check_credentials()
    except ValueError as e:
        print(f"  ❌ 인증 정보 오류: {e}")
        return False

    context = None
    try:
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(BROWSER_PROFILE),
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                    ],
                    viewport={'width': 1280, 'height': 900},
                )
            except PlaywrightError as e:
                print(f"  ❌ 브라우저 시작 실패: {e}")
                logger.error("Browser launch failed", exc_info=True)
                return False

            page = context.pages[0] if context.pages else await context.new_page()

            # Handle page crash gracefully
            page.on("crash", lambda: logger.error("Page crashed during login"))

            # 1. NotebookLM 접속
            print("\n[1/4] NotebookLM 접속...")
            try:
                await page.goto('https://notebooklm.google.com/', timeout=60000)
                await asyncio.sleep(3)
            except PlaywrightTimeoutError:
                print("  ❌ NotebookLM 접속 타임아웃 (60초). 네트워크를 확인하세요.")
                await _save_debug_screenshot(page, "login_step1_timeout")
                await context.close()
                return False
            except PlaywrightError as e:
                print(f"  ❌ NotebookLM 접속 실패: {e}")
                await context.close()
                return False

            # 이미 로그인된 경우
            if 'notebooklm.google.com' in page.url and 'accounts' not in page.url:
                print("  ✓ 이미 로그인되어 있습니다.")
                await context.close()
                return True

            # 계정 잠금 감지
            page_text = await page.inner_text('body').call if False else ""
            try:
                page_text = await page.inner_text('body')
            except PlaywrightError:
                page_text = ""

            if any(indicator.lower() in page_text.lower() for indicator in _LOCKOUT_INDICATORS):
                print("  ❌ 계정 잠금 또는 비정상 활동 감지. Google 계정을 직접 확인하세요.")
                await _save_debug_screenshot(page, "login_lockout_detected")
                await context.close()
                return False

            # 2. 이메일 입력
            if 'accounts.google.com' in page.url:
                print("[2/4] 이메일 입력...")
                try:
                    await page.wait_for_selector('input[type="email"]', timeout=10000)
                    await page.fill('input[type="email"]', EMAIL)
                    await page.click('#identifierNext')
                    await asyncio.sleep(4)
                    print("  ✓ 이메일 입력 완료")
                except PlaywrightTimeoutError:
                    print("  ❌ 이메일 입력 필드를 찾을 수 없습니다 (타임아웃). 로그인 페이지 구조가 변경되었을 수 있습니다.")
                    await _save_debug_screenshot(page, "login_step2_timeout")
                    await context.close()
                    return False
                except PlaywrightError as e:
                    print(f"  ❌ 이메일 입력 실패 (브라우저 오류): {e}")
                    await _save_debug_screenshot(page, "login_step2_error")
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
            except PlaywrightTimeoutError:
                print("  ❌ 비밀번호 입력 필드를 찾을 수 없습니다 (타임아웃). 이메일 주소가 올바른지 확인하세요.")
                await _save_debug_screenshot(page, "login_step3_timeout")
                await context.close()
                return False
            except PlaywrightError as e:
                print(f"  ❌ 비밀번호 입력 실패 (브라우저 오류): {e}")
                await _save_debug_screenshot(page, "login_step3_error")
                await context.close()
                return False

            # 비밀번호 오류 감지 (잘못된 비밀번호)
            await asyncio.sleep(1)
            try:
                wrong_pw_indicators = [
                    '[jsname="B34EJ"]:visible',  # Google 오류 메시지 컨테이너
                    '[aria-live="assertive"]:visible',
                ]
                for sel in wrong_pw_indicators:
                    err_elem = await page.query_selector(sel)
                    if err_elem:
                        err_text = await err_elem.inner_text()
                        if err_text.strip():
                            print(f"  ❌ Google 로그인 오류: {err_text.strip()[:100]}")
                            await _save_debug_screenshot(page, "login_wrong_password")
                            await context.close()
                            return False
            except PlaywrightError:
                pass

            # 4. 2FA TOTP 입력 (최대 2회 재시도)
            print("[4/4] 2FA 코드 입력...")
            totp_success = await _handle_totp(page)
            if not totp_success:
                # 2FA 실패해도 로그인 성공일 수 있으므로 계속 진행
                logger.warning("TOTP step did not confirm success; checking login state anyway")

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
            await _save_debug_screenshot(page, "login_failed")
            await context.close()
            return False

    except Exception as e:
        logger.error(f"Unexpected error during full_auto_login: {e}", exc_info=True)
        print(f"  ❌ 예기치 않은 오류: {e}")
        return False


async def _save_debug_screenshot(page, name: str) -> None:
    """오류 디버깅용 스크린샷 저장"""
    try:
        path = f"{name}_{int(time.time())}.png"
        await page.screenshot(path=path)
        print(f"  스크린샷 저장: {path}")
    except PlaywrightError as e:
        logger.warning(f"Screenshot failed for '{name}': {e}")


async def _handle_totp(page, max_attempts: int = 2) -> bool:
    """
    TOTP 2FA 처리 (재시도 포함)

    Args:
        page: Playwright 페이지
        max_attempts: 최대 시도 횟수 (Google은 재입력 허용)

    Returns:
        TOTP 입력 성공 여부
    """
    try:
        await asyncio.sleep(2)

        # 먼저 TOTP 입력 필드가 있는지 확인
        totp_input = await page.query_selector(
            'input[name="totpPin"], input[type="tel"][autocomplete="one-time-code"], input[id="totpPin"]'
        )

        # TOTP 필드가 없으면 "다른 방법 시도" 클릭
        if not totp_input:
            print("  Push 알림 방식 감지, OTP 방식으로 전환...")

            # "다른 방법 시도" 클릭
            switched = False
            for text_selector in ['text=다른 방법 시도', 'text=Try another way']:
                try:
                    await page.click(text_selector, timeout=5000)
                    await asyncio.sleep(2)
                    print(f"  ✓ 다른 방법 시도 클릭 ({text_selector})")
                    switched = True
                    break
                except PlaywrightTimeoutError:
                    continue
                except PlaywrightError as e:
                    logger.debug(f"Try another way click failed ({text_selector}): {e}")

            if not switched:
                logger.warning("Could not click 'Try another way'; proceeding anyway")

            # OTP/Authenticator 앱 옵션 선택
            otp_options = [
                'text=Google OTP',
                'text=Authenticator',
                'text=인증 앱',
                'text=OTP 앱',
                '[data-challengetype="6"]',
                '[data-challengetype="5"]',
            ]
            for selector in otp_options:
                try:
                    await page.click(selector, timeout=2000)
                    print(f"  ✓ OTP 방식 선택: {selector}")
                    await asyncio.sleep(3)
                    break
                except (PlaywrightTimeoutError, PlaywrightError):
                    continue

            # 다시 TOTP 필드 찾기
            try:
                totp_input = await page.wait_for_selector(
                    'input[name="totpPin"], input[type="tel"], input[id="totpPin"], input[autocomplete="one-time-code"]',
                    timeout=10000
                )
            except PlaywrightTimeoutError:
                print("  ⚠️ TOTP 입력 필드를 찾을 수 없습니다 (10초 타임아웃)")
                await _save_debug_screenshot(page, "login_totp_field_missing")
                return False

        if not totp_input:
            print("  ⚠️ TOTP 입력 필드를 찾지 못함")
            return False

        # TOTP 코드 생성 및 입력 (최대 max_attempts회)
        for attempt in range(1, max_attempts + 1):
            try:
                # TOTP 코드가 곧 만료되면 다음 코드로 갱신 (타이밍 경쟁 조건 방지)
                remaining = 30 - (int(time.time()) % 30)
                if remaining <= 3:
                    print(f"  ⏳ TOTP 코드 갱신 대기 ({remaining}초)...")
                    await asyncio.sleep(remaining + 1)
                code = get_totp_code()
                print(f"  생성된 코드: {code} (시도 {attempt}/{max_attempts})")
            except RuntimeError as e:
                print(f"  ❌ TOTP 코드 생성 실패: {e}")
                return False

            try:
                await totp_input.fill(code)
                await asyncio.sleep(1)
            except PlaywrightError as e:
                print(f"  ❌ TOTP 코드 입력 실패 (브라우저 오류): {e}")
                return False

            # 다음 버튼 클릭
            next_btn = await page.query_selector(
                '#totpNext, button:has-text("다음"), button:has-text("Next")'
            )
            if next_btn:
                try:
                    await next_btn.click()
                    await asyncio.sleep(5)
                except PlaywrightError as e:
                    print(f"  ❌ 다음 버튼 클릭 실패: {e}")
                    return False

            # 오류 메시지 확인 (잘못된 OTP)
            await asyncio.sleep(1)
            try:
                otp_error = await page.query_selector(
                    '[jsname="B34EJ"]:visible, [aria-live="assertive"]:visible'
                )
                if otp_error:
                    err_text = await otp_error.inner_text()
                    if err_text.strip() and attempt < max_attempts:
                        print(f"  ⚠️ OTP 오류: {err_text.strip()[:80]}. 재시도 중...")
                        await asyncio.sleep(2)
                        # 필드를 다시 찾아서 재입력
                        try:
                            totp_input = await page.wait_for_selector(
                                'input[name="totpPin"], input[type="tel"], input[id="totpPin"]',
                                timeout=5000
                            )
                        except PlaywrightTimeoutError:
                            print("  ❌ 재입력 필드를 찾을 수 없습니다")
                            return False
                        continue
                    elif err_text.strip():
                        print(f"  ❌ OTP 최대 시도 초과: {err_text.strip()[:80]}")
                        await _save_debug_screenshot(page, "login_totp_failed")
                        return False
            except PlaywrightError:
                pass

            print("  ✓ 2FA 코드 입력 완료")
            return True

        return False

    except PlaywrightError as e:
        print(f"  ❌ 2FA 처리 중 브라우저 오류: {e}")
        logger.error("TOTP handling failed", exc_info=True)
        return False
    except Exception as e:
        print(f"  2FA 입력 건너뜀 (이미 인증됨 또는 불필요): {e}")
        return False


async def login_and_get_context():
    """
    로그인 후 브라우저 컨텍스트 반환 (다른 작업용)
    """
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE),
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                viewport={'width': 1280, 'height': 900},
            )
        except PlaywrightError as e:
            print(f"  ❌ 브라우저 시작 실패: {e}")
            logger.error("Browser launch failed in login_and_get_context", exc_info=True)
            return None, None

        page = context.pages[0] if context.pages else await context.new_page()

        try:
            await page.goto('https://notebooklm.google.com/', timeout=60000)
            await asyncio.sleep(3)
        except PlaywrightTimeoutError:
            print("  ❌ NotebookLM 접속 타임아웃. 네트워크를 확인하세요.")
            await context.close()
            return None, None
        except PlaywrightError as e:
            print(f"  ❌ 페이지 로드 실패: {e}")
            await context.close()
            return None, None

        # 로그인 필요시
        if 'accounts.google.com' in page.url:
            success = await full_auto_login(headless=False)
            if not success:
                await context.close()
                return None, None

            # 다시 컨텍스트 열기
            try:
                await context.close()
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(BROWSER_PROFILE),
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled'],
                    viewport={'width': 1280, 'height': 900},
                )
            except PlaywrightError as e:
                print(f"  ❌ 브라우저 재시작 실패: {e}")
                return None, None

            page = context.pages[0] if context.pages else await context.new_page()
            try:
                await page.goto('https://notebooklm.google.com/', timeout=60000)
                await asyncio.sleep(3)
            except PlaywrightTimeoutError:
                print("  ❌ 재접속 타임아웃")
                await context.close()
                return None, None

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
