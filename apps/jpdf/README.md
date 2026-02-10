# JPDF v1.1 - PDF/이미지 → 편집 가능 PPTX 변환기

PDF, PNG, JPG 파일을 편집 가능한 PPTX로 변환하는 웹 앱입니다.

## 기능

- **OCR**: Google Cloud Vision API로 정확한 한글/영문 텍스트 추출
- **Inpainting**: OpenCV로 텍스트 영역 배경 자동 복원
- **PPTX 생성**: 깨끗한 배경 + 편집 가능한 텍스트 박스
- **웹 UI**: 드래그 앤 드롭 파일 업로드
- **다양한 포맷**: PDF, PNG, JPG 지원

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt
```

## 설정

```bash
# API 키 설정
cp .env.example .env.local
# .env.local 편집하여 GOOGLE_VISION_API_KEY 입력
```

## 실행

### 웹 앱 (권장)

```bash
python app.py
# 브라우저에서 http://localhost:5000 접속
```

### CLI

```bash
# PDF 변환
python jpdf.py input.pdf -o output.pptx

# 이미지 변환
python jpdf.py image.png -o output.pptx

# 옵션
python jpdf.py input.pdf --font-family "Malgun Gothic" --font-size 20
```

## 변환 모드

| 모드 | 설명 |
|------|------|
| **수정 가능하게 만들기** | 텍스트 제거 → 배경 복원 → 편집 가능한 텍스트 박스 |
| **바로 만들기** | 원본 이미지 배경 + 텍스트 오버레이 |

## CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-o, --output` | 출력 파일 경로 | `{입력파일}_편집가능.pptx` |
| `--api-key` | Google Vision API 키 | 환경변수 |
| `--no-inpaint` | 텍스트 제거 안함 | False |
| `--font-family` | 폰트 | Arial |
| `--font-size` | 폰트 크기 고정 | 자동 |
| `--zoom` | 이미지 확대 비율 | 2.0 |

## 지원 폰트

- Arial, Calibri, Times New Roman, Georgia, Verdana, Tahoma
- 맑은 고딕 (Malgun Gothic), 나눔고딕 (NanumGothic)

## API 키 발급

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 프로젝트 생성 또는 선택
3. Vision API 활성화
4. API 키 생성
5. `.env.local`에 키 입력

## 파일 구조

```
jpdf/
├── app.py           # Flask 웹 서버
├── jpdf.py          # 변환 엔진
├── templates/
│   └── index.html   # 웹 UI
├── static/
│   └── style.css    # 스타일
├── requirements.txt
├── .env.example
└── README.md
```

## 라이선스

MIT License
