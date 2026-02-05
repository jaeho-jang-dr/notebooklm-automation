#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
슬라이드 디자인 갤러리 생성 - 실제 프리뷰 이미지 포함
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import fitz
import base64
import json

# 미니멀 젠 슬라이드 이미지 추출
pdf_path = 'G:/내 드라이브/notebooklm/족저근막염_미니멀젠_20260204_232249.pdf'
doc = fitz.open(pdf_path)

# 슬라이드 2 (한글 포함) 추출
page = doc[1]
mat = fitz.Matrix(0.4, 0.4)
pix = page.get_pixmap(matrix=mat)
img_bytes = pix.tobytes('png')
minimal_zen_preview = base64.b64encode(img_bytes).decode('utf-8')
doc.close()

print(f"미니멀 젠 프리뷰: {pix.width}x{pix.height}")

# 100개 디자인 데이터
designs = [
    {"id": 1, "name": "미니멀 젠", "category": "심플", "colors": ["#FFFFFF", "#000000", "#9ca3af"],
     "prompt": "미니멀 젠 스타일로 만들어주세요: 깔끔하고 간결한 레이아웃, 충분한 여백, 차분한 색상, 핵심만 전달하는 심플한 디자인",
     "preview": f"data:image/png;base64,{minimal_zen_preview}"},
    {"id": 2, "name": "블랙 & 화이트", "category": "심플", "colors": ["#000000", "#FFFFFF", "#333333"]},
    {"id": 3, "name": "노르딕", "category": "심플", "colors": ["#E8E4E1", "#2C3E50", "#95A5A6"]},
    {"id": 4, "name": "와이어프레임", "category": "심플", "colors": ["#FFFFFF", "#333333", "#0066FF"]},
    {"id": 5, "name": "화이트 페이퍼", "category": "심플", "colors": ["#FFFFFF", "#1a1a1a", "#666666"]},
    {"id": 6, "name": "무인양품", "category": "심플", "colors": ["#F5F5F5", "#8B4513", "#333333"]},
    {"id": 7, "name": "젠 가든", "category": "심플", "colors": ["#F0EDE5", "#4A5D23", "#8B7355"]},
    {"id": 8, "name": "클린 모던", "category": "심플", "colors": ["#FFFFFF", "#2563eb", "#64748b"]},
    {"id": 9, "name": "네온 퓨처", "category": "모던", "colors": ["#0a0a0a", "#00ff88", "#ff00ff"]},
    {"id": 10, "name": "스위스 스타일", "category": "모던", "colors": ["#FFFFFF", "#FF0000", "#000000"]},
    {"id": 11, "name": "글래스모피즘", "category": "모던", "colors": ["#667eea", "#FFFFFF", "#764ba2"]},
    {"id": 12, "name": "네온 느와르", "category": "모던", "colors": ["#0d0d0d", "#ff006e", "#00f5ff"]},
    {"id": 13, "name": "바우하우스", "category": "모던", "colors": ["#FFFFFF", "#FF0000", "#0000FF"]},
    {"id": 14, "name": "오로라 그라데이션", "category": "모던", "colors": ["#667eea", "#764ba2", "#f093fb"]},
    {"id": 15, "name": "웹 브루탈리즘", "category": "모던", "colors": ["#FFFF00", "#000000", "#FF0000"]},
    {"id": 16, "name": "뉴모피즘", "category": "모던", "colors": ["#e0e5ec", "#ffffff", "#a3b1c6"]},
    {"id": 17, "name": "다크 모드", "category": "모던", "colors": ["#1a1a2e", "#eaeaea", "#0f3460"]},
    {"id": 18, "name": "멤피스", "category": "모던", "colors": ["#FF6B6B", "#4ECDC4", "#FFE66D"]},
    {"id": 19, "name": "코퍼레이트", "category": "비즈니스", "colors": ["#003366", "#FFFFFF", "#0066CC"]},
    {"id": 20, "name": "스타트업 피치", "category": "비즈니스", "colors": ["#FF6B35", "#FFFFFF", "#1a1a1a"]},
    {"id": 21, "name": "파이낸스", "category": "비즈니스", "colors": ["#1B365D", "#C5B358", "#FFFFFF"]},
    {"id": 22, "name": "메디컬 케어", "category": "비즈니스", "colors": ["#00A86B", "#FFFFFF", "#E8F5E9"]},
    {"id": 23, "name": "럭셔리 부동산", "category": "비즈니스", "colors": ["#1a1a1a", "#C9A961", "#FFFFFF"]},
    {"id": 24, "name": "법률 문서", "category": "비즈니스", "colors": ["#1C2841", "#8B0000", "#D4AF37"]},
    {"id": 25, "name": "컨설팅 리포트", "category": "비즈니스", "colors": ["#2C3E50", "#E74C3C", "#ECF0F1"]},
    {"id": 26, "name": "테크 기업", "category": "비즈니스", "colors": ["#00D4FF", "#0a0a0a", "#FFFFFF"]},
    {"id": 27, "name": "HR/채용", "category": "비즈니스", "colors": ["#FF6B6B", "#4A90A4", "#FFFFFF"]},
    {"id": 28, "name": "리테일/커머스", "category": "비즈니스", "colors": ["#FF4500", "#FFD700", "#FFFFFF"]},
    {"id": 29, "name": "포레스트", "category": "내추럴", "colors": ["#228B22", "#8B4513", "#F5F5DC"]},
    {"id": 30, "name": "딥 스페이스", "category": "내추럴", "colors": ["#0B0B1A", "#4B0082", "#FFD700"]},
    {"id": 31, "name": "딥 오션", "category": "내추럴", "colors": ["#000080", "#00CED1", "#E0FFFF"]},
    {"id": 32, "name": "사하라 듄", "category": "내추럴", "colors": ["#EDC9AF", "#8B4513", "#1a1a1a"]},
    {"id": 33, "name": "오로라", "category": "내추럴", "colors": ["#00FF7F", "#FF69B4", "#0a0a2e"]},
    {"id": 34, "name": "보타니컬", "category": "내추럴", "colors": ["#2E8B57", "#F0FFF0", "#8FBC8F"]},
    {"id": 35, "name": "알파인", "category": "내추럴", "colors": ["#87CEEB", "#FFFFFF", "#4682B4"]},
    {"id": 36, "name": "트로피컬", "category": "내추럴", "colors": ["#FF6347", "#00CED1", "#FFD700"]},
    {"id": 37, "name": "골든 아워", "category": "럭셔리", "colors": ["#FFD700", "#1a1a1a", "#FFA500"]},
    {"id": 38, "name": "보그 에디토리얼", "category": "럭셔리", "colors": ["#FFFFFF", "#000000", "#C9A961"]},
    {"id": 39, "name": "다이아몬드", "category": "럭셔리", "colors": ["#E8E8E8", "#B9F2FF", "#1a1a1a"]},
    {"id": 40, "name": "샴페인 골드", "category": "럭셔리", "colors": ["#F7E7CE", "#C9A961", "#2C1810"]},
    {"id": 41, "name": "누아르", "category": "럭셔리", "colors": ["#0a0a0a", "#C9A961", "#FFFFFF"]},
    {"id": 42, "name": "이탈리안 마블", "category": "럭셔리", "colors": ["#FFFFFF", "#C0C0C0", "#2F4F4F"]},
    {"id": 43, "name": "신스웨이브", "category": "레트로", "colors": ["#FF006E", "#8338EC", "#00F5FF"]},
    {"id": 44, "name": "8비트 아케이드", "category": "레트로", "colors": ["#FF0000", "#00FF00", "#0000FF"]},
    {"id": 45, "name": "Y2K 퓨처", "category": "레트로", "colors": ["#FF69B4", "#C0C0C0", "#00FFFF"]},
    {"id": 46, "name": "폴라로이드", "category": "레트로", "colors": ["#FFFEF0", "#000000", "#87CEEB"]},
    {"id": 47, "name": "재즈 바이닐", "category": "레트로", "colors": ["#1a1a1a", "#C9A961", "#8B0000"]},
    {"id": 48, "name": "브루탈 콘크리트", "category": "레트로", "colors": ["#808080", "#333333", "#FF4500"]},
    {"id": 49, "name": "VHS 글리치", "category": "레트로", "colors": ["#FF0000", "#00FF00", "#0000FF"]},
    {"id": 50, "name": "디스코 70s", "category": "레트로", "colors": ["#FF6B6B", "#FFE66D", "#4ECDC4"]},
    {"id": 51, "name": "빈티지 신문", "category": "레트로", "colors": ["#F5F5DC", "#1a1a1a", "#8B4513"]},
    {"id": 52, "name": "사이키델릭", "category": "레트로", "colors": ["#FF00FF", "#FFFF00", "#00FFFF"]},
    {"id": 53, "name": "아르데코", "category": "레트로", "colors": ["#1a1a1a", "#C9A961", "#2F4F4F"]},
    {"id": 54, "name": "폴라로이드 콜라주", "category": "레트로", "colors": ["#FFFEF0", "#FF69B4", "#87CEEB"]},
    {"id": 55, "name": "모던 갤러리", "category": "크리에이티브", "colors": ["#FFFFFF", "#1a1a1a", "#FF4500"]},
    {"id": 56, "name": "비비드 팝", "category": "크리에이티브", "colors": ["#FF1493", "#00FF00", "#FFD700"]},
    {"id": 57, "name": "스트릿 그래피티", "category": "크리에이티브", "colors": ["#FF4500", "#FFD700", "#32CD32"]},
    {"id": 58, "name": "다다 콜라주", "category": "크리에이티브", "colors": ["#FF0000", "#FFFF00", "#000000"]},
    {"id": 59, "name": "수채화", "category": "크리에이티브", "colors": ["#87CEEB", "#FFB6C1", "#98FB98"]},
    {"id": 60, "name": "네온 사인", "category": "크리에이티브", "colors": ["#0a0a0a", "#FF1493", "#00FFFF"]},
    {"id": 61, "name": "리소그래프", "category": "크리에이티브", "colors": ["#FF6B6B", "#4ECDC4", "#F7F7F7"]},
    {"id": 62, "name": "추상 미니멀", "category": "크리에이티브", "colors": ["#FFFFFF", "#000000", "#FF4500"]},
    {"id": 63, "name": "아메리칸 코믹", "category": "크리에이티브", "colors": ["#FFFF00", "#FF0000", "#0000FF"]},
    {"id": 64, "name": "스티커 팩", "category": "크리에이티브", "colors": ["#FFD700", "#FF69B4", "#00CED1"]},
    {"id": 65, "name": "학술 논문", "category": "학술", "colors": ["#FFFFFF", "#003366", "#333333"]},
    {"id": 66, "name": "역사 문서", "category": "학술", "colors": ["#F5F5DC", "#8B4513", "#1a1a1a"]},
    {"id": 67, "name": "사이언스 랩", "category": "학술", "colors": ["#E8F5E9", "#1B5E20", "#0D47A1"]},
    {"id": 68, "name": "수학 공식", "category": "학술", "colors": ["#FFFEF0", "#000080", "#1a1a1a"]},
    {"id": 69, "name": "학위논문", "category": "학술", "colors": ["#FFFFFF", "#800000", "#1a1a1a"]},
    {"id": 70, "name": "백과사전", "category": "학술", "colors": ["#F5F5F5", "#2F4F4F", "#8B0000"]},
    {"id": 71, "name": "팝 코믹스", "category": "카툰", "colors": ["#FFFF00", "#FF0000", "#000000"]},
    {"id": 72, "name": "애니메이션", "category": "카툰", "colors": ["#FF69B4", "#87CEEB", "#FFD700"]},
    {"id": 73, "name": "클레이 3D", "category": "카툰", "colors": ["#FFB6C1", "#98FB98", "#87CEEB"]},
    {"id": 74, "name": "로우 폴리", "category": "카툰", "colors": ["#4ECDC4", "#FF6B6B", "#2C3E50"]},
    {"id": 75, "name": "치비 캐릭터", "category": "카툰", "colors": ["#FFB6C1", "#FFFACD", "#98FB98"]},
    {"id": 76, "name": "웹툰 스타일", "category": "카툰", "colors": ["#FFFFFF", "#1a1a1a", "#FF6B6B"]},
    {"id": 77, "name": "두들 낙서", "category": "카툰", "colors": ["#FFFEF0", "#1a1a1a", "#FF4500"]},
    {"id": 78, "name": "빈티지 카툰", "category": "카툰", "colors": ["#F5F5DC", "#8B4513", "#FF6347"]},
    {"id": 79, "name": "건축 청사진", "category": "테크니컬", "colors": ["#003366", "#FFFFFF", "#00BFFF"]},
    {"id": 80, "name": "PCB 회로", "category": "테크니컬", "colors": ["#006400", "#FFD700", "#1a1a1a"]},
    {"id": 81, "name": "인포그래픽", "category": "테크니컬", "colors": ["#FF6B6B", "#4ECDC4", "#2C3E50"]},
    {"id": 82, "name": "지형 지도", "category": "테크니컬", "colors": ["#228B22", "#8B4513", "#87CEEB"]},
    {"id": 83, "name": "대시보드 UI", "category": "테크니컬", "colors": ["#1a1a2e", "#00D4FF", "#FFFFFF"]},
    {"id": 84, "name": "코드 에디터", "category": "테크니컬", "colors": ["#1E1E1E", "#569CD6", "#4EC9B0"]},
    {"id": 85, "name": "터미널", "category": "테크니컬", "colors": ["#0C0C0C", "#00FF00", "#FFFFFF"]},
    {"id": 86, "name": "플로우차트", "category": "테크니컬", "colors": ["#FFFFFF", "#4A90A4", "#FF6B6B"]},
    {"id": 87, "name": "스케치북", "category": "크래프트", "colors": ["#FFFEF0", "#2F4F4F", "#8B4513"]},
    {"id": 88, "name": "빈티지 타자기", "category": "크래프트", "colors": ["#F5F5DC", "#1a1a1a", "#8B4513"]},
    {"id": 89, "name": "종이접기", "category": "크래프트", "colors": ["#FF6B6B", "#4ECDC4", "#FFE66D"]},
    {"id": 90, "name": "자수 패턴", "category": "크래프트", "colors": ["#F5F5DC", "#8B0000", "#006400"]},
    {"id": 91, "name": "목판화", "category": "크래프트", "colors": ["#F5F5DC", "#1a1a1a", "#8B4513"]},
    {"id": 92, "name": "활판 인쇄", "category": "크래프트", "colors": ["#FFFEF0", "#1a1a1a", "#8B0000"]},
    {"id": 93, "name": "1급 기밀", "category": "재미", "colors": ["#1a1a1a", "#FF0000", "#FFFFFF"]},
    {"id": 94, "name": "위험 경고", "category": "재미", "colors": ["#FFD700", "#000000", "#FF0000"]},
    {"id": 95, "name": "어린이 그림", "category": "재미", "colors": ["#FFD700", "#FF69B4", "#87CEEB"]},
    {"id": 96, "name": "블루스크린", "category": "재미", "colors": ["#0000AA", "#FFFFFF", "#AAAAAA"]},
    {"id": 97, "name": "윈도우 95", "category": "재미", "colors": ["#008080", "#C0C0C0", "#000080"]},
    {"id": 98, "name": "로딩 스크린", "category": "재미", "colors": ["#1a1a1a", "#00FF00", "#FFFFFF"]},
    {"id": 99, "name": "영수증", "category": "재미", "colors": ["#FFFEF0", "#1a1a1a", "#FF0000"]},
    {"id": 100, "name": "밈 템플릿", "category": "재미", "colors": ["#FFFFFF", "#000000", "#FF4500"]},
]

# 프롬프트 생성 함수
def generate_prompt(design):
    name = design["name"]
    category = design["category"]

    prompts = {
        "블랙 & 화이트": "순수한 흑백 대비의 모던한 슬라이드를 만들어주세요. 강렬한 타이포그래피, 그래픽 요소는 흑백만 사용, 미니멀하면서도 임팩트 있는 디자인",
        "노르딕": "스칸디나비안 디자인 스타일로 만들어주세요. 밝은 자연광 느낌, 따뜻한 회색과 흰색 베이스, 나무 텍스처 힌트, 기능적이고 아늑한 분위기",
        "와이어프레임": "UI/UX 와이어프레임 스타일로 만들어주세요. 깔끔한 선과 박스 레이아웃, 블루 액센트 포인트, 프로토타입 느낌의 기술적 디자인",
        "화이트 페이퍼": "공식 보고서/백서 스타일로 만들어주세요. 깨끗한 흰 배경, 전문적인 타이포그래피, 데이터 시각화 중심, 신뢰감 있는 학술적 디자인",
        "무인양품": "MUJI 스타일의 미니멀리즘으로 만들어주세요. 자연스러운 소재 느낌, 베이지와 흰색 톤, 절제된 우아함, 일상의 아름다움",
        "젠 가든": "일본 정원에서 영감받은 평화로운 디자인으로 만들어주세요. 자연스러운 녹색 톤, 돌과 물의 느낌, 명상적이고 고요한 분위기",
        "클린 모던": "현대적이고 깔끔한 비즈니스 스타일로 만들어주세요. 밝은 배경에 블루 액센트, 명확한 계층 구조, 프로페셔널한 느낌",
        "네온 퓨처": "사이버펑크 네온 스타일로 만들어주세요. 어두운 배경에 밝은 네온 컬러, 글로우 효과, 미래지향적이고 테크니컬한 느낌",
        "스위스 스타일": "스위스 국제 타이포그래피 스타일로 만들어주세요. 그리드 기반 레이아웃, 산세리프 폰트, 빨간 액센트, 명확하고 객관적인 디자인",
        "글래스모피즘": "반투명 유리 효과의 모던 스타일로 만들어주세요. 블러 배경, 미묘한 테두리, 부드러운 그라데이션, 세련된 UI 느낌",
    }

    if name in prompts:
        return prompts[name]

    # 카테고리별 기본 프롬프트 생성
    category_base = {
        "심플": "깔끔하고 미니멀한",
        "모던": "현대적이고 세련된",
        "비즈니스": "전문적이고 신뢰감 있는",
        "내추럴": "자연에서 영감받은 편안한",
        "럭셔리": "고급스럽고 우아한",
        "레트로": "복고풍의 감성적인",
        "크리에이티브": "창의적이고 예술적인",
        "학술": "학술적이고 체계적인",
        "카툰": "재미있고 친근한 일러스트 스타일의",
        "테크니컬": "기술적이고 전문적인",
        "크래프트": "수공예 느낌의 따뜻한",
        "재미": "유머러스하고 재미있는",
    }

    base = category_base.get(category, "독특한")
    return f"{name} 스타일로 만들어주세요. {base} 디자인으로, {name}의 특징적인 비주얼 요소를 활용해주세요."

# 디자인에 프롬프트 추가
for design in designs:
    if "prompt" not in design:
        design["prompt"] = generate_prompt(design)

# HTML 생성
html_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NotebookLM 슬라이드 디자인 갤러리 - 100개 스타일</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .header {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
        .header p { color: rgba(255,255,255,0.6); font-size: 14px; }
        .stats { display: flex; gap: 20px; margin-top: 15px; }
        .stat { background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 20px; font-size: 13px; }
        .search-box {
            padding: 20px 40px;
        }
        .search-box input {
            width: 100%;
            padding: 15px 20px;
            border: none;
            border-radius: 12px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 16px;
        }
        .search-box input::placeholder { color: rgba(255,255,255,0.5); }
        .categories {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 10px 40px 20px;
        }
        .category-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
        .category-btn:hover { background: rgba(255,255,255,0.2); transform: translateY(-2px); }
        .category-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .category-btn .count {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 8px;
            font-size: 12px;
        }
        .container { padding: 20px 40px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
        .card-preview {
            height: 180px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .card-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .card-preview .gradient-preview {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .preview-text {
            font-size: 20px;
            font-weight: 700;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
            text-align: center;
            padding: 10px;
        }
        .preview-category {
            font-size: 12px;
            opacity: 0.8;
            margin-top: 5px;
        }
        .card-content { padding: 20px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .card-title { font-size: 18px; font-weight: 600; }
        .card-id { color: rgba(255,255,255,0.4); font-size: 12px; }
        .card-category {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            margin-bottom: 15px;
        }
        .card-actions { display: flex; gap: 10px; }
        .btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .btn-copy {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        .btn-copy:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }
        .btn-detail {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
        .btn-detail:hover { background: rgba(255,255,255,0.2); }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .modal.show { display: flex; }
        .modal-content {
            background: #1a1a2e;
            border-radius: 20px;
            max-width: 600px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
        }
        .modal-preview {
            height: 250px;
            position: relative;
        }
        .modal-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .modal-body { padding: 30px; }
        .modal-title { font-size: 28px; font-weight: 700; margin-bottom: 10px; }
        .modal-category {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .modal-section { margin-bottom: 20px; }
        .modal-section h3 { font-size: 14px; color: rgba(255,255,255,0.6); margin-bottom: 10px; }
        .modal-prompt {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            font-size: 14px;
            line-height: 1.6;
        }
        .modal-colors { display: flex; gap: 10px; }
        .color-chip {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.2);
        }
        .modal-close {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 50%;
            background: rgba(0,0,0,0.5);
            color: #fff;
            font-size: 24px;
            cursor: pointer;
        }
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: #4CAF50;
            color: #fff;
            padding: 15px 30px;
            border-radius: 10px;
            font-weight: 500;
            transition: transform 0.3s ease;
            z-index: 1001;
        }
        .toast.show { transform: translateX(-50%) translateY(0); }
        .real-preview-badge {
            position: absolute;
            top: 10px;
            left: 10px;
            background: #4CAF50;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>🎨 NotebookLM 슬라이드 디자인 갤러리</h1>
        <p>100개의 프로페셔널 슬라이드 디자인 프롬프트</p>
        <div class="stats">
            <div class="stat">📊 총 100개 스타일</div>
            <div class="stat">📁 12개 카테고리</div>
            <div class="stat">📋 복사해서 바로 사용</div>
        </div>
    </header>

    <div class="search-box">
        <input type="text" id="searchInput" placeholder="🔍 디자인 검색... (예: 미니멀, 3D, 비즈니스)">
    </div>

    <nav class="categories" id="categoryNav"></nav>
    <main class="container"><div class="grid" id="designGrid"></div></main>

    <div class="modal" id="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">×</button>
            <div class="modal-preview" id="modalPreview"></div>
            <div class="modal-body">
                <h2 class="modal-title" id="modalTitle"></h2>
                <span class="modal-category" id="modalCategory"></span>
                <div class="modal-section">
                    <h3>프롬프트</h3>
                    <div class="modal-prompt" id="modalPrompt"></div>
                </div>
                <div class="modal-section">
                    <h3>컬러 팔레트</h3>
                    <div class="modal-colors" id="modalColors"></div>
                </div>
                <button class="btn btn-copy" style="width:100%;margin-top:20px" onclick="copyFromModal()">📋 프롬프트 복사</button>
            </div>
        </div>
    </div>

    <div class="toast" id="toast">✅ 프롬프트가 클립보드에 복사되었습니다!</div>

    <script>
const designs = ''' + json.dumps(designs, ensure_ascii=False) + ''';

const categories = ["전체", ...new Set(designs.map(d => d.category))];
const categoryNav = document.getElementById('categoryNav');
const designGrid = document.getElementById('designGrid');
const searchInput = document.getElementById('searchInput');

let currentCategory = "전체";
let currentDesign = null;

function getCategoryCount(cat) {
    if (cat === "전체") return designs.length;
    return designs.filter(d => d.category === cat).length;
}

function renderCategories() {
    categoryNav.innerHTML = categories.map(cat => `
        <button class="category-btn ${cat === currentCategory ? 'active' : ''}" onclick="filterCategory('${cat}')">
            ${cat}<span class="count">${getCategoryCount(cat)}</span>
        </button>
    `).join('');
}

function createPreview(design) {
    if (design.preview) {
        return `<img src="${design.preview}" alt="${design.name}">
                <div class="real-preview-badge">실제 슬라이드</div>`;
    }
    const colors = design.colors;
    const gradient = `linear-gradient(135deg, ${colors[0]} 0%, ${colors[1]} 50%, ${colors[2] || colors[1]} 100%)`;
    const textColor = isLightColor(colors[0]) ? '#000' : '#fff';
    return `<div class="gradient-preview" style="background: ${gradient}">
        <div class="preview-text" style="color: ${textColor}">
            ${design.name}
            <div class="preview-category">${design.category}</div>
        </div>
    </div>`;
}

function isLightColor(hex) {
    const c = hex.replace('#', '');
    const r = parseInt(c.substr(0, 2), 16);
    const g = parseInt(c.substr(2, 2), 16);
    const b = parseInt(c.substr(4, 2), 16);
    return (r * 299 + g * 587 + b * 114) / 1000 > 128;
}

function renderDesigns() {
    const searchTerm = searchInput.value.toLowerCase();
    let filtered = designs;

    if (currentCategory !== "전체") {
        filtered = filtered.filter(d => d.category === currentCategory);
    }

    if (searchTerm) {
        filtered = filtered.filter(d =>
            d.name.toLowerCase().includes(searchTerm) ||
            d.category.toLowerCase().includes(searchTerm) ||
            d.prompt.toLowerCase().includes(searchTerm)
        );
    }

    designGrid.innerHTML = filtered.map(design => `
        <div class="card">
            <div class="card-preview">${createPreview(design)}</div>
            <div class="card-content">
                <div class="card-header">
                    <span class="card-title">${design.name}</span>
                    <span class="card-id">#${design.id}</span>
                </div>
                <span class="card-category">${design.category}</span>
                <div class="card-actions">
                    <button class="btn btn-copy" onclick="copyPrompt(${design.id})">📋 복사</button>
                    <button class="btn btn-detail" onclick="showDetail(${design.id})">👁️ 상세</button>
                </div>
            </div>
        </div>
    `).join('');
}

function filterCategory(cat) {
    currentCategory = cat;
    renderCategories();
    renderDesigns();
}

function copyPrompt(id) {
    const design = designs.find(d => d.id === id);
    navigator.clipboard.writeText(design.prompt).then(() => showToast());
}

function showToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

function showDetail(id) {
    currentDesign = designs.find(d => d.id === id);
    document.getElementById('modalTitle').textContent = currentDesign.name;
    document.getElementById('modalCategory').textContent = currentDesign.category;
    document.getElementById('modalPrompt').textContent = currentDesign.prompt;

    const previewHtml = currentDesign.preview
        ? `<img src="${currentDesign.preview}" alt="${currentDesign.name}">`
        : `<div class="gradient-preview" style="background: linear-gradient(135deg, ${currentDesign.colors.join(', ')}); height: 100%;"></div>`;
    document.getElementById('modalPreview').innerHTML = previewHtml;

    document.getElementById('modalColors').innerHTML = currentDesign.colors.map(c =>
        `<div class="color-chip" style="background: ${c}" title="${c}"></div>`
    ).join('');

    document.getElementById('modal').classList.add('show');
}

function closeModal() {
    document.getElementById('modal').classList.remove('show');
}

function copyFromModal() {
    if (currentDesign) {
        navigator.clipboard.writeText(currentDesign.prompt).then(() => showToast());
    }
}

document.getElementById('modal').addEventListener('click', e => {
    if (e.target.id === 'modal') closeModal();
});

searchInput.addEventListener('input', renderDesigns);

renderCategories();
renderDesigns();
    </script>
</body>
</html>'''

# 파일 저장
output_path = 'slide_design_gallery/index_with_preview.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\\n✅ 갤러리 생성 완료: {output_path}")
print(f"파일 크기: {len(html_content) / 1024:.1f} KB")
