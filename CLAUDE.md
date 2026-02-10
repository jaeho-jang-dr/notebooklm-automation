# 노트랑 (Noterang) v2.0 - NotebookLM 완전 자동화

## ⚡ 자동 트리거
**다음 키워드 감지 시 자동 실행:** `노트랑`, `noterang`, `notebooklm`, `슬라이드 만들어`, `ppt 만들어`

## Development Environment
- OS: Windows 10.0.26200
- Python: 3.12+
- Conductor: `D:/Projects/_Global_Orchestrator/conductor/NoterangIntegration.ts`

## Quick Start

```bash
# 전체 자동화 실행
python run_noterang.py

# CLI 사용
python -m noterang login --show    # 먼저 로그인!
python -m noterang config --show   # 설정 확인

# API 호출 (Conductor용)
python run_noterang_api.py --title "제목" --language ko
```

## 프로젝트 구조 (v2.0)

```
noterang/
├── __init__.py     # 패키지 API
├── config.py       # 설정 관리
├── auth.py         # 자동 로그인
├── browser.py      # ⭐ Playwright 직접 제어 (권장)
├── notebook.py     # 노트북 CRUD
├── artifacts.py    # 슬라이드/인포그래픽 생성
├── download.py     # 브라우저 기반 다운로드
├── convert.py      # PDF → PPTX 변환
├── core.py         # Noterang 클래스
└── cli.py          # CLI 인터페이스

run_noterang.py       # 간편 실행 스크립트
run_noterang_api.py   # Conductor API 인터페이스
noterang_config.json  # 설정 파일
```

## 핵심 API

### Python 사용 (권장: 브라우저 기반)

```python
from noterang import Noterang

noterang = Noterang()

# 브라우저 기반 자동화
result = await noterang.run_browser(
    title="견관절회전근개 파열",
    sources=["https://example.com/article"],  # 선택
    language="ko"  # 반드시 한글!
)

if result.success:
    print(f"PDF: {result.pdf_path}")
    print(f"PPTX: {result.pptx_path}")
```

### CLI 명령

```bash
python -m noterang login --show     # 로그인
python -m noterang list             # 노트북 목록
python -m noterang config --show    # 설정 확인
python -m noterang convert file.pdf # PDF 변환
```

## 🔐 완전 자동 로그인 (2FA TOTP 포함)

### 자동 로그인 흐름
```
[1] NotebookLM 접속
[2] 이메일 자동 입력 (GOOGLE_EMAIL)
[3] 비밀번호 자동 입력 (GOOGLE_PASSWORD)
[4] "다른 방법 시도" 클릭 → "Google OTP" 선택
[5] TOTP 코드 자동 생성/입력 (pyotp)
[6] 로그인 완료!
```

### 인증 정보 파일 (`.env.local`)
```bash
GOOGLE_EMAIL=your@gmail.com
GOOGLE_PASSWORD=yourpassword
GOOGLE_2FA_SECRET=your2fasecretwithoutspaces
NOTEBOOKLM_APP_PASSWORD=xxxx xxxx xxxx xxxx
APIFY_API_KEY=apify_api_xxxxx
```

### 자동 로그인 명령
```bash
# 완전 자동 로그인 테스트
python -m noterang.auto_login

# TOTP 코드만 확인
python -m noterang.auto_login --test-totp

# 백그라운드 실행
python -m noterang.auto_login --headless
```

## 중요 규칙

| 문제 | 해결책 |
|------|--------|
| nlm CLI 버그 | **run_browser() 메서드 사용** |
| 다운로드 403 | **Playwright 브라우저 사용** |
| 슬라이드 언어 | **반드시 한글 "ko"** |
| 로그인 필요 | **자동 로그인 (2FA TOTP 자동)** |

## 경로

- 다운로드: `G:/내 드라이브/notebooklm/`
- 인증 정보: `./.env.local` (git 제외됨)
- 브라우저 프로필: `~/.notebooklm-auto-v3/`
- 설정: `./noterang_config.json`

## Conductor 통합

```typescript
// D:/Projects/_Global_Orchestrator/conductor/NoterangIntegration.ts
import { handleNoterangMessage, detectNoterangTrigger } from './NoterangIntegration';

// 메시지에서 트리거 감지
if (detectNoterangTrigger(message)) {
    const result = await handleNoterangMessage(message);
}
```

## API 키 설정

API 키는 `.env.local`에서 관리 (git에 커밋하지 않음)

---

## 📝 JPDF - PDF → 편집 가능 PPTX 변환

PDF 슬라이드에서 텍스트를 OCR로 추출하고, 배경을 복원(inpainting)한 후 편집 가능한 PPTX를 생성합니다.

### 사용법

```bash
# noterang 모듈로 실행
python -m noterang.jpdf input.pdf -o output.pptx

# 옵션
python -m noterang.jpdf input.pdf --no-inpaint  # 텍스트 제거 없이
python -m noterang.jpdf input.pdf --font-size 20
```

### Python에서 사용

```python
from noterang import JPDF, jpdf_convert

# 클래스 사용
converter = JPDF()
pptx_path, count = converter.convert("slides.pdf")

# 간편 함수
pptx_path, count = jpdf_convert("slides.pdf", "output.pptx")
```

### 필요한 API 키

`.env.local`에 Google Vision API 키 필요:
```
GOOGLE_VISION_API_KEY=AIzaSy...
```

### 독립 앱

`apps/jpdf/` 폴더에 독립 실행 버전이 있습니다.

---

## 🎨 슬라이드 디자인 스타일 (100개 프롬프트)

슬라이드 생성 시 **반드시 스타일을 물어볼 것!**

### 질병/의료 슬라이드 추천 스타일

| # | 스타일 | 카테고리 | 특징 |
|---|--------|---------|------|
| 1 | **기본** | - | NotebookLM 기본 스타일 (프롬프트 없음) |
| 2 | **메디컬 케어** | 비즈니스 | 의료/헬스케어 전문, 청록+흰색, 신뢰감 |
| 3 | **사이언스 랩** | 학술 | 과학/연구 느낌, 다크+그린, 실험실 무드 |
| 4 | **학술 논문** | 학술 | 논문 스타일, 세리프 폰트, 공식적 |
| 5 | **클린 모던** | 심플 | iOS 스타일, 깔끔한 카드 UI |
| 6 | **인포그래픽** | 테크니컬 | 데이터 시각화, 차트/그래프 적합 |
| 7 | **화이트 페이퍼** | 심플 | 백서/공식문서, 인쇄물 느낌 |
| 8 | **미니멀 젠** | 심플 | 여백 60%+, Apple 키노트 스타일 |
| 9 | **클레이 3D** | 카툰 | 부드러운 점토 느낌, 파스텔, 친근함 |

### 스타일 질문 예시

```
슬라이드 스타일을 선택해주세요:

1. 기본 (NotebookLM 기본)
2. 메디컬 케어 (의료 전문, 추천)
3. 사이언스 랩 (연구/실험)
4. 학술 논문 (논문 스타일)
5. 클린 모던 (깔끔한 현대적)
6. 인포그래픽 (데이터 시각화)
7. 화이트 페이퍼 (공식 문서)
8. 미니멀 젠 (여백 중심)
9. 클레이 3D (친근한 점토 느낌)

번호 또는 스타일명을 입력하세요 (기본: 2):
```

### 클레이 3D 프롬프트 예시

```text
[NotebookLM 슬라이드 디자인 요청]

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

위 가이드를 바탕으로 고품질 슬라이드를 생성해주세요.
```

### 프롬프트 CLI

```bash
# 전체 스타일 목록
python -m noterang prompts --list

# 특정 스타일 프롬프트 보기
python -m noterang prompts --get "메디컬 케어"

# 스타일 검색
python -m noterang prompts --search "의료"
```

### Python에서 프롬프트 사용

```python
from noterang import get_slide_prompt, SlidePrompts

# 특정 스타일 프롬프트 가져오기
prompt = get_slide_prompt("메디컬 케어")

# 전체 관리
prompts = SlidePrompts()
medical_styles = prompts.search("메디컬")
```
