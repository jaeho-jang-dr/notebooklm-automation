#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 기본 워크플로우

워크플로우:
1. 노트북 생성 또는 기존 노트북 선택
2. 디자인 선택 (9개 프리셋 또는 커스텀)
3. 15장 한글 슬라이드 생성 요청
4. 생성 완료까지 모니터링 (일정 간격 체크)
5. PDF 다운로드 → G:/내 드라이브/notebooklm/
6. PPTX 변환

Usage:
    python -m noterang.workflow --title "족관절 염좌"
    python -m noterang.workflow --title "족관절 염좌" --design "클레이 3D"
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 다운로드 경로
DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")

# 9개 기본 디자인 프리셋
DESIGN_PRESETS = [
    {"id": 1, "name": "미니멀 젠", "category": "심플", "description": "깔끔한 기본 스타일"},
    {"id": 2, "name": "클레이 3D", "category": "카툰", "description": "부드러운 3D 클레이 스타일"},
    {"id": 3, "name": "메디컬 케어", "category": "비즈니스", "description": "의료/건강 전문 스타일"},
    {"id": 4, "name": "사이언스 랩", "category": "학술", "description": "과학/연구 스타일"},
    {"id": 5, "name": "학술 논문", "category": "학술", "description": "학술 발표 스타일"},
    {"id": 6, "name": "인포그래픽", "category": "테크니컬", "description": "데이터 시각화 스타일"},
    {"id": 7, "name": "코퍼레이트", "category": "비즈니스", "description": "비즈니스 프레젠테이션"},
    {"id": 8, "name": "클린 모던", "category": "심플", "description": "현대적 깔끔한 스타일"},
    {"id": 9, "name": "다크 모드", "category": "모던", "description": "어두운 배경 스타일"},
]

# 질병/의료 관련 추천 디자인
MEDICAL_DESIGNS = ["메디컬 케어", "사이언스 랩", "학술 논문", "인포그래픽",
                   "클린 모던", "미니멀 젠", "코퍼레이트"]


def print_design_menu() -> None:
    """디자인 선택 메뉴 출력"""
    print("\n" + "=" * 60)
    print("  🎨 슬라이드 디자인 선택")
    print("=" * 60)
    print()
    for preset in DESIGN_PRESETS:
        print(f"  [{preset['id']}] {preset['name']:<12} - {preset['description']}")
    print()
    print("  [0] 직접 입력 (100개 스타일 중 선택)")
    print("=" * 60)


def select_design(choice: Optional[int] = None) -> Dict[str, str]:
    """
    디자인 선택

    Args:
        choice: 1-9 프리셋 선택, 0이면 직접 입력, None이면 메뉴 표시

    Returns:
        {"name": "디자인명", "category": "카테고리"}
    """
    if choice is None:
        print_design_menu()
        try:
            choice = int(input("  디자인 번호 선택 (1-9, 기본=1): ").strip() or "1")
        except ValueError:
            choice = 1

    if choice == 0:
        # 직접 입력
        from .prompts import SlidePrompts
        prompts = SlidePrompts()

        print("\n카테고리:", ", ".join(prompts.list_categories()))
        style_name = input("스타일 이름 입력: ").strip()

        if style_name in prompts:
            style = prompts.get_style(style_name)
            return {"name": style["name"], "category": style["category"]}
        else:
            print(f"'{style_name}' 스타일을 찾을 수 없습니다. 기본 스타일 사용.")
            return {"name": "미니멀 젠", "category": "심플"}

    elif 1 <= choice <= 9:
        preset = DESIGN_PRESETS[choice - 1]
        return {"name": preset["name"], "category": preset["category"]}

    else:
        print("잘못된 선택. 기본 스타일 사용.")
        return {"name": "미니멀 젠", "category": "심플"}


def get_design_prompt(design_name: str) -> str:
    """디자인 이름으로 프롬프트 가져오기"""
    from .prompts import SlidePrompts
    prompts = SlidePrompts()
    return prompts.get_prompt(design_name) or ""


class NoterangWorkflow:
    """노트랑 기본 워크플로우 관리자"""

    def __init__(
        self,
        title: str,
        design: Optional[str] = None,
        slide_count: int = 15,
        language: str = "ko",
        download_dir: Optional[Path] = None,
    ):
        """
        Args:
            title: 노트북/슬라이드 제목
            design: 디자인 이름 (None이면 선택 메뉴 표시)
            slide_count: 슬라이드 수 (기본 15)
            language: 언어 (기본 한글)
            download_dir: 다운로드 경로
        """
        self.title = title
        self.design_name = design
        self.slide_count = slide_count
        self.language = language
        self.download_dir = download_dir or DOWNLOAD_DIR

        # 결과
        self.notebook_id: Optional[str] = None
        self.pdf_path: Optional[Path] = None
        self.pptx_path: Optional[Path] = None

    async def run(self, headless: bool = False) -> Dict[str, Any]:
        """
        전체 워크플로우 실행

        Returns:
            {
                "success": bool,
                "notebook_id": str,
                "pdf_path": str,
                "pptx_path": str,
                "slide_count": int,
                "design": str,
                "error": str (실패 시)
            }
        """
        print("\n" + "=" * 60)
        print(f"  🎯 노트랑 워크플로우 시작")
        print(f"  제목: {self.title}")
        print("=" * 60)

        try:
            # 1. 디자인 선택
            if self.design_name is None:
                design = select_design()
                self.design_name = design["name"]

            print(f"\n✓ 디자인: {self.design_name}")

            # 2. 브라우저 시작 및 로그인
            print("\n[1/5] 브라우저 시작 및 로그인...")
            from .browser import NotebookLMBrowser

            browser = NotebookLMBrowser(headless=headless)
            await browser.start()

            if not await browser.ensure_logged_in():
                return {"success": False, "error": "로그인 실패"}

            print("  ✓ 로그인 완료")

            # 3. 노트북 찾기 또는 생성
            print(f"\n[2/5] 노트북 '{self.title}' 찾기/생성...")
            notebook = await browser.find_or_create_notebook(self.title)

            if not notebook:
                await browser.close()
                return {"success": False, "error": "노트북 생성 실패"}

            self.notebook_id = notebook.get("id")
            print(f"  ✓ 노트북 ID: {self.notebook_id}")

            # 4. 슬라이드 생성 요청
            print(f"\n[3/5] 슬라이드 생성 요청 ({self.slide_count}장, 한글)...")
            design_prompt = get_design_prompt(self.design_name)

            success = await browser.create_slides(
                language="Korean",
                slide_count=self.slide_count,
                design_prompt=design_prompt,
            )

            if not success:
                await browser.close()
                return {"success": False, "error": "슬라이드 생성 요청 실패"}

            print("  ✓ 슬라이드 생성 요청 완료")

            # 5. 생성 완료 모니터링
            print(f"\n[4/5] 슬라이드 생성 모니터링...")
            completed = await self._monitor_slide_generation(browser)

            if not completed:
                await browser.close()
                return {"success": False, "error": "슬라이드 생성 타임아웃"}

            print("  ✓ 슬라이드 생성 완료")

            # 6. PDF 다운로드
            print(f"\n[5/5] PDF 다운로드...")
            self.download_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = self.title.replace(" ", "_").replace("/", "-")
            pdf_filename = f"{safe_title}_{self.design_name}_{timestamp}.pdf"
            self.pdf_path = self.download_dir / pdf_filename

            downloaded = await browser.download_slides(str(self.pdf_path))

            if not downloaded:
                await browser.close()
                return {"success": False, "error": "PDF 다운로드 실패"}

            print(f"  ✓ PDF 저장: {self.pdf_path}")

            await browser.close()

            # 7. PPTX 변환
            print(f"\n[변환] PDF → PPTX...")
            self.pptx_path = await self._convert_to_pptx()

            if self.pptx_path:
                print(f"  ✓ PPTX 저장: {self.pptx_path}")

            # 완료
            print("\n" + "=" * 60)
            print("  ✅ 워크플로우 완료!")
            print(f"  PDF:  {self.pdf_path}")
            print(f"  PPTX: {self.pptx_path}")
            print("=" * 60)

            return {
                "success": True,
                "notebook_id": self.notebook_id,
                "pdf_path": str(self.pdf_path),
                "pptx_path": str(self.pptx_path) if self.pptx_path else None,
                "slide_count": self.slide_count,
                "design": self.design_name,
            }

        except Exception as e:
            print(f"\n❌ 오류: {e}")
            return {"success": False, "error": str(e)}

    async def _monitor_slide_generation(
        self,
        browser,
        timeout: int = 300,
        interval: int = 10,
    ) -> bool:
        """
        슬라이드 생성 완료 모니터링

        Args:
            browser: NotebookLMBrowser 인스턴스
            timeout: 최대 대기 시간 (초)
            interval: 체크 간격 (초)

        Returns:
            생성 완료 여부
        """
        start_time = time.time()
        check_count = 0

        while time.time() - start_time < timeout:
            check_count += 1
            elapsed = int(time.time() - start_time)

            print(f"  체크 #{check_count} ({elapsed}초 경과)...", end=" ")

            # 슬라이드 생성 완료 확인
            is_ready = await browser.check_slides_ready()

            if is_ready:
                print("✓ 완료!")
                return True

            print("생성 중...")
            await asyncio.sleep(interval)

        print(f"  ⚠️ 타임아웃 ({timeout}초)")
        return False

    async def _convert_to_pptx(self) -> Optional[Path]:
        """PDF를 PPTX로 변환"""
        if not self.pdf_path or not self.pdf_path.exists():
            return None

        try:
            from .converter import pdf_to_pptx

            pptx_path = self.pdf_path.with_suffix(".pptx")
            success = pdf_to_pptx(str(self.pdf_path), str(pptx_path))

            return pptx_path if success else None

        except Exception as e:
            print(f"  PPTX 변환 실패: {e}")
            return None


async def run_workflow(
    title: str,
    design: Optional[str] = None,
    slide_count: int = 15,
    headless: bool = False,
) -> Dict[str, Any]:
    """
    노트랑 워크플로우 실행 (편의 함수)

    Args:
        title: 노트북 제목
        design: 디자인 이름 (None이면 선택 메뉴)
        slide_count: 슬라이드 수
        headless: 브라우저 숨김 여부

    Returns:
        워크플로우 결과
    """
    workflow = NoterangWorkflow(
        title=title,
        design=design,
        slide_count=slide_count,
    )
    return await workflow.run(headless=headless)


# CLI 실행
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="노트랑 기본 워크플로우")
    parser.add_argument("--title", "-t", required=True, help="노트북/슬라이드 제목")
    parser.add_argument("--design", "-d", help="디자인 이름 (미입력시 선택 메뉴)")
    parser.add_argument("--slides", "-s", type=int, default=15, help="슬라이드 수 (기본 15)")
    parser.add_argument("--headless", action="store_true", help="브라우저 숨김")
    parser.add_argument("--list-designs", action="store_true", help="디자인 목록 출력")

    args = parser.parse_args()

    if args.list_designs:
        print_design_menu()
        sys.exit(0)

    result = asyncio.run(run_workflow(
        title=args.title,
        design=args.design,
        slide_count=args.slides,
        headless=args.headless,
    ))

    sys.exit(0 if result.get("success") else 1)
