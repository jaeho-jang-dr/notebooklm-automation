# web_publisher

NotebookLM PDF → 웹 자료실 자동 등록 CLI

## 설치

```bash
pip install firebase-admin PyMuPDF requests python-dotenv
```

## 사용법

```bash
cd D:\Projects\notebooklm-automation

# 단일 실행: NLM 슬라이드 생성 → PDF 분석 → 자료실 등록
python -m apps.web_publisher single --title "아킬레스건염" --design "미니멀 젠"

# 병렬 배치: 여러 주제 동시 실행
python -m apps.web_publisher batch --titles "골다공증,측만증,거북목" --max-workers 3

# 기존 PDF만 등록 (5-10초)
python -m apps.web_publisher pdf --pdf "G:/내 드라이브/notebooklm/slides.pdf" --title "오십견"
python -m apps.web_publisher pdf --latest --title "족저근막염"
```

## 공통 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--no-register` | 자료실 등록 안 함 | false |
| `--hidden` | 비공개 등록 | false |
| `--type` | disease / guide / news | disease |
| `--slides` | 슬라이드 장수 | 15 |

## 아키텍처

```
apps/web_publisher/
├── __init__.py           # 패키지
├── __main__.py           # python -m 진입점
├── config.py             # WebPublisherConfig
├── body_parts.py         # 부위 키워드 매칭
├── pdf_analyzer.py       # PyMuPDF + Vision OCR
├── file_manager.py       # UUID 파일명 + uploads 복사
├── firestore_client.py   # Firebase Firestore 등록
├── pipeline.py           # WebPublishPipeline (단일)
├── batch.py              # BatchPublisher (병렬)
├── cli.py                # CLI 인터페이스
└── README.md
```

## 파이프라인 흐름

```
[1/4] NotebookLM 슬라이드 생성 (기존 PDF 있으면 건너뜀)
      ├── 인증 확인 (TTL 20분 자동 갱신)
      ├── 노트북 생성/재사용
      ├── 연구 소스 수집 (한의학 자동 제외)
      ├── 슬라이드 생성 (timeout=600)
      └── PDF 다운로드 (API → Playwright fallback)

[2/4] PDF 분석
      ├── PyMuPDF 텍스트 추출
      ├── Vision OCR 폴백 (이미지 기반 PDF)
      └── 키워드 추출 + 부위 자동 판별

[3/4] 웹앱 파일 복사
      ├── PDF → public/uploads/noterang_{timestamp}_{uuid}_{title}.pdf
      └── 썸네일 → public/uploads/noterang_{timestamp}_{uuid}_{title}_thumb.png

[4/4] Firestore 자료실 등록
      ├── content: 첫 페이지 이미지 + 목차 + 전체 텍스트
      ├── tags: 자동생성 + 부위 + 키워드
      └── 8000자 제한 truncation
```

## 환경 변수

| 변수 | 설명 |
|------|------|
| `GOOGLE_CLOUD_VISION_API_KEY` | Vision OCR API 키 |
| `WEBAPP_DIR` | miryangosweb 경로 (기본: D:/Projects/miryangosweb) |
| `FIREBASE_PROJECT_ID` | Firebase 프로젝트 ID (기본: miryangosweb) |
