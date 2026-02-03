## Development Environment
- OS: Windows 10.0.26200
- Shell: Git Bash
- Path format: Windows (use forward slashes in Git Bash)
- File system: Case-insensitive
- Line endings: CRLF (configure Git autocrlf)

## 노트랑 (Noterang) - NotebookLM 완전 자동화

### 핵심 명령
```bash
# 전체 자동화 실행
python noterang_auto.py

# 또는 Python에서
from noterang_auto import run_full_automation
result = run_full_automation(
    title="주제",
    research_queries=["검색어1", "검색어2"],
    focus="초점",
    language="ko"
)
```

### 워크플로우 (완전 자동 - 사용자 개입 없음)
1. **자동 로그인** - `ensure_auth()` (공식 도구 + Chrome 프로필)
2. **인증 동기화** - `sync_auth()` (profiles/default/ 동기화)
3. **연구 수집** - `nlm research` (멀티에이전트 모니터링)
4. **슬라이드 생성** - `nlm slides create` (타임아웃 시 헬퍼 에이전트)
5. **다운로드** - `download_via_browser()` (CLI 403 버그 우회)
6. **PPTX 변환** - `pdf_to_pptx()`

### 중요 해결책 (기억할 것)
| 문제 | 해결책 |
|------|--------|
| 인증 만료 | `sync_auth()` 호출 |
| 다운로드 403 | Playwright 브라우저 사용 (CLI 사용 금지) |
| 로그인 필요 | 자동 로그인 (사용자에게 요청 금지) |
| 타임아웃 | 헬퍼 에이전트 자동 투입 |

### 경로
- 다운로드: `G:/내 드라이브/notebooklm/`
- 메모리: `G:/내 드라이브/notebooklm/agent_memory.json`

### 멀티 에이전트 시스템
- `main`: 메인 작업
- `monitor`: 진행 감시
- `helper`: 타임아웃 시 투입
- `recovery`: 에러 시 투입

## Playwright MCP Guide

File paths:
- Screenshots: `./CCimages/screenshots/`
- PDFs: `./CCimages/pdfs/`

Browser version fix:
- Error: "Executable doesn't exist at chromium-XXXX" → Version mismatch
- v1.0.12+ uses Playwright 1.57.0, requires chromium-1200 with `chrome-win64/` structure
- Quick fix: `npx playwright@latest install chromium`
- Manual symlink (if needed): `cd ~/AppData/Local/ms-playwright && cmd //c "mklink /J chromium-1200 chromium-1181"`
