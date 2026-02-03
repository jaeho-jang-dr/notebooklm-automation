#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NotebookLM 다운로드 헬퍼"""
import asyncio
import sys
import requests
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PROFILE_DIR = Path.home() / ".notebooklm-mcp-cli" / "browser_profile"

async def download_with_playwright(url, output_path):
    """Playwright로 다운로드"""
    from playwright.async_api import async_playwright
    
    global _download
    _download = None
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
            ignore_default_args=['--enable-automation'],
            accept_downloads=True,
        )
        
        page = await context.new_page()
        
        def on_download(d):
            global _download
            _download = d
        
        page.on("download", on_download)
        
        try:
            await page.goto(url, timeout=120000)
        except:
            pass
        
        await asyncio.sleep(3)
        
        if _download:
            path = await _download.path()
            if path:
                await _download.save_as(str(output_path))
                await context.close()
                return True
        
        await context.close()
        return False

def download_direct(url, output_path):
    """직접 다운로드"""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False

async def main():
    if len(sys.argv) < 4:
        print("사용: python download_helper.py <type> <url> <output_path>")
        sys.exit(1)
    
    file_type = sys.argv[1]
    url = sys.argv[2]
    output_path = Path(sys.argv[3])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"다운로드: {output_path.name}")
    
    if 'lh3.googleusercontent.com' in url:
        success = download_direct(url, output_path)
    else:
        success = await download_with_playwright(url, output_path)
    
    if success and output_path.exists():
        size = output_path.stat().st_size
        print(f"완료: {output_path} ({size:,} bytes)")
        sys.exit(0)
    else:
        print("실패")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
