import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from noterang.browser import NotebookLMBrowser
from noterang.convert import pdf_to_pptx
from noterang.config import get_config

# "Clay 3D" Prompt
CLAY_PROMPT = """[NotebookLM 슬라이드 디자인 요청]

■ 역할: 전문 프레젠테이션 디자이너
■ 스타일: 클레이 3D
■ 카테고리: 카툰

━━━━━━━━━━━━━━━━━━━━━━

[컬러 시스템]
• 배경: #f1f5f9
• 텍스트: #475569
• 강조: #818cf8
• 폰트: Nunito

[무드 & 레퍼런스]
닌텐도 Kirby, 클레이 렌더

[디자인 특성]
• 부드러운 라운드
• 파스텔 컬러
• 소프트 그림자
• 촉감적 느낌

[텍스처]
클레이 표면

[레이아웃 가이드]
둥근 3D 오브젝트, 파스텔 배경

━━━━━━━━━━━━━━━━━━━━━━

위 가이드를 바탕으로 고품질 슬라이드를 생성해주세요."""

async def send_chat_message(page, message):
    """채팅 메시지 전송"""
    print("  채팅 입력 중... (20초 대기)")
    await asyncio.sleep(20) # UI 로딩 대기
    
    # 챗 입력창 찾기 시도
    # Main chat input usually at the bottom
    
    input_el = await page.query_selector('textarea')
    if not input_el:
         # Try looking for a div that looks like a simplified input
         input_el = await page.query_selector('div[contenteditable="true"]')
    
    if not input_el:
        print("  ⚠️ textarea 찾기 실패, 페이지 텍스트 덤프...")
        # Debug: check what placeholders are available
        inputs = await page.query_selector_all('input, textarea')
        for i in inputs:
            ph = await i.get_attribute('placeholder')
            label = await i.get_attribute('aria-label')
            print(f"    found input/textarea: ph='{ph}', label='{label}'")
            
        print("  ❌ 채팅 입력창을 찾을 수 없습니다.")
        return False
        
    print(f"  ✓ 입력창 발견, 메시지 입력...")
    try:
        await input_el.click(force=True, timeout=5000)
    except Exception as e:
        print(f"  ⚠️ click 실패 ({e}), 바로 type 시도...")
        
    try:
        # fill 대신 type 사용 (이벤트 트리거가 확실함)
        await input_el.type(message, delay=10) # 10ms delay simulates typing
    except Exception as e:
        print(f"  ⚠️ type 실패, fill로 재시도: {e}")
        await input_el.fill(message)
        
    await asyncio.sleep(2)
    
    # 전송 버튼 클릭
    send_btn = await page.query_selector('button[aria-label*="Send"], button[aria-label*="전송"], button[type="submit"]:not([disabled])')
    
    if send_btn:
        print("  전송 버튼 클릭...")
        try:
             await send_btn.click(timeout=5000)
        except:
             print("  ⚠️ 전송 버튼 클릭 실패 (비활성화?), Enter 키 시도...")
             await input_el.press('Enter')
    else:
        print("  전송 버튼 미발견, Enter 키 입력...")
        await input_el.press('Enter')
        
    print("  메시지 전송 완료, 응답 대기 (30초)...")
    await asyncio.sleep(30) # 모델 응답 대기 (확실히 처리되도록)
    return True

async def main():
    # 설정 override
    config = get_config()
    target_dir = Path("G:/내 드라이브/notebooklm")
    target_dir.mkdir(parents=True, exist_ok=True)
    config.download_dir = target_dir
    
    print("=" * 60)
    print("노트랑: 족저 근막염 + 클레이 3D 슬라이드 생성")
    print(f"다운로드 경로: {target_dir}")
    print("=" * 60)

    async with NotebookLMBrowser() as browser:
        # 로그인
        print("\n[1/5] 로그인 확인...")
        if not await browser.ensure_logged_in():
            print("❌ 로그인 실패")
            return

        # 노트북 찾기 (Fallback Logic added)
        print("\n[2/5] '족저 근막염' 노트북 찾기...")
        notebook_found = False
        
        # 1. Try standard find
        notebook = await browser.find_notebook("족저 근막염")
        if notebook:
            notebook_id = notebook['id']
            print(f"  ✓ 노트북 발견: {notebook_id[:8]}...")
            await browser.open_notebook(notebook_id)
            notebook_found = True
        else:
            print("  ⚠️ 목록에서 찾기 실패, 텍스트 매칭 시도...")
            # 2. Try clicking text directly
            try:
                # "족저" 텍스트를 포함하는 요소 찾기 (공백/오타 가능성)
                search_term = "족저"
                notebook_el = browser.page.get_by_text(search_term, exact=False).first
                count = await browser.page.get_by_text(search_term, exact=False).count()
                print(f"  ℹ️ '{search_term}' 포함 요소 {count}개 발견")
                
                if count > 0:
                    print(f"  ✓ '{search_term}' 텍스트 요소 클릭 시도...")
                    # 혹시 모르니 강제로 클릭
                    await notebook_el.click(force=True)
                    await asyncio.sleep(8) # 로딩 대기
                    
                    # URL 확인하여 ID 추출
                    if '/notebook/' in browser.page.url:
                        notebook_id = browser.page.url.split('/notebook/')[-1].split('/')[0]
                        print(f"  ✓ 노트북 열기 성공: {notebook_id}")
                        notebook_found = True
                    else:
                         print(f"  ⚠️ 클릭 후 URL 변경 안됨: {browser.page.url}")
                else:
                    print(f"  ❌ '{search_term}' 텍스트를 찾을 수 없습니다.")
                    
            except Exception as e:
                print(f"  ❌ 텍스트 클릭 실패: {e}")

        if not notebook_found:
            print("❌ '족저 근막염' 노트북을 열 수 없습니다.")
            return

        # ID가 없으면 현재 URL에서 추출
        if 'notebook_id' not in locals():
             if '/notebook/' in browser.page.url:
                notebook_id = browser.page.url.split('/notebook/')[-1].split('/')[0]

        
        # 프롬프트 주입
        print("\n[3/5] 클레이 3D 프롬프트 적용...")
        await send_chat_message(browser.page, CLAY_PROMPT)
        
        # 슬라이드 생성
        print("\n[4/5] 슬라이드 생성 및 다운로드...")
        # create_slides는 "Slides" 버튼을 클릭합니다.
        # 프롬프트가 컨텍스트에 들어갔으므로, 생성 버튼 클릭 시 반영되기를 기대합니다.
        if await browser.create_slides(notebook_id, language="ko"):
             if await browser.wait_for_slides(notebook_id):
                 pdf_path = await browser.download_slides(notebook_id)
                 if pdf_path and pdf_path.exists():
                     print(f"  ✓ PDF 다운로드 완료: {pdf_path}")
                     
                     # PPTX 변환
                     print("\n[5/5] PPTX 변환...")
                     pptx_path, count = pdf_to_pptx(pdf_path)
                     if pptx_path:
                         print(f"  ✓ PPTX 변환 완료: {pptx_path}")
                         print(f"  슬라이드 수: {count}")
                     else:
                         print("  ❌ PPTX 변환 실패")
                 else:
                     print("  ❌ PDF 다운로드 실패")
             else:
                 print("  ❌ 슬라이드 생성 대기 실패")
        else:
             print("  ❌ 슬라이드 생성 시작 실패")

if __name__ == "__main__":
    asyncio.run(main())
