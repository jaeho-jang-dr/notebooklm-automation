#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 아티팩트 모듈
- 슬라이드 생성
- 인포그래픽 생성
- 스튜디오 상태 확인
"""
import asyncio
import json
import sys
import time
from typing import Optional, Dict, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .config import get_config
from .auth import run_nlm


def create_slides(
    notebook_id: str,
    language: str = None,
    focus: str = None,
    confirm: bool = True
) -> Optional[str]:
    """
    슬라이드 생성 시작

    Args:
        notebook_id: 노트북 ID
        language: 언어 (기본: "ko" 한글)
        focus: 집중할 주제
        confirm: 자동 확인

    Returns:
        Artifact ID 또는 None
    """
    config = get_config()
    lang = language or config.default_language  # 기본: 한글!

    args = ["slides", "create", notebook_id, "--language", lang]
    if focus:
        args.extend(["--focus", focus])
    if confirm:
        args.append("--confirm")

    print(f"  슬라이드 생성 시작 (언어: {lang})...")
    success, stdout, stderr = run_nlm(args, timeout=60)

    if not success:
        print(f"  ❌ 생성 시작 실패: {stderr[:100]}")
        return None

    # Artifact ID 추출
    for line in stdout.split('\n'):
        if 'Artifact ID:' in line:
            artifact_id = line.split('Artifact ID:')[1].strip()
            print(f"  Artifact ID: {artifact_id}")
            return artifact_id

    return None


def create_infographic(
    notebook_id: str,
    language: str = None,
    style: str = "modern",
    focus: str = None
) -> Optional[str]:
    """
    인포그래픽 생성 시작

    Args:
        notebook_id: 노트북 ID
        language: 언어
        style: 스타일 (modern, minimal, detailed)
        focus: 집중할 주제

    Returns:
        Artifact ID 또는 None
    """
    config = get_config()
    lang = language or config.default_language

    args = ["infographic", "create", notebook_id, "--language", lang, "--style", style]
    if focus:
        args.extend(["--focus", focus])

    print(f"  인포그래픽 생성 시작 (스타일: {style})...")
    success, stdout, stderr = run_nlm(args, timeout=60)

    if not success:
        print(f"  ❌ 생성 시작 실패: {stderr[:100]}")
        return None

    # Artifact ID 추출
    for line in stdout.split('\n'):
        if 'Artifact ID:' in line or 'id' in line.lower():
            parts = line.split(':')
            if len(parts) > 1:
                return parts[1].strip().strip('"')

    return None


def check_studio_status(notebook_id: str) -> Tuple[str, Dict]:
    """
    스튜디오 상태 확인

    Returns:
        (status, full_response)
        status: "completed", "in_progress", "failed", "unknown"
    """
    success, stdout, stderr = run_nlm(["studio", "status", notebook_id])

    if not success:
        return "unknown", {"error": stderr}

    try:
        data = json.loads(stdout)
        status = data.get("status", "unknown")
        return status, data
    except json.JSONDecodeError:
        # 텍스트 파싱
        if '"status": "completed"' in stdout or "'completed'" in stdout.lower():
            return "completed", {"raw": stdout}
        elif '"status": "in_progress"' in stdout or "'in_progress'" in stdout.lower():
            return "in_progress", {"raw": stdout}
        elif '"status": "failed"' in stdout or "'failed'" in stdout.lower():
            return "failed", {"raw": stdout}
        return "unknown", {"raw": stdout}


def is_generation_complete(notebook_id: str) -> bool:
    """생성 완료 여부 확인"""
    status, _ = check_studio_status(notebook_id)
    return status == "completed"


async def wait_for_completion(
    notebook_id: str,
    timeout: int = None,
    check_interval: int = 10,
    on_progress: callable = None
) -> bool:
    """
    생성 완료 대기

    Args:
        notebook_id: 노트북 ID
        timeout: 최대 대기 시간 (초)
        check_interval: 체크 간격 (초)
        on_progress: 진행 콜백 (elapsed_seconds, status)

    Returns:
        완료 여부
    """
    config = get_config()
    max_wait = timeout or config.timeout_slides

    start_time = time.time()
    check_count = 0

    while True:
        elapsed = time.time() - start_time
        check_count += 1

        if elapsed > max_wait:
            print(f"\n  ⏰ 타임아웃 ({int(elapsed)}초)")
            return False

        status, data = check_studio_status(notebook_id)

        if on_progress:
            on_progress(int(elapsed), status)

        if status == "completed":
            print(f"\n  ✓ 생성 완료 ({int(elapsed)}초)")
            return True
        elif status == "failed":
            print(f"\n  ❌ 생성 실패")
            return False

        if check_count % 3 == 0:
            print(f"\r  체크 #{check_count}: {int(elapsed)}초 경과...", end="", flush=True)

        await asyncio.sleep(check_interval)


async def create_slides_and_wait(
    notebook_id: str,
    language: str = None,
    focus: str = None,
    timeout: int = None
) -> Optional[str]:
    """
    슬라이드 생성 및 완료 대기

    Returns:
        Artifact ID 또는 None
    """
    artifact_id = create_slides(notebook_id, language, focus)

    if not artifact_id:
        return None

    completed = await wait_for_completion(notebook_id, timeout)

    if completed:
        return artifact_id
    return None


async def create_infographic_and_wait(
    notebook_id: str,
    language: str = None,
    style: str = "modern",
    focus: str = None,
    timeout: int = None
) -> Optional[str]:
    """
    인포그래픽 생성 및 완료 대기

    Returns:
        Artifact ID 또는 None
    """
    artifact_id = create_infographic(notebook_id, language, style, focus)

    if not artifact_id:
        return None

    completed = await wait_for_completion(notebook_id, timeout)

    if completed:
        return artifact_id
    return None


class ArtifactManager:
    """아티팩트 관리자"""

    def __init__(self, notebook_id: str = None):
        self.notebook_id = notebook_id
        self.artifacts: Dict[str, Dict] = {}

    def set_notebook(self, notebook_id: str):
        """노트북 설정"""
        self.notebook_id = notebook_id

    def create_slides(self, language: str = None, focus: str = None) -> Optional[str]:
        """슬라이드 생성"""
        if not self.notebook_id:
            print("  ❌ 노트북 없음")
            return None

        artifact_id = create_slides(self.notebook_id, language, focus)
        if artifact_id:
            self.artifacts[artifact_id] = {
                "type": "slides",
                "language": language,
                "focus": focus,
                "created_at": time.time()
            }
        return artifact_id

    def create_infographic(self, language: str = None, style: str = "modern", focus: str = None) -> Optional[str]:
        """인포그래픽 생성"""
        if not self.notebook_id:
            print("  ❌ 노트북 없음")
            return None

        artifact_id = create_infographic(self.notebook_id, language, style, focus)
        if artifact_id:
            self.artifacts[artifact_id] = {
                "type": "infographic",
                "style": style,
                "language": language,
                "focus": focus,
                "created_at": time.time()
            }
        return artifact_id

    def check_status(self) -> Tuple[str, Dict]:
        """상태 확인"""
        if not self.notebook_id:
            return "unknown", {"error": "노트북 없음"}
        return check_studio_status(self.notebook_id)

    def is_complete(self) -> bool:
        """완료 여부"""
        if not self.notebook_id:
            return False
        return is_generation_complete(self.notebook_id)

    async def wait_complete(self, timeout: int = None) -> bool:
        """완료 대기"""
        if not self.notebook_id:
            return False
        return await wait_for_completion(self.notebook_id, timeout)

    async def create_slides_wait(self, language: str = None, focus: str = None, timeout: int = None) -> Optional[str]:
        """슬라이드 생성 및 대기"""
        if not self.notebook_id:
            return None
        return await create_slides_and_wait(self.notebook_id, language, focus, timeout)

    async def create_infographic_wait(self, language: str = None, style: str = "modern", focus: str = None, timeout: int = None) -> Optional[str]:
        """인포그래픽 생성 및 대기"""
        if not self.notebook_id:
            return None
        return await create_infographic_and_wait(self.notebook_id, language, style, focus, timeout)
