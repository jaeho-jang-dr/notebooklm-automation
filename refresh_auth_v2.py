#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NotebookLM 인증 갱신 - 자동 감지 + 저장"""
import asyncio
import json
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def main():
    from playwright.async_api import async_playwright
    
    auth_dir = Path.home() / ".notebooklm-mcp-cli"
    auth_dir.mkdir(exist_ok=True)
    auth_file = auth_dir / "auth.json"
    
    user_data_dir = auth_dir / "browser_profile"
    user_data_dir.mkdir(exist_ok=True)
    
    print("="*60)
    print("NotebookLM 인증 갱신")
    print("="*60)
    print()
    print("브라우저가 열리면 Google 로그인 해주세요.")
    print("로그인 완료가 감지되면 자동으로 저장됩니다.")
    print()
    
    saved_cookies = {}
    
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
        
        print("브라우저 열림...")
        
        try:
            await page.goto("https://notebooklm.google.com", wait_until='domcontentloaded', timeout=30000)
        except:
            pass
        
        print("NotebookLM 접속 완료. 로그인 대기 중...\n")
        
        # 로그인 감지 루프
        for i in range(120):  # 최대 10분
            await asyncio.sleep(5)
            
            try:
                # 쿠키 수집
                cookies = await context.cookies()
                cookie_dict = {}
                for cookie in cookies:
                    if 'google.com' in cookie.get('domain', ''):
                        cookie_dict[cookie['name']] = cookie['value']
                
                # 중요 쿠키 확인 (로그인 지표)
                has_sid = 'SID' in cookie_dict
                has_psid = '__Secure-1PSID' in cookie_dict or '__Secure-3PSID' in cookie_dict
                
                if has_sid and has_psid and len(cookie_dict) > 10:
                    saved_cookies = cookie_dict
                    
                    # URL 체크
                    url = page.url
                    if 'notebooklm.google.com' in url and 'accounts.google' not in url:
                        print(f"\n로그인 감지됨! (쿠키 {len(cookie_dict)}개)")
                        break
                
                mins, secs = divmod((i+1)*5, 60)
                print(f"\r대기 중... {mins}분 {secs}초 (쿠키: {len(cookie_dict)}개)", end='', flush=True)
                
            except Exception as e:
                # 브라우저 닫힘
                print(f"\n브라우저 닫힘: {e}")
                break
        
        # 최종 쿠키 저장
        if not saved_cookies:
            try:
                cookies = await context.cookies()
                for cookie in cookies:
                    if 'google.com' in cookie.get('domain', ''):
                        saved_cookies[cookie['name']] = cookie['value']
            except:
                pass
        
        if len(saved_cookies) < 5:
            print("\n\n오류: 유효한 쿠키를 찾을 수 없습니다.")
            print("로그인 후 다시 시도하세요.")
            try:
                await context.close()
            except:
                pass
            return
        
        # 저장
        # CSRF token: SAPISID hash 기반
        sapisid = saved_cookies.get('SAPISID', saved_cookies.get('__Secure-3PAPISID', ''))
        csrf_token = sapisid[:16] + ':' + str(int(time.time() * 1000))

        # Session ID: URL에서 추출 시도, 없으면 빈 문자열
        url = page.url
        session_id = ""
        if '/notebook/' in url:
            # URL 형식: https://notebooklm.google.com/notebook/SESSION_ID
            parts = url.split('/notebook/')
            if len(parts) > 1:
                session_id = parts[1].split('/')[0].split('?')[0]
        
        auth_data = {
            "cookies": saved_cookies,
            "csrf_token": csrf_token,
            "session_id": session_id,
            "extracted_at": time.time()
        }
        
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2)
        
        print(f"\n\n저장 완료!")
        print(f"  파일: {auth_file}")
        print(f"  쿠키: {len(saved_cookies)}개")
        
        # 3초 후 자동 종료
        print("\n3초 후 브라우저가 닫힙니다...")
        await asyncio.sleep(3)
        
        try:
            await context.close()
        except:
            pass
        
        print("\n인증 갱신 완료!")

if __name__ == "__main__":
    asyncio.run(main())
