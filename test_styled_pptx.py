#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스타일 PPTX 생성 테스트

사용 가능한 스타일:
- modern: 다크 네이비 배경 + 사이안 악센트
- minimal: 화이트 배경 + 미니멀 디자인
- corporate: 라이트 그레이 배경 + 비즈니스 스타일
- creative: 다크 퍼플 배경 + 골드 악센트
"""
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang import Converter, create_styled_pptx

# 출력 디렉토리
OUTPUT_DIR = Path("G:/내 드라이브/notebooklm")


def test_styled_pptx():
    """스타일 PPTX 생성 테스트"""

    # 테스트 콘텐츠 (노트북에서 추출한 것처럼)
    content_data = [
        {
            "title": "슬라이드 템플릿 가이드",
            "body": "노트랑에서 자동 생성된 스타일 슬라이드입니다.\n\n"
                    "• 4가지 스타일 지원\n"
                    "• PDF에서 자동 텍스트 추출\n"
                    "• 커스텀 템플릿 적용 가능"
        },
        {
            "title": "Modern 스타일",
            "body": "다크 네이비 배경에 사이안 악센트\n\n"
                    "기술 프레젠테이션에 적합합니다.\n"
                    "전문적이고 현대적인 느낌을 줍니다."
        },
        {
            "title": "Minimal 스타일",
            "body": "깔끔한 화이트 배경\n\n"
                    "콘텐츠에 집중할 수 있습니다.\n"
                    "학술 발표나 비즈니스 미팅에 적합합니다."
        },
        {
            "title": "Corporate 스타일",
            "body": "라이트 그레이 배경에 블루 포인트\n\n"
                    "비즈니스 프레젠테이션에 적합합니다.\n"
                    "신뢰감을 주는 디자인입니다."
        },
        {
            "title": "Creative 스타일",
            "body": "다크 퍼플 배경에 골드 악센트\n\n"
                    "창의적인 프레젠테이션에 적합합니다.\n"
                    "눈에 띄는 디자인입니다."
        },
    ]

    print("=" * 60)
    print("스타일 PPTX 생성 테스트")
    print("=" * 60)

    styles = ["modern", "minimal", "corporate", "creative"]

    for style in styles:
        output_path = OUTPUT_DIR / f"test_styled_{style}.pptx"
        print(f"\n{style} 스타일 생성 중...")

        try:
            result = create_styled_pptx(
                content_data=content_data,
                output_path=output_path,
                style=style
            )
            print(f"  ✓ 완료: {result}")
        except Exception as e:
            print(f"  ❌ 실패: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


def test_pdf_to_styled():
    """PDF를 스타일 PPTX로 변환 테스트"""

    converter = Converter(OUTPUT_DIR)

    # 기존 PDF 파일 찾기
    pdf_files = list(OUTPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print("❌ PDF 파일이 없습니다.")
        return

    print(f"\n발견된 PDF 파일: {len(pdf_files)}개")

    for pdf_file in pdf_files[:1]:  # 첫 번째만 테스트
        print(f"\n{pdf_file.name} → 스타일 PPTX 변환 중...")

        result, slide_count = converter.pdf_to_styled_pptx(
            pdf_path=pdf_file,
            style="modern"
        )

        if result:
            print(f"  ✓ 완료: {result} ({slide_count}슬라이드)")
        else:
            print("  ❌ 변환 실패")


if __name__ == "__main__":
    test_styled_pptx()
    # test_pdf_to_styled()
