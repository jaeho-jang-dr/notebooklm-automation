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

# 기존 노트북에서 슬라이드 재생성
python regenerate_slides.py

# 병렬 노트북 생성
python run_parallel.py
```

### 완전 자동화 워크플로우
```
1. 자동 로그인 → 2. 노트북 찾기/생성 → 3. 슬라이드 생성 (한글)
→ 4. 생성 완료 체크 → 5. PDF 다운로드 → 6. PPTX 변환
```

| 단계 | 함수/방법 | 비고 |
|------|-----------|------|
| 자동 로그인 | `ensure_auth()` | Chrome 프로필 + Playwright |
| 인증 동기화 | `sync_auth()` | profiles/default/ 동기화 |
| 노트북 찾기 | Playwright 텍스트 검색 | 이름으로 노트북 클릭 |
| 슬라이드 생성 | `create_korean_slides()` | **반드시 한글** 설정 |
| 생성 체크 | `check_slides_created()` | 모니터링 에이전트 |
| 다운로드 | `helper_agent_download()` | 헬퍼 에이전트 (3가지 방법 시도) |
| PPTX 변환 | `pdf_to_pptx()` | PyMuPDF + python-pptx |

### 중요 해결책 (반드시 기억)
| 문제 | 해결책 |
|------|--------|
| 인증 만료 | `sync_auth()` 호출 |
| 다운로드 403 | **Playwright 브라우저 사용** (CLI 사용 금지) |
| 로그인 필요 | 자동 로그인 시도 → 실패 시 브라우저 표시 |
| 타임아웃 | 헬퍼 에이전트 자동 투입 |
| 에러 발생 | 디버그 에이전트 스크린샷 저장 |
| 슬라이드 언어 | **반드시 한글(Korean)** 선택 |

### 경로 설정
```python
DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")  # Google Drive
AUTH_DIR = Path.home() / ".notebooklm-mcp-cli"
BROWSER_PROFILE = AUTH_DIR / "browser_profile"
```

### 멀티 에이전트 시스템
| 에이전트 | 역할 | 투입 시점 |
|----------|------|----------|
| `main` | 메인 작업 실행 | 항상 |
| `monitor` | 슬라이드 생성 감시 | 생성 중 |
| `helper` | 다운로드 전담 | 다운로드 시 |
| `debug` | 스크린샷/로그 | 에러 발생 시 |
| `recovery` | 에러 복구 | 실패 시 |

### 다운로드 방법 (3가지 시도)
```python
# 방법 1: 메뉴 버튼 클릭
menu_buttons = await page.query_selector_all('[aria-haspopup="menu"]')
await menu_btn.click()
download_item = await page.query_selector('[role="menuitem"]:has-text("Download")')

# 방법 2: 좌표 기반 (백업)
await page.mouse.click(1846, 365)  # 스튜디오 패널 more 버튼

# 방법 3: 키보드 단축키
await page.keyboard.press('Tab')  # 다운로드 버튼으로 이동
```

## 병렬 노트북 생성 (대량 생산용)

### 사용법
```python
from run_parallel import run_parallel
import asyncio

topics = [
    {"title": "족관절 염좌", "queries": ["염좌 원인", "염좌 치료", "염좌 재활"]},
    {"title": "족관절 골절", "queries": ["골절 원인", "골절 수술", "골절 재활"]},
]

results = asyncio.run(run_parallel(topics))
```

### 병렬/순차 처리
| 단계 | 병렬 여부 | 이유 |
|------|----------|------|
| 노트북 생성 | ✓ 병렬 | asyncio.gather() |
| 연구 수집 | ✓ 병렬 | 각 노트북 독립 |
| 슬라이드 생성 | ✓ 병렬 | 동시 요청 가능 |
| 다운로드 | ✗ 순차 | 브라우저 충돌 방지 |
| PPTX 변환 | ✗ 순차 | 다운로드 후 즉시 |

### 성공 사례
- 2026-02-03: 족관절 3종 (염좌, 골관절염, 골절) - 각 15슬라이드
- 저장 위치: `G:/내 드라이브/notebooklm/`

## MCP 서버 설정

### 설치된 MCP 서버
| 서버 | 명령 | 용도 |
|------|------|------|
| skillsmp | `skillsmp-mcp` | 71,000+ 스킬 검색/설치 |
| playwright | `npx @playwright/mcp@latest` | 브라우저 자동화 |
| playwright-stealth | `playwright-stealth-mcp-server` | 봇 감지 우회 |
| context7 | `npx -y @upstash/context7-mcp` | 라이브러리 문서 |
| stitch | `stitch-mcp` | Google Stitch UI/UX |

### API 키 설정
```json
{
  "skillsmp": {
    "env": { "SKILLSMP_API_KEY": "sk_live_skillsmp_..." }
  },
  "stitch": {
    "env": { "GOOGLE_CLOUD_PROJECT": "claude-stitch" }
  }
}
```

### MCP 관리 명령
```bash
claude mcp list                    # 서버 목록/상태
claude mcp add <name> -- <cmd>     # 서버 추가
claude mcp remove <name>           # 서버 제거
```

## Playwright 설정

### 파일 경로
- Screenshots: `./CCimages/screenshots/`
- PDFs: `./CCimages/pdfs/`

### 버전 문제 해결
```bash
# Chromium 버전 불일치 시
npx playwright@latest install chromium

# 수동 심볼릭 링크 (필요시)
cd ~/AppData/Local/ms-playwright
cmd //c "mklink /J chromium-1200 chromium-1181"
```

## Google Cloud 인증 (Stitch용)

```bash
# 로그인
gcloud auth login

# ADC 설정
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project claude-stitch
```
