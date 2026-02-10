#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 에이전트 매니저
- 작업 모니터링 및 타임아웃 감지
- 추가 에이전트 자동 투입
- 버그 발생 시 복구 에이전트 실행
"""
import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"
    TIMEOUT = "timeout"

class AgentType(Enum):
    MAIN = "main"           # 메인 작업 에이전트
    MONITOR = "monitor"     # 모니터링 에이전트
    HELPER = "helper"       # 보조 에이전트 (타임아웃 시 투입)
    RECOVERY = "recovery"   # 복구 에이전트 (버그 발생 시 투입)

@dataclass
class AgentTask:
    """에이전트 작업 정보"""
    task_id: str
    task_type: str
    params: Dict[str, Any]
    status: AgentStatus = AgentStatus.IDLE
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    retries: int = 0

@dataclass
class Agent:
    """에이전트 정보"""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[AgentTask] = None
    created_at: float = field(default_factory=time.time)

class AgentMemory:
    """에이전트 메모리 - 상태 및 학습 정보 저장"""

    def __init__(self, memory_path: Path = None):
        self.memory_path = memory_path or Path("G:/내 드라이브/notebooklm/agent_memory.json")
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "tasks_history": [],
            "error_patterns": {},
            "timeout_thresholds": {
                "slides_create": 300,  # 5분
                "research": 120,       # 2분
                "download": 60,        # 1분
            },
            "recovery_strategies": {},
            "performance_stats": {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "avg_completion_time": {},
            }
        }

    def save(self):
        with open(self.memory_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def record_task(self, task: AgentTask):
        """작업 기록"""
        record = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "duration": (task.completed_at - task.started_at) if task.completed_at and task.started_at else None,
            "error": task.error,
            "timestamp": datetime.now().isoformat()
        }
        self.data["tasks_history"].append(record)

        # 성능 통계 업데이트
        stats = self.data["performance_stats"]
        stats["total_tasks"] += 1
        if task.status == AgentStatus.COMPLETED:
            stats["successful_tasks"] += 1
        elif task.status == AgentStatus.ERROR:
            stats["failed_tasks"] += 1

        # 평균 완료 시간 업데이트
        if record["duration"] and task.task_type:
            if task.task_type not in stats["avg_completion_time"]:
                stats["avg_completion_time"][task.task_type] = []
            stats["avg_completion_time"][task.task_type].append(record["duration"])

        self.save()

    def record_error(self, error_type: str, error_msg: str, recovery_action: str = None):
        """에러 패턴 기록"""
        if error_type not in self.data["error_patterns"]:
            self.data["error_patterns"][error_type] = {
                "count": 0,
                "examples": [],
                "recovery_actions": []
            }

        pattern = self.data["error_patterns"][error_type]
        pattern["count"] += 1
        pattern["examples"].append({
            "message": error_msg[:200],
            "timestamp": datetime.now().isoformat()
        })

        if recovery_action:
            if recovery_action not in pattern["recovery_actions"]:
                pattern["recovery_actions"].append(recovery_action)

        self.save()

    def get_timeout_threshold(self, task_type: str) -> int:
        """작업 타입별 타임아웃 임계값 반환"""
        return self.data["timeout_thresholds"].get(task_type, 180)

    def update_timeout_threshold(self, task_type: str, new_value: int):
        """타임아웃 임계값 업데이트 (학습)"""
        self.data["timeout_thresholds"][task_type] = new_value
        self.save()

    def get_recovery_strategy(self, error_type: str) -> Optional[str]:
        """에러 타입에 대한 복구 전략 반환"""
        if error_type in self.data["error_patterns"]:
            actions = self.data["error_patterns"][error_type].get("recovery_actions", [])
            if actions:
                return actions[0]  # 가장 최근 성공한 복구 전략
        return None


class AgentManager:
    """멀티 에이전트 매니저"""

    def __init__(self):
        self.memory = AgentMemory()
        self.agents: Dict[str, Agent] = {}
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.running = False
        self._agent_counter = 0
        self._lock = threading.Lock()

    def _generate_agent_id(self, agent_type: AgentType) -> str:
        with self._lock:
            self._agent_counter += 1
            return f"{agent_type.value}_{self._agent_counter}_{int(time.time())}"

    def create_agent(self, agent_type: AgentType) -> Agent:
        """새 에이전트 생성"""
        agent_id = self._generate_agent_id(agent_type)
        agent = Agent(agent_id=agent_id, agent_type=agent_type)
        self.agents[agent_id] = agent
        print(f"  [에이전트] {agent_type.value} 생성: {agent_id[:20]}...")
        return agent

    def spawn_helper_agent(self, task: AgentTask, reason: str) -> Agent:
        """헬퍼 에이전트 투입"""
        print(f"\n  ⚡ 헬퍼 에이전트 투입 (사유: {reason})")
        helper = self.create_agent(AgentType.HELPER)
        helper.current_task = task
        helper.status = AgentStatus.RUNNING
        return helper

    def spawn_recovery_agent(self, error: str, task: AgentTask) -> Agent:
        """복구 에이전트 투입"""
        print(f"\n  🔧 복구 에이전트 투입 (에러: {error[:50]}...)")
        recovery = self.create_agent(AgentType.RECOVERY)
        recovery.current_task = task
        recovery.status = AgentStatus.RUNNING

        # 복구 전략 확인
        strategy = self.memory.get_recovery_strategy(type(error).__name__ if isinstance(error, Exception) else "unknown")
        if strategy:
            print(f"    학습된 복구 전략 적용: {strategy}")

        return recovery

    async def monitor_task(
        self,
        task: AgentTask,
        check_fn: Callable[[], bool],
        check_interval: int = 10,
        on_timeout: Callable = None,
        on_error: Callable = None
    ) -> bool:
        """
        작업 모니터링 - 주기적 체크, 타임아웃/에러 시 에이전트 투입

        Args:
            task: 모니터링할 작업
            check_fn: 완료 여부 체크 함수 (True 반환 시 완료)
            check_interval: 체크 간격 (초)
            on_timeout: 타임아웃 시 콜백
            on_error: 에러 시 콜백
        """
        task.status = AgentStatus.RUNNING
        task.started_at = time.time()

        timeout = self.memory.get_timeout_threshold(task.task_type)
        helper_spawned = False
        check_count = 0

        print(f"\n  [모니터] 작업 감시 시작: {task.task_type}")
        print(f"    타임아웃: {timeout}초, 체크 간격: {check_interval}초")

        while True:
            try:
                elapsed = time.time() - task.started_at
                check_count += 1

                # 완료 체크
                if check_fn():
                    task.status = AgentStatus.COMPLETED
                    task.completed_at = time.time()
                    self.memory.record_task(task)
                    print(f"\n  ✓ 작업 완료! (소요시간: {int(elapsed)}초)")
                    return True

                # 타임아웃 체크
                if elapsed > timeout:
                    if not helper_spawned:
                        task.status = AgentStatus.TIMEOUT
                        print(f"\n  ⏰ 타임아웃 감지 ({int(elapsed)}초 > {timeout}초)")

                        # 헬퍼 에이전트 투입
                        helper = self.spawn_helper_agent(task, "timeout")
                        helper_spawned = True

                        if on_timeout:
                            try:
                                await on_timeout(task, helper)
                            except Exception as e:
                                print(f"    헬퍼 에이전트 오류: {e}")

                        # 타임아웃 임계값 학습 (10% 증가)
                        new_timeout = int(timeout * 1.1)
                        self.memory.update_timeout_threshold(task.task_type, new_timeout)
                        print(f"    타임아웃 임계값 학습: {timeout}초 → {new_timeout}초")

                    # 추가 대기 (최대 2배까지)
                    if elapsed > timeout * 2:
                        task.status = AgentStatus.ERROR
                        task.error = "Extended timeout exceeded"
                        self.memory.record_task(task)
                        return False

                # 진행 상황 출력
                if check_count % 3 == 0:
                    print(f"\r    체크 #{check_count}: {int(elapsed)}초 경과...", end="", flush=True)

                await asyncio.sleep(check_interval)

            except Exception as e:
                task.status = AgentStatus.ERROR
                task.error = str(e)
                task.completed_at = time.time()

                print(f"\n  ❌ 에러 발생: {e}")

                # 복구 에이전트 투입
                recovery = self.spawn_recovery_agent(str(e), task)

                # 에러 패턴 기록
                self.memory.record_error(
                    type(e).__name__,
                    str(e),
                    "retry" if task.retries < 3 else "skip"
                )

                if on_error:
                    try:
                        result = await on_error(task, recovery, e)
                        if result:  # 복구 성공
                            task.retries += 1
                            task.status = AgentStatus.RUNNING
                            task.error = None
                            print(f"    복구 성공! 재시도 #{task.retries}")
                            continue
                    except Exception as recovery_error:
                        print(f"    복구 실패: {recovery_error}")

                self.memory.record_task(task)
                return False

        return False


class NoterangMultiAgent:
    """노트랑 멀티 에이전트 시스템"""

    def __init__(self):
        self.manager = AgentManager()
        self.nlm_exe = Path.home() / "AppData/Roaming/Python/Python313/Scripts/nlm.exe"

    def run_nlm(self, args, timeout=120):
        """nlm CLI 실행"""
        import subprocess
        import os

        cmd = [str(self.nlm_exe)] + args
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env)
            stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
            stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
            return result.returncode == 0, stdout, stderr
        except Exception as e:
            return False, '', str(e)

    async def create_slides_with_monitoring(
        self,
        notebook_id: str,
        language: str = "ko",
        focus: str = None
    ) -> Optional[str]:
        """슬라이드 생성 (모니터링 포함)"""

        # 작업 생성
        task = AgentTask(
            task_id=f"slides_{int(time.time())}",
            task_type="slides_create",
            params={"notebook_id": notebook_id, "language": language, "focus": focus}
        )

        # 슬라이드 생성 시작
        args = ["slides", "create", notebook_id, "--language", language, "--confirm"]
        if focus:
            args.extend(["--focus", focus])

        print(f"\n[슬라이드 생성] 노트북: {notebook_id[:8]}...")
        success, stdout, stderr = self.run_nlm(args, timeout=60)

        if not success:
            print(f"  ❌ 생성 시작 실패: {stderr[:100]}")
            return None

        # Artifact ID 추출
        artifact_id = None
        for line in stdout.split('\n'):
            if 'Artifact ID:' in line:
                artifact_id = line.split('Artifact ID:')[1].strip()
                break

        print(f"  Artifact ID: {artifact_id}")

        # 완료 체크 함수
        def check_completion():
            success, stdout, _ = self.run_nlm(["studio", "status", notebook_id])
            return success and '"status": "completed"' in stdout

        # 타임아웃 시 콜백 (헬퍼 에이전트가 수행)
        async def on_timeout(task, helper):
            print(f"    [헬퍼] 상태 재확인 중...")
            success, stdout, _ = self.run_nlm(["studio", "status", notebook_id])
            print(f"    [헬퍼] 현재 상태: {stdout[:100]}...")

            # 진행 중이면 계속 대기
            if '"status": "in_progress"' in stdout:
                print(f"    [헬퍼] 아직 진행 중 - 대기 계속")
                return

            # 실패한 경우 재시도
            if '"status": "failed"' in stdout:
                print(f"    [헬퍼] 실패 감지 - 재생성 시도")
                self.run_nlm(args, timeout=60)

        # 에러 시 콜백 (복구 에이전트가 수행)
        async def on_error(task, recovery, error):
            print(f"    [복구] 에러 분석: {type(error).__name__}")

            # 인증 에러면 재인증
            if "auth" in str(error).lower() or "expired" in str(error).lower():
                print(f"    [복구] 인증 재시도...")
                from sync_auth import sync_auth
                sync_auth()
                return True

            # 네트워크 에러면 재시도
            if "timeout" in str(error).lower() or "connection" in str(error).lower():
                print(f"    [복구] 네트워크 재시도 대기...")
                await asyncio.sleep(5)
                return True

            return False

        # 모니터링 시작
        completed = await self.manager.monitor_task(
            task=task,
            check_fn=check_completion,
            check_interval=10,
            on_timeout=on_timeout,
            on_error=on_error
        )

        if completed:
            return artifact_id
        return None

    async def run_research_with_monitoring(
        self,
        notebook_id: str,
        query: str,
        mode: str = "fast"
    ) -> tuple:
        """연구 실행 (모니터링 포함)"""

        task = AgentTask(
            task_id=f"research_{int(time.time())}",
            task_type="research",
            params={"notebook_id": notebook_id, "query": query, "mode": mode}
        )

        print(f"\n[연구] 쿼리: {query}")

        # 연구 시작
        success, stdout, stderr = self.run_nlm([
            "research", "start", query,
            "--notebook-id", notebook_id,
            "--mode", mode
        ])

        if not success:
            print(f"  ❌ 연구 시작 실패")
            return False, 0

        # Task ID 추출
        task_id = None
        for line in stdout.split('\n'):
            if 'Task ID:' in line:
                task_id = line.split('Task ID:')[1].strip()
                break

        # 완료 체크 함수
        def check_completion():
            success, stdout, _ = self.run_nlm(["research", "status", notebook_id])
            return success and "completed" in stdout.lower()

        # 모니터링
        completed = await self.manager.monitor_task(
            task=task,
            check_fn=check_completion,
            check_interval=5
        )

        if completed and task_id:
            # 소스 가져오기
            success, stdout, _ = self.run_nlm(["research", "import", notebook_id, task_id])
            imported = 0
            if "Imported" in stdout:
                try:
                    imported = int(stdout.split("Imported")[1].split("source")[0].strip())
                except:
                    pass
            return True, imported

        return False, 0

    def get_memory_stats(self) -> Dict:
        """메모리 통계 반환"""
        return {
            "performance": self.manager.memory.data["performance_stats"],
            "error_patterns": list(self.manager.memory.data["error_patterns"].keys()),
            "timeout_thresholds": self.manager.memory.data["timeout_thresholds"],
            "agents_created": len(self.manager.agents)
        }


# 전역 인스턴스
_noterang_agent = None

def get_noterang_agent() -> NoterangMultiAgent:
    """노트랑 멀티 에이전트 인스턴스 반환"""
    global _noterang_agent
    if _noterang_agent is None:
        _noterang_agent = NoterangMultiAgent()
    return _noterang_agent


async def main():
    """테스트 실행"""
    agent = get_noterang_agent()

    print("=" * 60)
    print("노트랑 멀티 에이전트 시스템 테스트")
    print("=" * 60)

    # 메모리 통계 출력
    stats = agent.get_memory_stats()
    print(f"\n현재 메모리 상태:")
    print(f"  총 작업: {stats['performance']['total_tasks']}")
    print(f"  성공: {stats['performance']['successful_tasks']}")
    print(f"  실패: {stats['performance']['failed_tasks']}")
    print(f"  타임아웃 설정: {stats['timeout_thresholds']}")

    print("\n테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
