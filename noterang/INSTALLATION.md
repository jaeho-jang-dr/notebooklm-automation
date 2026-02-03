# Noterang (노트랑) 설치 완료 ✅

## 설치 위치

### Agent 스킬
```
D:\Entertainments\DevEnvironment\skills\noterang\
├── noterang.py              # 메인 에이전트 코드
├── __init__.py             # Python 패키지 초기화
├── skill.json              # 스킬 메타데이터
├── README.md               # 사용 설명서
├── CONDUCTOR.md            # Conductor 통합 가이드
└── INSTALLATION.md         # 이 파일
```

### 작업 디렉토리
```
D:\Entertainments\DevEnvironment\notebooklm\
├── *.py                    # 유틸리티 스크립트들
├── *.json                  # 노트북 데이터 및 아티팩트 정보
├── *.md                    # 가이드 문서들
└── [future downloads]      # 다운로드된 콘텐츠가 여기 저장됨
```

## 사용 가능한 기능

### 1. 노트북 관리
- ✅ 노트북 목록 조회
- ✅ 최신 노트북 찾기
- ✅ 새 노트북 생성
- ✅ 노트북 삭제
- ✅ 노트북 이름 변경

### 2. 소스 관리
- ✅ URL 소스 추가
- ✅ 파일 소스 추가 (PDF, DOCX, TXT 등)
- ✅ YouTube 비디오 추가
- ✅ 텍스트 직접 추가
- ✅ Google Drive 동기화

### 3. AI 콘텐츠 생성
- ✅ 인포그래픽
- ✅ 오디오 팟캐스트
- ✅ 슬라이드 덱
- ✅ 퀴즈
- ✅ 플래시카드
- ✅ 보고서
- ✅ 데이터 테이블
- ✅ 비디오 개요
- ✅ 마인드맵

### 4. 대화형 기능
- ✅ 노트북 질의응답
- ✅ 자동 연구
- ✅ 소스 자동 수집

## 인증 상태

✅ NotebookLM 인증 완료
- Auth file: `~/.notebooklm-mcp-cli/auth.json`
- Session ID: 2017819530828417667
- 계정: drjang00@gmail.com
- 쿠키: 22개 저장됨

## 현재 데이터

### NotebookLM 계정 정보
- 총 노트북: 153개
- 최신 노트북: "n8n 마스터 가이드: 설치부터 AI 통합까지 통합 기본서"
- 마지막 수정: 2026-02-02 01:48:22 (UTC)

### 생성된 콘텐츠
- 인포그래픽 (진행 완료)
  - Notebook ID: 492d2a27-9f5a-4230-9cc4-69f3f3a6b0d7
  - Artifact ID: 1dbc9f7c-5c75-477a-b07f-21c60dd8a92d
  - 상태: 생성 완료
  - 확인: https://notebooklm.google.com/notebook/492d2a27-9f5a-4230-9cc4-69f3f3a6b0d7

## 사용 방법

### 방법 1: CLI로 사용
```bash
# 노트북 목록
python D:/Entertainments/DevEnvironment/skills/noterang/noterang.py list

# 최신 노트북
python D:/Entertainments/DevEnvironment/skills/noterang/noterang.py latest

# 인포그래픽 생성
python D:/Entertainments/DevEnvironment/skills/noterang/noterang.py infographic --notebook-id <ID>
```

### 방법 2: Python API로 사용
```python
import sys
sys.path.append("D:/Entertainments/DevEnvironment/skills")

from noterang import NoterangAgent
import asyncio

agent = NoterangAgent()

# 최신 노트북 조회
latest = agent.get_latest_notebook()
print(latest)

# 인포그래픽 생성
result = asyncio.run(agent.create_infographic(latest['id']))
print(result)
```

### 방법 3: Claude Code에서 자연어로 사용
```
"noterang으로 최신 노트북 보여줘"
"noterang으로 인포그래픽 만들어줘"
"noterang으로 오디오 팟캐스트 생성해줘"
```

## Conductor 통합

Conductor는 Noterang을 자동으로 인식합니다:
- "노트랑", "NotebookLM" 언급 시 자동 활성화
- 모든 작업 결과는 `D:/Entertainments/DevEnvironment/notebooklm/` 에 저장
- 다른 프로젝트에서도 사용 가능

## 다른 프로젝트에서 사용하기

Noterang은 상위 디렉토리에 저장되어 있어 어떤 프로젝트에서도 사용 가능합니다:

```python
# 어떤 프로젝트에서든
import sys
sys.path.append("D:/Entertainments/DevEnvironment/skills")

from noterang import NoterangAgent

agent = NoterangAgent()
# ... 사용
```

## 문제 해결

### 인증 만료 시
```bash
notebooklm-mcp-auth
```

### 모듈을 찾을 수 없을 때
```bash
pip install notebooklm-mcp-cli
```

### 다운로드 실패 시
NotebookLM 웹사이트에서 직접 다운로드:
```
https://notebooklm.google.com/notebook/<NOTEBOOK_ID>
```

## 다음 단계

1. ✅ Noterang 에이전트 설치 완료
2. ✅ 작업 디렉토리 설정
3. ✅ NotebookLM 인증 완료
4. ✅ 테스트 완료 (최신 노트북 조회, 인포그래픽 생성)
5. ⏭️ 다른 콘텐츠 유형 테스트
6. ⏭️ Conductor 자동화 규칙 설정
7. ⏭️ 다른 프로젝트에서 활용

## 지원

- README: `D:/Entertainments/DevEnvironment/skills/noterang/README.md`
- Conductor 가이드: `D:/Entertainments/DevEnvironment/skills/noterang/CONDUCTOR.md`
- 작업 디렉토리: `D:/Entertainments/DevEnvironment/notebooklm/`

---

**Noterang (노트랑) v1.0.0**
Antigravity x Claude Sonnet 4.5
2026-02-02
