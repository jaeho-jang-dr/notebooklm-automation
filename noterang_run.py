#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 기본 워크플로우 실행 스크립트

사용법:
    python noterang_run.py --title "족관절 염좌"
    python noterang_run.py --title "족관절 염좌" --design 2
    python noterang_run.py --title "족관절 염좌" --design "클레이 3D"
    python noterang_run.py --list-designs

워크플로우:
1. 노트북 생성/선택
2. 디자인 선택 (9개 프리셋)
3. 15장 한글 슬라이드 생성
4. 생성 완료 모니터링
5. PDF 다운로드 → G:/내 드라이브/notebooklm/
6. PPTX 변환
"""
import asyncio
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang.workflow import (
    NoterangWorkflow,
    run_workflow,
    print_design_menu,
    select_design,
    DESIGN_PRESETS,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="노트랑 - NotebookLM 슬라이드 자동화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python noterang_run.py --title "족관절 염좌"
  python noterang_run.py --title "족관절 염좌" --design 3
  python noterang_run.py --title "족관절 염좌" --design "클레이 3D"
  python noterang_run.py --list-designs

디자인 프리셋:
  1. 미니멀 젠     - 깔끔한 기본 스타일
  2. 클레이 3D     - 부드러운 3D 클레이 스타일
  3. 메디컬 케어   - 의료/건강 전문 스타일
  4. 사이언스 랩   - 과학/연구 스타일
  5. 학술 논문     - 학술 발표 스타일
  6. 인포그래픽    - 데이터 시각화 스타일
  7. 코퍼레이트    - 비즈니스 프레젠테이션
  8. 클린 모던     - 현대적 깔끔한 스타일
  9. 다크 모드     - 어두운 배경 스타일
"""
    )

    parser.add_argument(
        "--title", "-t",
        help="노트북/슬라이드 제목 (필수)"
    )
    parser.add_argument(
        "--design", "-d",
        help="디자인 번호(1-9) 또는 이름. 미입력시 선택 메뉴"
    )
    parser.add_argument(
        "--slides", "-s",
        type=int,
        default=15,
        help="슬라이드 수 (기본: 15)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="브라우저 숨김 모드"
    )
    parser.add_argument(
        "--list-designs",
        action="store_true",
        help="디자인 목록 출력"
    )

    args = parser.parse_args()

    # 디자인 목록 출력
    if args.list_designs:
        print_design_menu()
        return

    # 제목 필수
    if not args.title:
        parser.print_help()
        print("\n오류: --title 옵션이 필요합니다.")
        sys.exit(1)

    # 디자인 결정
    design_name = None
    if args.design:
        # 숫자인지 확인
        try:
            design_num = int(args.design)
            if 1 <= design_num <= 9:
                design_name = DESIGN_PRESETS[design_num - 1]["name"]
            else:
                print(f"오류: 디자인 번호는 1-9 사이여야 합니다.")
                sys.exit(1)
        except ValueError:
            # 문자열이면 디자인 이름으로 사용
            design_name = args.design

    # 워크플로우 실행
    print("\n" + "=" * 60)
    print("  🎯 노트랑 - NotebookLM 슬라이드 자동화")
    print("=" * 60)

    result = asyncio.run(run_workflow(
        title=args.title,
        design=design_name,
        slide_count=args.slides,
        headless=args.headless,
    ))

    if result.get("success"):
        print("\n✅ 완료!")
        print(f"   PDF:  {result.get('pdf_path')}")
        print(f"   PPTX: {result.get('pptx_path')}")
    else:
        print(f"\n❌ 실패: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
