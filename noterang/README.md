# Noterang (노트랑) - NotebookLM Control Agent

Google NotebookLM을 완벽하게 컨트롤하는 AI 에이전트 스킬

## 중요: 한글 우선 정책

> **모든 아티팩트 생성 시 반드시 `language="ko"` 파라미터를 포함할 것!**
>
> NotebookLM에서 생성하는 모든 콘텐츠(슬라이드, 오디오, 인포그래픽, 퀴즈 등)는
> 기본적으로 **한국어**로 생성해야 합니다.

```python
# 올바른 사용법 (항상 language="ko" 포함)
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",
    language="ko",  # 필수!
    confirm=True
)
```

## 개요

Noterang은 NotebookLM의 모든 기능을 프로그래밍 방식으로 제어할 수 있는 강력한 에이전트입니다. 노트북 관리부터 AI 콘텐츠 생성까지 모든 것을 자동화할 수 있습니다.

## 주요 기능

### 📚 노트북 관리
- 노트북 목록 조회
- 최신 노트북 찾기
- 새 노트북 생성
- 노트북 이름 변경
- 노트북 삭제

### 📄 소스 관리
- URL 소스 추가
- 파일 소스 추가 (PDF, DOCX, TXT 등)
- YouTube 비디오 추가
- 텍스트 직접 추가
- Google Drive 동기화

### 🎨 AI 콘텐츠 생성
- **인포그래픽** - 시각적 요약 생성
- **오디오 팟캐스트** - AI 대화형 오디오 생성
- **슬라이드 덱** - 프레젠테이션 자동 생성
- **퀴즈** - 학습용 퀴즈 생성
- **플래시카드** - 암기 카드 생성
- **보고서** - 상세 보고서 작성
- **데이터 테이블** - 구조화된 데이터 정리
- **비디오 개요** - 비디오 요약 생성
- **마인드맵** - 개념 연결도 생성

### 💬 대화형 질의응답
- 노트북 콘텐츠에 대해 질문하고 답변 받기
- 연구 자동화
- 소스 자동 가져오기

## 설치

### 1. NotebookLM MCP CLI 설치
```bash
pip install notebooklm-mcp-cli
```

### 2. 인증 설정
```bash
notebooklm-mcp-auth
```

### 3. Noterang 설치
이 skill은 다음 위치에 설치됩니다:
```
D:\Entertainments\DevEnvironment\notebooklm\noterang\
```

## 사용법

### CLI 사용

```bash
# 노트북 목록 조회
python noterang.py list

# 최신 노트북 조회
python noterang.py latest

# 새 노트북 생성
python noterang.py create --title "AI 연구 노트"

# 인포그래픽 생성
python noterang.py infographic --notebook-id <NOTEBOOK_ID>

# 오디오 팟캐스트 생성
python noterang.py audio --notebook-id <NOTEBOOK_ID>

# 슬라이드 생성
python noterang.py slides --notebook-id <NOTEBOOK_ID>

# 퀴즈 생성
python noterang.py quiz --notebook-id <NOTEBOOK_ID>

# URL 소스 추가
python noterang.py add-url --notebook-id <NOTEBOOK_ID> --url "https://example.com"

# 파일 소스 추가
python noterang.py add-file --notebook-id <NOTEBOOK_ID> --file "paper.pdf"

# 질문하기
python noterang.py query --notebook-id <NOTEBOOK_ID> --question "주요 내용이 뭐야?"
```

### Python API 사용

```python
from noterang import NoterangAgent
import asyncio

# 에이전트 초기화
agent = NoterangAgent()

# 노트북 목록
notebooks = agent.list_notebooks(limit=10)
print(notebooks)

# 최신 노트북
latest = agent.get_latest_notebook()
print(latest)

# 새 노트북 생성
new_notebook = agent.create_notebook("AI 영상 제작 연구")
notebook_id = new_notebook['id']

# URL 소스 추가
asyncio.run(agent.add_url_source(
    notebook_id,
    "https://example.com/article"
))

# 인포그래픽 생성
result = asyncio.run(agent.create_infographic(notebook_id))
print(f"Infographic created: {result['artifact_id']}")

# 질문하기
answer = asyncio.run(agent.query_notebook(
    notebook_id,
    "이 문서의 핵심 내용은 무엇인가요?"
))
print(answer)
```

### Claude Code에서 사용

Claude Code에서 자연어로 요청하면 됩니다:

```
"noterang을 사용해서 최신 노트북으로 인포그래픽 만들어줘"
"noterang으로 새 노트북 만들고 이 PDF 파일들 추가해줘"
"noterang으로 이 노트북에서 오디오 팟캐스트 생성해줘"
```

## 작업 디렉토리

모든 생성된 파일과 다운로드는 다음 위치에 저장됩니다:
```
D:\Entertainments\DevEnvironment\notebooklm\
```

## 파일 구조

```
notebooklm/
├── infographic_<id>.json       # 인포그래픽 정보
├── audio_<id>.json            # 오디오 정보
├── slides_<id>.json           # 슬라이드 정보
├── quiz_<id>.json             # 퀴즈 정보
├── qa_<notebook_id>.jsonl     # 질의응답 기록
└── notebooks_list.json        # 노트북 목록
```

## Conductor 통합

이 에이전트는 Conductor 시스템에서 기억되고 활용됩니다:

```python
# Conductor가 Noterang을 호출하는 예시
conductor.use_skill("noterang", {
    "action": "create_infographic",
    "notebook_id": "latest"
})
```

## 주요 메서드

### NoterangAgent

| 메서드 | 설명 | 비동기 |
|--------|------|--------|
| `list_notebooks(limit)` | 노트북 목록 조회 | ❌ |
| `get_latest_notebook()` | 최신 노트북 조회 | ❌ |
| `create_notebook(title)` | 새 노트북 생성 | ❌ |
| `create_infographic(notebook_id)` | 인포그래픽 생성 | ✅ |
| `create_audio(notebook_id)` | 오디오 생성 | ✅ |
| `create_slides(notebook_id)` | 슬라이드 생성 | ✅ |
| `create_quiz(notebook_id)` | 퀴즈 생성 | ✅ |
| `add_url_source(notebook_id, url)` | URL 추가 | ✅ |
| `add_file_source(notebook_id, file_path)` | 파일 추가 | ✅ |
| `query_notebook(notebook_id, question)` | 질문하기 | ✅ |
| `save_notebook_list(filename)` | 목록 저장 | ❌ |

## 완전 자동화 워크플로우 (2026-02-02 업데이트)

두 가지 방법으로 NotebookLM을 자동화할 수 있습니다:
1. **MCP 도구** - Claude Code에서 직접 호출 (권장)
2. **nlm CLI** - MCP 오류 시 대안

---

### 방법 1: MCP 도구 사용 (권장)

```python
# Claude Code에서 직접 호출

# 1. 인증 확인
mcp__notebooklm__refresh_auth()
mcp__notebooklm__notebook_list(max_results=5)

# 2. 아티팩트 생성 (항상 language="ko" 포함!)
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",
    language="ko",  # 필수!
    confirm=True
)

# 3. 상태 확인 (URL 획득)
mcp__notebooklm__studio_status(notebook_id="...")

# 4. 한글 요약 요청
mcp__notebooklm__notebook_query(
    notebook_id="...",
    query="모든 내용을 한국어로 상세하게 요약해줘"
)
```

---

### 방법 2: nlm CLI 사용 (MCP 오류 시)

MCP에서 400 Bad Request 오류가 발생하면 nlm CLI를 직접 사용합니다.

#### 2-1. CLI 인증 (최초 1회)
```bash
# nlm 경로 (Windows)
NLM="C:/Users/antigravity/AppData/Roaming/Python/Python313/Scripts/nlm.exe"

# 로그인 (Chrome 브라우저 열림)
$NLM login -p default
```

#### 2-2. 노트북 생성 및 소스 추가
```bash
# 노트북 목록 조회
$NLM notebook list

# 새 노트북 생성
$NLM notebook create "노트북 제목"

# URL 소스 추가
$NLM source add <NOTEBOOK_ID> --url "https://example.com" --wait

# 파일 소스 추가
$NLM source add <NOTEBOOK_ID> --file "document.pdf" --wait
```

#### 2-3. 슬라이드 생성
```bash
# 한글 슬라이드 생성 (항상 --language ko 포함!)
$NLM slides create <NOTEBOOK_ID> --language ko --confirm

# 상태 확인 (completed 될 때까지)
$NLM studio status <NOTEBOOK_ID>

# 다운로드
$NLM download slide-deck <NOTEBOOK_ID> --output "downloads/output.pdf"
```

#### 2-4. 한글 요약 질의
```bash
# 노트북에 질문하기
$NLM query notebook <NOTEBOOK_ID> "15개 슬라이드에 맞게 각각 2-3문장으로 요약해줘"
```

---

### 핵심 스크립트 (notebooklm/ 디렉토리)

| 스크립트 | 용도 |
|----------|------|
| `refresh_auth_v2.py` | 브라우저로 MCP 인증 갱신 |
| `download_helper.py` | Playwright로 파일 다운로드 (403 우회) |
| `pdf_to_pptx.py` | PDF→PPTX 변환 및 합치기 |
| `add_korean_notes.py` | PPTX에 한글 노트 추가 |

---

### 전체 자동화 프로시저 (End-to-End)

```bash
# ===== 1. 인증 =====
# MCP 인증
python D:/Entertainments/DevEnvironment/notebooklm/refresh_auth_v2.py
# 또는 CLI 인증
$NLM login -p default

# ===== 2. 노트북 생성 =====
$NLM notebook create "주제 제목"
# → NOTEBOOK_ID 획득

# ===== 3. 소스 추가 (URL 여러 개) =====
$NLM source add <NOTEBOOK_ID> --url "https://url1.com" --wait
$NLM source add <NOTEBOOK_ID> --url "https://url2.com" --wait

# ===== 4. 슬라이드 생성 =====
$NLM slides create <NOTEBOOK_ID> --language ko --confirm

# ===== 5. 상태 확인 (completed 될 때까지 반복) =====
$NLM studio status <NOTEBOOK_ID>

# ===== 6. 다운로드 =====
$NLM download slide-deck <NOTEBOOK_ID> --output "downloads/output.pdf"

# ===== 7. PDF → PPTX 변환 =====
cd D:/Entertainments/DevEnvironment/notebooklm
python -c "
from pdf_to_pptx import pdf_to_pptx
pdf_to_pptx('downloads/output.pdf', 'downloads/output.pptx')
"

# ===== 8. 한글 요약 획득 =====
$NLM query notebook <NOTEBOOK_ID> "15개 슬라이드에 맞게 각각 2-3문장으로 요약해줘"

# ===== 9. PPTX에 한글 노트 추가 =====
# Python으로 pptx 라이브러리 사용하여 notes_slide에 추가
```

---

### 출력 디렉토리

```
D:/Entertainments/DevEnvironment/notebooklm/downloads/
├── *.pdf                    # 원본 슬라이드 (NotebookLM 생성)
├── *.pptx                   # PPTX 변환본
├── *_한글노트.pptx          # 한글 노트 포함 최종본
├── *_통합.pptx              # 여러 슬라이드 합침
└── *_자료.md                # 참고 자료
```

---

### 공유 문서

상세 가이드: `D:/Entertainments/DevEnvironment/notebooklm/NOTEBOOKLM_AUTOMATION.md`

---

## 문제 해결

### MCP 400 Bad Request 오류
MCP 서버에서 인증 관련 버그 발생 시 (GitHub Issue #28):
```bash
# nlm CLI로 대체 사용
$NLM login -p default
$NLM notebook list
```

### 인증 오류 (RPC Error 16)
```bash
# MCP 인증 갱신
cd D:/Entertainments/DevEnvironment/notebooklm
python refresh_auth_v2.py
```
브라우저가 열리면 Google 로그인 → 자동 저장

### Windows 콘솔 인코딩 오류
nlm CLI에서 유니코드 문자(✓) 출력 시 오류가 발생하지만, 실제 작업은 정상 완료됨.
오류 메시지의 locals 부분에서 결과 확인 가능.

### 모듈을 찾을 수 없음
```bash
pip install notebooklm-mcp-cli
```

### 다운로드 실패
NotebookLM 웹사이트에서 직접 다운로드:
```
https://notebooklm.google.com/notebook/<NOTEBOOK_ID>
```

## 라이선스

MIT License

## 제작자

Antigravity x Claude Sonnet 4.5

## 버전

1.0.0 - 2026-02-02
