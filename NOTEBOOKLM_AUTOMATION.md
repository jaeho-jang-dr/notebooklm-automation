# NotebookLM 완전 자동화 가이드

> 모든 프로젝트에서 사용 가능한 NotebookLM 자동화 시스템

## 중요: 한글 우선 정책

**모든 아티팩트 생성 시 반드시 `language="ko"` 파라미터를 포함해야 합니다!**

```python
# 모든 studio_create 호출에 language="ko" 필수
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",  # 또는 audio, infographic, quiz 등
    language="ko",               # 항상 포함!
    confirm=True
)
```

---

## 디렉토리 구조

```
D:/Entertainments/DevEnvironment/notebooklm/   # 메인 프로젝트 디렉토리
├── README.md                      # 프로젝트 README
├── NOTEBOOKLM_AUTOMATION.md       # 이 파일 (상세 자동화 가이드)
│
├── noterang/                      # Noterang 에이전트
│   ├── noterang.py                # 에이전트 코드
│   ├── CONDUCTOR.md               # Conductor 통합 가이드
│   └── README.md                  # 에이전트 문서
│
├── 핵심 스크립트
│   ├── refresh_auth_v2.py         # 인증 갱신
│   ├── download_helper.py         # 파일 다운로드
│   ├── pdf_to_pptx.py             # PDF→PPTX 변환
│   └── add_korean_notes.py        # 한글 노트 추가
│
├── downloads/                     # 다운로드된 아티팩트
│
└── ~/.notebooklm-mcp-cli/         # 인증 정보 저장소
    ├── auth.json                  # 쿠키/토큰
    └── browser_profile/           # Playwright 프로필
```

## 1. 인증 설정

### 최초 인증 또는 만료 시
```bash
cd D:/Entertainments/DevEnvironment/notebooklm
python refresh_auth_v2.py
```
- 브라우저가 열리면 Google 로그인
- 로그인 완료 감지 후 자동 저장

### Claude Code에서 인증 확인
```
mcp__notebooklm__refresh_auth  → 토큰 리로드
mcp__notebooklm__notebook_list → 작동 확인
```

## 2. MCP 도구 사용법

### 노트북 관리
```python
# 목록 조회
mcp__notebooklm__notebook_list(max_results=10)

# 노트북 생성
mcp__notebooklm__notebook_create(title="제목")

# 노트북 상세
mcp__notebooklm__notebook_get(notebook_id="...")

# 한글 요약 요청
mcp__notebooklm__notebook_query(
    notebook_id="...",
    query="이 내용을 한국어로 상세히 요약해줘"
)
```

### 소스 추가
```python
# URL 추가
mcp__notebooklm__source_add(
    notebook_id="...",
    source_type="url",
    url="https://...",
    wait=True  # 처리 완료까지 대기
)

# 파일 추가
mcp__notebooklm__source_add(
    notebook_id="...",
    source_type="file",
    file_path="/path/to/file.pdf"
)

# 텍스트 추가
mcp__notebooklm__source_add(
    notebook_id="...",
    source_type="text",
    text="내용...",
    title="제목"
)
```

### 아티팩트 생성 (항상 language="ko" 포함!)
```python
# 슬라이드 생성
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",
    language="ko",  # 필수!
    confirm=True
)

# 인포그래픽 생성
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="infographic",
    language="ko",  # 필수!
    confirm=True
)

# 오디오 팟캐스트 생성
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="audio",
    audio_format="deep_dive",  # deep_dive|brief|critique|debate
    language="ko",  # 필수!
    confirm=True
)

# 퀴즈 생성
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="quiz",
    language="ko",  # 필수!
    confirm=True
)

# 플래시카드 생성
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="flashcards",
    language="ko",  # 필수!
    confirm=True
)

# 상태 확인
mcp__notebooklm__studio_status(notebook_id="...")
```

### 아티팩트 종류
| 타입 | 설명 | 출력 |
|------|------|------|
| slide_deck | 프레젠테이션 | PDF |
| infographic | 인포그래픽 | PNG |
| audio | 오디오 팟캐스트 | MP3 |
| video | 비디오 | MP4 |
| report | 보고서 | Markdown |
| quiz | 퀴즈 | JSON |
| flashcards | 플래시카드 | JSON |
| mind_map | 마인드맵 | JSON |

## 3. 파일 다운로드

### MCP 다운로드가 403 에러 시 → Playwright 사용
```bash
cd D:/Entertainments/DevEnvironment/notebooklm
python download_helper.py <type> <url> <output_path>

# 예시
python download_helper.py pdf "https://..." "downloads/slides.pdf"
python download_helper.py png "https://..." "downloads/infographic.png"
```

### 자동화 스크립트에서
```python
import subprocess
subprocess.run([
    "python", "download_helper.py",
    "pdf", url, output_path
], cwd="D:/Entertainments/DevEnvironment/notebooklm")
```

## 4. PDF → PPTX 변환 및 합치기

```bash
cd D:/Entertainments/DevEnvironment/notebooklm
python pdf_to_pptx.py
```

### 커스텀 사용
```python
from pdf_to_pptx import pdf_to_pptx, merge_pptx

# 단일 변환
pdf_to_pptx("input.pdf", "output.pptx")

# 여러 파일 합치기
merge_pptx(["1.pptx", "2.pptx"], "merged.pptx")
```

## 5. 한글화 워크플로우

1. **NotebookLM 쿼리로 한글 요약 생성**
```python
result = mcp__notebooklm__notebook_query(
    notebook_id="...",
    query="모든 내용을 한국어로 상세하게 요약해줘. 마크다운 형식으로."
)
```

2. **PPTX 노트에 추가**
```python
from pptx import Presentation
prs = Presentation("slides.pptx")
for slide in prs.slides:
    notes = slide.notes_slide
    notes.notes_text_frame.text = "한글 번역 내용"
prs.save("slides_korean.pptx")
```

## 6. 전체 자동화 예시

```python
# Claude Code에서 실행

# 1. 노트북 조회
notebooks = mcp__notebooklm__notebook_list()

# 2. 아티팩트 상태 확인
status = mcp__notebooklm__studio_status(notebook_id="...")

# 3. 슬라이드 URL 추출
slide_urls = [a['slide_deck_url'] for a in status['artifacts'] 
              if a['type'] == 'slide_deck' and a['slide_deck_url']]

# 4. 다운로드 (Bash로)
for i, url in enumerate(slide_urls):
    !python download_helper.py pdf "{url}" "downloads/slide_{i}.pdf"

# 5. PPTX 변환
!python pdf_to_pptx.py

# 6. 한글 요약 요청
summary = mcp__notebooklm__notebook_query(notebook_id="...", query="한국어로 요약")

# 7. 노트 추가
!python add_korean_notes.py
```

## 7. nlm CLI 대안 사용법 (MCP 오류 시)

MCP 서버에서 400 Bad Request 오류 발생 시 nlm CLI를 직접 사용합니다.
> GitHub Issue #28: batchexecute 요청에 필요한 헤더/토큰 누락 문제

### 7.1 CLI 인증
```bash
# nlm 경로 (Windows)
NLM="C:/Users/antigravity/AppData/Roaming/Python/Python313/Scripts/nlm.exe"

# 로그인 (Chrome 브라우저 열림)
$NLM login -p default
```

### 7.2 노트북 관리
```bash
# 목록 조회
$NLM notebook list

# 새 노트북 생성
$NLM notebook create "노트북 제목"

# 노트북 상세
$NLM notebook get <NOTEBOOK_ID>
```

### 7.3 소스 추가
```bash
# URL 소스 추가
$NLM source add <NOTEBOOK_ID> --url "https://example.com" --wait

# 파일 소스 추가
$NLM source add <NOTEBOOK_ID> --file "document.pdf" --wait

# 텍스트 소스 추가
$NLM source add <NOTEBOOK_ID> --text "내용..." --title "제목" --wait
```

### 7.4 슬라이드 생성 (항상 --language ko!)
```bash
# 한글 슬라이드 생성
$NLM slides create <NOTEBOOK_ID> --language ko --confirm

# 상태 확인 (completed 될 때까지 반복)
$NLM studio status <NOTEBOOK_ID>

# 다운로드
$NLM download slide-deck <NOTEBOOK_ID> --output "downloads/output.pdf"
```

### 7.5 한글 요약 질의
```bash
$NLM query notebook <NOTEBOOK_ID> "15개 슬라이드에 맞게 각각 2-3문장으로 요약해줘"
```

### 7.6 전체 프로시저 (End-to-End)
```bash
# ===== 1. 인증 =====
$NLM login -p default

# ===== 2. 노트북 생성 =====
$NLM notebook create "요추간판 탈출증 수술: 최신 지견"
# → NOTEBOOK_ID 획득 (예: 32ba5081-6e8e-4ed1-adae-0c283a2a5b02)

# ===== 3. 소스 추가 =====
$NLM source add <NOTEBOOK_ID> --url "https://url1.com" --wait
$NLM source add <NOTEBOOK_ID> --url "https://url2.com" --wait

# ===== 4. 슬라이드 생성 =====
$NLM slides create <NOTEBOOK_ID> --language ko --confirm

# ===== 5. 상태 확인 (completed 될 때까지) =====
$NLM studio status <NOTEBOOK_ID>

# ===== 6. 다운로드 =====
$NLM download slide-deck <NOTEBOOK_ID> --output "downloads/output.pdf"

# ===== 7. PDF → PPTX 변환 =====
cd D:/Entertainments/DevEnvironment/notebooklm
python -c "from pdf_to_pptx import pdf_to_pptx; pdf_to_pptx('downloads/output.pdf', 'downloads/output.pptx')"

# ===== 8. 한글 요약 획득 =====
$NLM query notebook <NOTEBOOK_ID> "15개 슬라이드에 맞게 각각 2-3문장으로 요약해줘"

# ===== 9. PPTX에 한글 노트 추가 (Python) =====
python -c "
from pptx import Presentation
notes = ['슬라이드1 내용', '슬라이드2 내용', ...]  # 위에서 얻은 요약
prs = Presentation('downloads/output.pptx')
for i, slide in enumerate(prs.slides):
    if i < len(notes):
        slide.notes_slide.notes_text_frame.text = notes[i]
prs.save('downloads/output_한글노트.pptx')
"
```

---

## 8. 트러블슈팅

### MCP 400 Bad Request 오류
MCP 서버 인증 버그 (GitHub Issue #28):
```bash
# nlm CLI로 대체 사용
$NLM login -p default
$NLM notebook list
```

### 인증 만료 (RPC Error 16)
```bash
python refresh_auth_v2.py  # 브라우저 로그인
```

### 다운로드 403 에러
- MCP download_artifact 대신 download_helper.py 사용
- 또는 nlm CLI: `$NLM download slide-deck <ID> --output "file.pdf"`

### PDF 텍스트 추출 안됨
- NotebookLM 슬라이드는 이미지 기반 PDF
- OCR 대신 notebook_query로 한글 요약 요청:
  ```bash
  $NLM query notebook <ID> "한글로 요약해줘"
  ```

### Windows 콘솔 인코딩 오류
nlm CLI에서 유니코드 문자(✓, ⚠) 출력 시 `UnicodeEncodeError` 발생
- **실제 작업은 정상 완료됨**
- 오류 메시지의 `locals` 부분에서 결과 확인 가능

---

## 9. 필수 패키지

```bash
pip install python-pptx PyMuPDF playwright deep-translator requests notebooklm-mcp-cli
npx playwright install chromium
```

---

## 10. 관련 문서

- Noterang 에이전트: `./noterang/README.md`
- Conductor 통합: `./noterang/CONDUCTOR.md`
- 프로젝트 README: `./README.md`

---
*Last updated: 2026-02-03*
*Generated by Claude Code - NotebookLM Automation System*
