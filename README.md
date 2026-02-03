# NotebookLM 프로젝트

Google NotebookLM을 완전 자동화하기 위한 통합 프로젝트 디렉토리.
Noterang 에이전트, 자동화 스크립트, 문서가 모두 이 디렉토리에 있습니다.

## 핵심 원칙: NotebookLM 우선

> **Claude는 다음 작업에 토큰을 낭비하지 않는다. 전부 NotebookLM에게 맡긴다:**

| 작업 | 담당 | 이유 |
|------|------|------|
| 정보 수집/연구 | NotebookLM | 더 정확하고 빠름 |
| 슬라이드/프레젠테이션 | NotebookLM | 품질이 더 미려함 |
| 인포그래픽 | NotebookLM | 시각적 품질 우수 |
| 요약/보고서 | NotebookLM | 더 정직한 요약 |
| 퀴즈/플래시카드 | NotebookLM | 교육 콘텐츠 특화 |

**Claude의 역할:** MCP 도구로 NotebookLM을 제어하고, 결과물을 활용하는 것에 집중

---

## 중요: 한글 우선 정책

**모든 아티팩트 생성 시 `language="ko"` 필수!**

```python
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",
    language="ko",  # 항상 포함!
    confirm=True
)
```

## 핵심 스크립트

| 스크립트 | 용도 | 사용법 |
|----------|------|--------|
| `refresh_auth_v2.py` | 브라우저 로그인으로 인증 갱신 | `python refresh_auth_v2.py` |
| `download_helper.py` | Playwright로 파일 다운로드 | `python download_helper.py <type> <url> <path>` |
| `pdf_to_pptx.py` | PDF→PPTX 변환 + 합치기 | `python pdf_to_pptx.py` |
| `add_korean_notes.py` | PPTX에 한글 노트 추가 | `python add_korean_notes.py` |
| `translate_slides.py` | 슬라이드 번역 (OCR 필요시) | `python translate_slides.py` |

## 디렉토리 구조

```
notebooklm/                         # 메인 프로젝트 디렉토리
├── README.md                       # 이 파일
├── NOTEBOOKLM_AUTOMATION.md        # 상세 자동화 가이드
│
├── noterang/                       # Noterang 에이전트 (노트랑)
│   ├── noterang.py                 # 에이전트 코드
│   ├── CONDUCTOR.md                # Conductor 통합 가이드
│   ├── README.md                   # 에이전트 문서
│   ├── INSTALLATION.md             # 설치 가이드
│   └── skill.json                  # 스킬 메타데이터
│
├── 핵심 스크립트
│   ├── refresh_auth_v2.py          # 인증 갱신
│   ├── download_helper.py          # 다운로드 헬퍼
│   ├── pdf_to_pptx.py              # PDF 변환
│   ├── add_korean_notes.py         # 한글 노트 추가
│   └── translate_slides.py         # 번역 스크립트
│
├── downloads/                      # 다운로드 폴더
│   ├── *.pdf                       # 원본 슬라이드
│   ├── *.pptx                      # 변환된 슬라이드
│   ├── *_통합.pptx                 # 합쳐진 슬라이드
│   └── *_한글.pptx                 # 한글 노트 포함
│
└── (기타 유틸리티 스크립트)
```

## 워크플로우

### 방법 1: MCP 사용 (권장)

#### 1-1. 인증 (세션 만료 시)
```bash
python refresh_auth_v2.py
# 브라우저 열림 → Google 로그인 → 자동 저장
```

#### 1-2. Claude Code에서 MCP 호출
```python
# 노트북 목록
mcp__notebooklm__notebook_list()

# 아티팩트 생성 (항상 language="ko" 포함!)
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",
    language="ko",  # 필수!
    confirm=True
)

# 상태 확인 (다운로드 URL 획득)
mcp__notebooklm__studio_status(notebook_id="...")

# 한글 요약
mcp__notebooklm__notebook_query(notebook_id="...", query="한국어로 요약")
```

---

### 방법 2: nlm CLI 사용 (MCP 400 오류 시)

MCP에서 `400 Bad Request` 오류 발생 시 nlm CLI를 직접 사용합니다.

#### 2-1. CLI 인증
```bash
NLM="C:/Users/antigravity/AppData/Roaming/Python/Python313/Scripts/nlm.exe"
$NLM login -p default
```

#### 2-2. 전체 프로시저
```bash
# 노트북 생성
$NLM notebook create "노트북 제목"
# → NOTEBOOK_ID 획득

# 소스 추가
$NLM source add <NOTEBOOK_ID> --url "https://url1.com" --wait
$NLM source add <NOTEBOOK_ID> --url "https://url2.com" --wait

# 슬라이드 생성 (항상 --language ko!)
$NLM slides create <NOTEBOOK_ID> --language ko --confirm

# 상태 확인 (completed 될 때까지)
$NLM studio status <NOTEBOOK_ID>

# 다운로드
$NLM download slide-deck <NOTEBOOK_ID> --output "downloads/output.pdf"

# 한글 요약 질의
$NLM query notebook <NOTEBOOK_ID> "15개 슬라이드에 맞게 2-3문장씩 요약해줘"
```

---

### 공통: 다운로드 및 변환

#### 다운로드 (MCP 403 에러 시)
```bash
python download_helper.py pdf "URL" "downloads/output.pdf"
python download_helper.py png "URL" "downloads/output.png"
```

#### PDF → PPTX 변환
```bash
python pdf_to_pptx.py
# 또는 단일 파일:
python -c "from pdf_to_pptx import pdf_to_pptx; pdf_to_pptx('downloads/input.pdf', 'downloads/output.pptx')"
```

#### 한글 노트 추가
```python
from pptx import Presentation
notes = ['슬라이드1 내용', '슬라이드2 내용', ...]
prs = Presentation('downloads/output.pptx')
for i, slide in enumerate(prs.slides):
    if i < len(notes):
        slide.notes_slide.notes_text_frame.text = notes[i]
prs.save('downloads/output_한글노트.pptx')
```

## 필수 패키지

```bash
pip install python-pptx PyMuPDF playwright deep-translator requests
```

## 인증 파일 위치

```
~/.notebooklm-mcp-cli/
├── auth.json           # 쿠키/토큰
└── browser_profile/    # Playwright 브라우저 프로필
```

## 관련 문서

- 상세 자동화 가이드: `./NOTEBOOKLM_AUTOMATION.md`
- Noterang 에이전트: `./noterang/README.md`
- Conductor 통합: `./noterang/CONDUCTOR.md`

---
*Last updated: 2026-02-03*
