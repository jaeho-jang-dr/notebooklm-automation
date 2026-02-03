#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 노트북 관리 모듈
- 노트북 생성/삭제/목록
- 연구 자료 추가
- 소스 관리
"""
import json
import sys
from typing import Optional, List, Dict, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .auth import run_nlm


def list_notebooks() -> List[Dict]:
    """노트북 목록 조회"""
    success, stdout, stderr = run_nlm(["list", "notebooks"])

    if not success:
        print(f"  ❌ 노트북 목록 조회 실패: {stderr}")
        return []

    try:
        notebooks = json.loads(stdout)
        return notebooks if isinstance(notebooks, list) else []
    except json.JSONDecodeError:
        return []


def find_notebook(title: str) -> Optional[Dict]:
    """이름으로 노트북 찾기"""
    notebooks = list_notebooks()
    for nb in notebooks:
        if nb.get('title') == title:
            return nb
    return None


def create_notebook(title: str) -> Optional[str]:
    """
    새 노트북 생성

    Args:
        title: 노트북 제목

    Returns:
        노트북 ID 또는 None
    """
    success, stdout, stderr = run_nlm(["notebook", "create", title])

    if not success:
        print(f"  ❌ 노트북 생성 실패: {stderr}")
        return None

    try:
        data = json.loads(stdout)
        notebook_id = data.get('id')
        print(f"  ✓ 노트북 생성: {notebook_id[:8]}...")
        return notebook_id
    except (json.JSONDecodeError, TypeError):
        # stdout에서 ID 추출 시도
        if 'id' in stdout.lower():
            lines = stdout.split('\n')
            for line in lines:
                if 'id' in line.lower():
                    parts = line.split(':')
                    if len(parts) > 1:
                        return parts[1].strip().strip('"')
        return None


def delete_notebook(notebook_id: str) -> bool:
    """
    노트북 삭제

    Args:
        notebook_id: 노트북 ID

    Returns:
        성공 여부
    """
    success, stdout, stderr = run_nlm(["notebook", "delete", notebook_id, "--confirm"])

    if success:
        print(f"  ✓ 노트북 삭제됨: {notebook_id[:8]}...")
        return True
    else:
        print(f"  ❌ 삭제 실패: {stderr}")
        return False


def get_or_create_notebook(title: str) -> Optional[str]:
    """
    노트북 찾기 또는 생성

    Args:
        title: 노트북 제목

    Returns:
        노트북 ID 또는 None
    """
    # 먼저 기존 노트북 찾기
    existing = find_notebook(title)
    if existing:
        notebook_id = existing.get('id')
        print(f"  기존 노트북 발견: {notebook_id[:8]}...")
        return notebook_id

    # 없으면 새로 생성
    return create_notebook(title)


def start_research(notebook_id: str, query: str, mode: str = "fast") -> Optional[str]:
    """
    연구 시작

    Args:
        notebook_id: 노트북 ID
        query: 검색 쿼리
        mode: "fast" 또는 "deep"

    Returns:
        Task ID 또는 None
    """
    success, stdout, stderr = run_nlm([
        "research", "start", query,
        "--notebook-id", notebook_id,
        "--mode", mode
    ])

    if not success:
        print(f"  ❌ 연구 시작 실패: {stderr}")
        return None

    # Task ID 추출
    for line in stdout.split('\n'):
        if 'Task ID:' in line:
            return line.split('Task ID:')[1].strip()

    return None


def check_research_status(notebook_id: str) -> Tuple[bool, str]:
    """
    연구 상태 확인

    Returns:
        (완료 여부, 상태 문자열)
    """
    success, stdout, stderr = run_nlm(["research", "status", notebook_id])

    if not success:
        return False, stderr

    is_completed = "completed" in stdout.lower()
    return is_completed, stdout


def import_research(notebook_id: str, task_id: str) -> int:
    """
    연구 결과 가져오기

    Returns:
        가져온 소스 수
    """
    success, stdout, stderr = run_nlm(["research", "import", notebook_id, task_id])

    if not success:
        return 0

    # "Imported X sources" 추출
    if "Imported" in stdout:
        try:
            return int(stdout.split("Imported")[1].split("source")[0].strip())
        except (ValueError, IndexError):
            pass

    return 0


def get_notebook_sources(notebook_id: str) -> List[Dict]:
    """노트북 소스 목록"""
    success, stdout, stderr = run_nlm(["notebook", "sources", notebook_id])

    if not success:
        return []

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return []


def add_source_url(notebook_id: str, url: str) -> bool:
    """URL 소스 추가"""
    success, stdout, stderr = run_nlm(["source", "add", notebook_id, "--url", url])
    return success


def add_source_text(notebook_id: str, text: str, title: str = "텍스트 소스") -> bool:
    """텍스트 소스 추가"""
    success, stdout, stderr = run_nlm(["source", "add", notebook_id, "--text", text, "--title", title])
    return success


class NotebookManager:
    """노트북 관리자 클래스"""

    def __init__(self):
        self.current_notebook_id: Optional[str] = None
        self.current_title: Optional[str] = None

    def set_current(self, notebook_id: str, title: str = None):
        """현재 노트북 설정"""
        self.current_notebook_id = notebook_id
        self.current_title = title

    def list(self) -> List[Dict]:
        """노트북 목록"""
        return list_notebooks()

    def find(self, title: str) -> Optional[Dict]:
        """이름으로 노트북 찾기"""
        return find_notebook(title)

    def create(self, title: str) -> Optional[str]:
        """노트북 생성"""
        notebook_id = create_notebook(title)
        if notebook_id:
            self.set_current(notebook_id, title)
        return notebook_id

    def delete(self, notebook_id: str = None) -> bool:
        """노트북 삭제"""
        target_id = notebook_id or self.current_notebook_id
        if not target_id:
            print("  ❌ 삭제할 노트북 없음")
            return False

        if delete_notebook(target_id):
            if target_id == self.current_notebook_id:
                self.current_notebook_id = None
                self.current_title = None
            return True
        return False

    def get_or_create(self, title: str) -> Optional[str]:
        """노트북 찾기 또는 생성"""
        notebook_id = get_or_create_notebook(title)
        if notebook_id:
            self.set_current(notebook_id, title)
        return notebook_id

    def research(self, query: str, mode: str = "fast", notebook_id: str = None) -> Optional[str]:
        """연구 시작"""
        target_id = notebook_id or self.current_notebook_id
        if not target_id:
            print("  ❌ 노트북 없음")
            return None
        return start_research(target_id, query, mode)

    def check_research(self, notebook_id: str = None) -> Tuple[bool, str]:
        """연구 상태 확인"""
        target_id = notebook_id or self.current_notebook_id
        if not target_id:
            return False, "노트북 없음"
        return check_research_status(target_id)

    def import_research_results(self, task_id: str, notebook_id: str = None) -> int:
        """연구 결과 가져오기"""
        target_id = notebook_id or self.current_notebook_id
        if not target_id:
            return 0
        return import_research(target_id, task_id)

    def get_sources(self, notebook_id: str = None) -> List[Dict]:
        """소스 목록"""
        target_id = notebook_id or self.current_notebook_id
        if not target_id:
            return []
        return get_notebook_sources(target_id)


# 전역 매니저
_manager: Optional[NotebookManager] = None


def get_notebook_manager() -> NotebookManager:
    """전역 노트북 매니저 반환"""
    global _manager
    if _manager is None:
        _manager = NotebookManager()
    return _manager
