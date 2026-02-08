"""
web_publisher - NotebookLM PDF → 웹 자료실 자동 등록

독립형 CLI로 NLM 슬라이드 생성 + PDF 분석 + Firestore 자료실 등록을 수행합니다.

Usage:
    # 단일 실행
    python -m apps.web_publisher single --title "아킬레스건염"

    # 병렬 배치
    python -m apps.web_publisher batch --titles "골다공증,측만증" --max-workers 2

    # 기존 PDF만 등록
    python -m apps.web_publisher pdf --latest --title "오십견"
"""

__version__ = "1.0.0"
