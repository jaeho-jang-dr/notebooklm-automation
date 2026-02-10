#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
템플릿 미리보기 이미지 생성
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = Path("D:/Projects/notebooklm-automation/CCimages/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 스타일 정의
STYLES = {
    "modern": {
        "name": "Modern",
        "name_ko": "모던",
        "bg": (0x1a, 0x1a, 0x2e),
        "title": (0xff, 0xff, 0xff),
        "body": (0xe0, 0xe0, 0xe0),
        "accent": (0x00, 0xd9, 0xff),
        "desc": "다크 네이비 배경 + 사이안 악센트\n기술/개발 프레젠테이션에 적합"
    },
    "minimal": {
        "name": "Minimal",
        "name_ko": "미니멀",
        "bg": (0xff, 0xff, 0xff),
        "title": (0x33, 0x33, 0x33),
        "body": (0x66, 0x66, 0x66),
        "accent": (0x00, 0x7a, 0xcc),
        "desc": "깔끔한 화이트 배경\n학술 발표/비즈니스 미팅에 적합"
    },
    "corporate": {
        "name": "Corporate",
        "name_ko": "코퍼레이트",
        "bg": (0xf5, 0xf5, 0xf5),
        "title": (0x00, 0x3d, 0x7a),
        "body": (0x33, 0x33, 0x33),
        "accent": (0x00, 0x7a, 0xcc),
        "desc": "라이트 그레이 배경 + 블루 포인트\n기업 프레젠테이션에 적합"
    },
    "creative": {
        "name": "Creative",
        "name_ko": "크리에이티브",
        "bg": (0x2d, 0x13, 0x2c),
        "title": (0xff, 0xd9, 0x3d),
        "body": (0xff, 0xff, 0xff),
        "accent": (0xff, 0x6b, 0x6b),
        "desc": "다크 퍼플 배경 + 골드 악센트\n창의적인 프레젠테이션에 적합"
    },
}


def create_preview(style_key: str, style: dict) -> Path:
    """템플릿 미리보기 이미지 생성"""

    # 16:9 비율 (1280x720)
    width, height = 1280, 720
    img = Image.new('RGB', (width, height), style["bg"])
    draw = ImageDraw.Draw(img)

    # 폰트 설정 (기본 폰트 사용)
    try:
        title_font = ImageFont.truetype("malgun.ttf", 48)
        body_font = ImageFont.truetype("malgun.ttf", 24)
        small_font = ImageFont.truetype("malgun.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # 악센트 라인
    draw.rectangle([50, 140, 250, 148], fill=style["accent"])

    # 제목
    title_text = f"슬라이드 템플릿 가이드"
    draw.text((50, 50), title_text, font=title_font, fill=style["title"])

    # 스타일 이름 뱃지
    badge_text = f"{style['name']} Style"
    draw.rectangle([50, 170, 250, 210], fill=style["accent"])
    draw.text((60, 175), badge_text, font=body_font, fill=style["bg"])

    # 본문
    body_lines = [
        "노트랑에서 자동 생성된 스타일 슬라이드입니다.",
        "",
        "• 4가지 스타일 지원 (Modern, Minimal, Corporate, Creative)",
        "• PDF에서 자동 텍스트 추출",
        "• 커스텀 템플릿 적용 가능",
        "• NotebookLM 완전 자동화",
    ]

    y_pos = 250
    for line in body_lines:
        draw.text((50, y_pos), line, font=body_font, fill=style["body"])
        y_pos += 40

    # 하단 설명
    desc_lines = style["desc"].split('\n')
    y_pos = height - 100
    for line in desc_lines:
        draw.text((50, y_pos), line, font=small_font, fill=style["accent"])
        y_pos += 25

    # 우측 샘플 박스
    box_x, box_y = 850, 200
    box_w, box_h = 350, 400

    # 샘플 카드
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h],
                   outline=style["accent"], width=2)

    # 샘플 제목
    draw.text((box_x + 20, box_y + 20), "Sample Card",
              font=body_font, fill=style["title"])

    # 샘플 라인
    draw.rectangle([box_x + 20, box_y + 60, box_x + 120, box_y + 65],
                   fill=style["accent"])

    # 샘플 텍스트
    sample_lines = [
        "Lorem ipsum dolor sit",
        "amet consectetur",
        "adipiscing elit.",
        "",
        "• Item one",
        "• Item two",
        "• Item three",
    ]
    y_pos = box_y + 90
    for line in sample_lines:
        draw.text((box_x + 20, y_pos), line, font=small_font, fill=style["body"])
        y_pos += 30

    # 저장
    output_path = OUTPUT_DIR / f"template_{style_key}.png"
    img.save(output_path)

    return output_path


def main():
    print("=" * 60)
    print("템플릿 미리보기 이미지 생성")
    print("=" * 60)

    for key, style in STYLES.items():
        print(f"\n{style['name']} ({style['name_ko']}) 생성 중...")
        path = create_preview(key, style)
        print(f"  ✓ {path}")

    print("\n" + "=" * 60)
    print(f"미리보기 저장 위치: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
