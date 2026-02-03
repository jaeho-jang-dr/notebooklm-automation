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

## 중요 규칙

| 문제 | 해결책 |
|------|--------|
| nlm CLI 버그 | **run_browser() 메서드 사용** |
| 다운로드 403 | **Playwright 브라우저 사용** |
| 슬라이드 언어 | **반드시 한글 "ko"** |
| 로그인 필요 | `python -m noterang login --show` |

## 경로

- 다운로드: `G:/내 드라이브/notebooklm/`
- 인증: `~/.notebooklm-mcp-cli/`
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

API 키는 `noterang_config.json`에서 관리 (git에 커밋하지 않음)
