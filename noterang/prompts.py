"""
노트랑 슬라이드 프롬프트 관리자

100개의 NotebookLM 슬라이드 디자인 프롬프트 템플릿을 제공합니다.

Usage:
    from noterang.prompts import SlidePrompts

    prompts = SlidePrompts()

    # 전체 스타일 목록
    styles = prompts.list_styles()

    # 카테고리별 스타일
    simple_styles = prompts.get_by_category("심플")

    # 특정 스타일 프롬프트 가져오기
    prompt = prompts.get_prompt("미니멀 젠")

    # 스타일 검색
    results = prompts.search("네온")
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any


class SlidePrompts:
    """100개의 슬라이드 디자인 프롬프트 관리자"""

    def __init__(self, prompts_file: Optional[str] = None):
        """
        Args:
            prompts_file: 프롬프트 JSON 파일 경로. 기본값은 패키지 내 slide_prompts.json
        """
        if prompts_file is None:
            prompts_file = Path(__file__).parent / "slide_prompts.json"

        self.prompts_file = Path(prompts_file)
        self._data: Optional[Dict[str, Any]] = None
        self._styles: Optional[List[Dict[str, Any]]] = None
        self._by_name: Optional[Dict[str, Dict[str, Any]]] = None
        self._by_category: Optional[Dict[str, List[Dict[str, Any]]]] = None

    def _load(self) -> None:
        """프롬프트 데이터 로드"""
        if self._data is not None:
            return

        if not self.prompts_file.exists():
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompts_file}")

        with open(self.prompts_file, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self._styles = self._data.get("styles", [])

        # 이름으로 인덱싱
        self._by_name = {style["name"]: style for style in self._styles}

        # 카테고리로 그룹화
        self._by_category = {}
        for style in self._styles:
            category = style.get("category", "기타")
            if category not in self._by_category:
                self._by_category[category] = []
            self._by_category[category].append(style)

    @property
    def source(self) -> str:
        """프롬프트 출처 URL"""
        self._load()
        return self._data.get("source", "")

    @property
    def default_style(self) -> str:
        """기본 스타일 이름"""
        self._load()
        return self._data.get("default_style", "미니멀 젠")

    def list_styles(self) -> List[Dict[str, str]]:
        """
        전체 스타일 목록 반환

        Returns:
            [{"name": "미니멀 젠", "category": "심플"}, ...]
        """
        self._load()
        return [{"name": s["name"], "category": s["category"]} for s in self._styles]

    def list_categories(self) -> List[str]:
        """
        카테고리 목록 반환

        Returns:
            ["심플", "모던", "비즈니스", ...]
        """
        self._load()
        return list(self._by_category.keys())

    def get_by_category(self, category: str) -> List[Dict[str, str]]:
        """
        특정 카테고리의 스타일 목록

        Args:
            category: 카테고리 이름 (심플, 모던, 비즈니스 등)

        Returns:
            해당 카테고리의 스타일 목록
        """
        self._load()
        styles = self._by_category.get(category, [])
        return [{"name": s["name"], "category": s["category"]} for s in styles]

    def get_prompt(self, style_name: str) -> Optional[str]:
        """
        특정 스타일의 프롬프트 텍스트 반환

        Args:
            style_name: 스타일 이름 (예: "미니멀 젠")

        Returns:
            프롬프트 텍스트 또는 None
        """
        self._load()
        style = self._by_name.get(style_name)
        if not style:
            return None

        # 프롬프트가 있으면 반환
        if "prompt" in style and style["prompt"]:
            return style["prompt"]

        # 프롬프트가 없으면 템플릿으로 생성
        return self._generate_prompt(style["name"], style["category"])

    def _generate_prompt(self, name: str, category: str) -> str:
        """스타일 이름과 카테고리로 기본 프롬프트 생성"""
        return f"""[NotebookLM 슬라이드 디자인 요청]

■ 역할: 전문 프레젠테이션 디자이너
■ 스타일: {name}
■ 카테고리: {category}
━━━━━━━━━━━━━━━━━━━━━━
이 스타일의 특성을 살려 고품질 슬라이드를 생성해주세요.

- '{name}' 스타일의 핵심 디자인 요소를 반영
- '{category}' 카테고리에 어울리는 톤 & 매너 유지
- 전문적이고 일관된 비주얼 구성
━━━━━━━━━━━━━━━━━━━━━━
위 가이드를 바탕으로 고품질 슬라이드를 생성해주세요."""

    def get_style(self, style_name: str) -> Optional[Dict[str, Any]]:
        """
        특정 스타일의 전체 정보 반환

        Args:
            style_name: 스타일 이름

        Returns:
            {"index": 1, "name": "미니멀 젠", "category": "심플", "prompt": "..."}
        """
        self._load()
        return self._by_name.get(style_name)

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        스타일 이름으로 검색

        Args:
            query: 검색어

        Returns:
            검색어가 이름에 포함된 스타일 목록
        """
        self._load()
        query_lower = query.lower()
        results = []
        for style in self._styles:
            if query_lower in style["name"].lower():
                results.append({"name": style["name"], "category": style["category"]})
        return results

    def get_random(self) -> Dict[str, Any]:
        """무작위 스타일 반환"""
        import random
        self._load()
        return random.choice(self._styles)

    def get_default_prompt(self) -> str:
        """기본 스타일의 프롬프트 반환"""
        return self.get_prompt(self.default_style)

    def format_prompt(self, style_name: str, **kwargs) -> Optional[str]:
        """
        프롬프트에 사용자 정의 값 삽입 (확장용)

        현재는 원본 프롬프트 반환, 추후 템플릿 변수 지원 가능
        """
        return self.get_prompt(style_name)

    def __len__(self) -> int:
        """스타일 총 개수"""
        self._load()
        return len(self._styles)

    def __iter__(self):
        """스타일 이터레이터"""
        self._load()
        return iter(self._styles)

    def __contains__(self, style_name: str) -> bool:
        """스타일 존재 여부 확인"""
        self._load()
        return style_name in self._by_name


# 싱글톤 인스턴스
_prompts_instance: Optional[SlidePrompts] = None


def get_slide_prompts() -> SlidePrompts:
    """SlidePrompts 싱글톤 인스턴스 반환"""
    global _prompts_instance
    if _prompts_instance is None:
        _prompts_instance = SlidePrompts()
    return _prompts_instance


def list_slide_styles() -> List[Dict[str, str]]:
    """전체 슬라이드 스타일 목록"""
    return get_slide_prompts().list_styles()


def get_slide_prompt(style_name: str) -> Optional[str]:
    """특정 스타일의 프롬프트 가져오기"""
    return get_slide_prompts().get_prompt(style_name)


def search_slide_styles(query: str) -> List[Dict[str, str]]:
    """스타일 검색"""
    return get_slide_prompts().search(query)


def print_style_catalog():
    """스타일 카탈로그 출력 (CLI용)"""
    prompts = get_slide_prompts()

    print(f"\n{'='*60}")
    print(f"  NotebookLM 슬라이드 디자인 스타일 ({len(prompts)}개)")
    print(f"{'='*60}\n")

    for category in prompts.list_categories():
        styles = prompts.get_by_category(category)
        print(f"[{category}] ({len(styles)}개)")
        for style in styles:
            print(f"  - {style['name']}")
        print()

    print(f"소스: {prompts.source}")
    print(f"기본 스타일: {prompts.default_style}")


if __name__ == "__main__":
    print_style_catalog()
