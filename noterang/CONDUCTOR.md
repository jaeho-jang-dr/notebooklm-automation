# Conductor Integration for Noterang

## Agent Overview

**Name**: Noterang (노트랑)
**Type**: 글로벌 에이전트 스킬 (프로젝트 상위 레벨)
**Scope**: DevEnvironment 하위 모든 프로젝트에서 사용 가능
**Purpose**: Google NotebookLM 완전 제어

### 중요: 한글 우선 정책
> **모든 아티팩트 생성 시 `language="ko"` 필수!**

```python
mcp__notebooklm__studio_create(
    notebook_id="...",
    artifact_type="slide_deck",
    language="ko",  # 항상 포함!
    confirm=True
)
```

### 프로젝트 위치
```
D:/Entertainments/DevEnvironment/notebooklm/   # 메인 프로젝트 디렉토리
├── noterang/                                   # 에이전트 코드
├── NOTEBOOKLM_AUTOMATION.md                    # 자동화 가이드
├── downloads/                                  # 다운로드 폴더
└── (스크립트들)
```

## Conductor Memory Instructions

Conductor는 이 에이전트를 다음과 같이 기억하고 활용해야 합니다:

### 1. 언제 Noterang을 사용하는가

다음 상황에서 Noterang을 자동으로 호출:
- 사용자가 "노트북LM", "NotebookLM", "노트랑" 언급 시
- 연구 자료 정리가 필요할 때
- AI 콘텐츠 생성이 필요할 때 (인포그래픽, 오디오, 슬라이드 등)
- 문서/웹페이지를 분석하고 요약해야 할 때
- 팟캐스트나 프레젠테이션이 필요할 때

### 2. Noterang의 주요 워크플로우

#### 워크플로우 1: 연구 자료 수집 및 분석
```
1. 새 노트북 생성 (주제명)
2. 관련 URL/파일 소스 추가
3. 노트북에 질문하여 인사이트 추출
4. 결과를 D:/Entertainments/DevEnvironment/notebooklm/ 에 저장
```

#### 워크플로우 2: 콘텐츠 자동 생성
```
1. 기존 노트북 선택 (또는 최신 노트북 사용)
2. 원하는 아티팩트 생성 (인포그래픽/오디오/슬라이드/퀴즈)
3. NotebookLM에서 생성 완료 대기
4. 다운로드 링크 제공
```

#### 워크플로우 3: 자동 연구 시스템
```
1. 연구 주제 입력
2. 자동으로 관련 소스 검색 및 추가
3. AI 분석 및 요약
4. 최종 보고서 생성
```

### 3. Conductor 호출 예시

```python
# Example 1: 최신 노트북으로 인포그래픽 생성
conductor.execute_skill("noterang", {
    "action": "create_infographic",
    "notebook": "latest"
})

# Example 2: 새 연구 프로젝트 시작
conductor.execute_skill("noterang", {
    "action": "create_and_populate",
    "title": "AI 영상 제작 연구",
    "sources": ["url1", "url2", "file1.pdf"]
})

# Example 3: 노트북 질의
conductor.execute_skill("noterang", {
    "action": "query",
    "notebook_id": "abc123",
    "question": "핵심 인사이트는?"
})
```

### 4. 결과 저장 및 기억

Conductor는 Noterang의 모든 작업 결과를 다음 위치에 저장:
```
D:/Entertainments/DevEnvironment/notebooklm/
```

저장되는 정보:
- 생성된 아티팩트 메타데이터 (JSON)
- 질의응답 기록 (JSONL)
- 노트북 목록 스냅샷
- 다운로드된 콘텐츠

### 5. 다른 프로젝트에서 사용

Noterang은 notebooklm 프로젝트 내에 있어 모든 프로젝트에서 사용 가능:

```
D:/Entertainments/DevEnvironment/notebooklm/noterang/
```

다른 프로젝트에서 import:
```python
import sys
sys.path.append("D:/Entertainments/DevEnvironment/notebooklm")

from noterang import NoterangAgent

agent = NoterangAgent()
```

### 6. Conductor 자동화 규칙

Conductor는 다음 패턴을 인식하고 자동으로 Noterang 실행:

| 사용자 입력 | Conductor 액션 | language |
|------------|---------------|----------|
| "연구 자료 정리해줘" | 새 노트북 생성 + 소스 추가 | - |
| "이거 요약해줘" | NotebookLM에 추가 + 쿼리 | ko |
| "팟캐스트 만들어줘" | 오디오 생성 | **ko** |
| "프레젠테이션 필요해" | 슬라이드 생성 | **ko** |
| "인포그래픽으로 보여줘" | 인포그래픽 생성 | **ko** |
| "퀴즈 만들어줘" | 퀴즈 생성 | **ko** |
| "플래시카드 만들어줘" | 플래시카드 생성 | **ko** |

> **모든 콘텐츠 생성 시 `language="ko"` 자동 적용!**

### 7. 상태 추적

Conductor는 Noterang의 상태를 추적:
- 마지막 사용한 노트북 ID
- 생성 중인 아티팩트 목록
- 실패한 작업 (재시도 필요)
- 사용 통계

### 8. 에러 처리

Noterang 에러 발생 시 Conductor의 대응:

1. **인증 에러**: 자동으로 `notebooklm-mcp-auth` 실행 안내
2. **네트워크 에러**: 3번 재시도 후 사용자에게 알림
3. **생성 실패**: NotebookLM 웹 링크 제공
4. **다운로드 실패**: 웹에서 수동 다운로드 안내

### 9. 성능 최적화

- 노트북 목록은 5분마다 캐싱
- 인증 토큰은 자동 갱신
- 대량 작업은 비동기 처리
- 결과는 로컬에 저장하여 재사용

### 10. 보안 및 개인정보

- 인증 정보는 `~/.notebooklm-mcp-cli/auth.json`에 암호화 저장
- 생성된 콘텐츠는 로컬에만 저장
- Google 계정 정보는 절대 로그에 기록하지 않음

## Integration Checklist

- [x] Agent 코드 작성
- [x] Skill 메타데이터 정의
- [x] 작업 디렉토리 설정
- [x] README 문서화
- [x] Conductor 통합 가이드
- [x] 상위 디렉토리 배치
- [ ] Conductor 테스트
- [ ] 다른 프로젝트에서 테스트

## 다음 단계

1. Conductor에 Noterang 등록
2. 자동화 규칙 테스트
3. 에러 처리 검증
4. 성능 모니터링
5. 문서 업데이트
