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
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

_DEFAULT_PROMPTS_FILE = Path(__file__).parent / "slide_prompts.json"
_DEFAULT_STYLE = "미니멀 젠"


class SlidePrompts:
    """Manager for 100 NotebookLM slide design prompt templates.

    Prompts are loaded lazily from a JSON file on the first access so that
    importing this module has no I/O cost.

    Attributes:
        prompts_file: Path to the JSON file containing style definitions.
    """

    def __init__(self, prompts_file: Optional[str] = None) -> None:
        """Initialise the manager.

        Args:
            prompts_file: Path to the prompts JSON file. Defaults to the
                ``slide_prompts.json`` bundled with the package.
        """
        self.prompts_file = Path(prompts_file) if prompts_file else _DEFAULT_PROMPTS_FILE

        self._data: Optional[Dict[str, Any]] = None
        self._styles: Optional[List[Dict[str, Any]]] = None
        self._by_name: Optional[Dict[str, Dict[str, Any]]] = None
        self._by_category: Optional[Dict[str, List[Dict[str, Any]]]] = None

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load and index prompt data from :attr:`prompts_file`.

        Raises:
            FileNotFoundError: When :attr:`prompts_file` does not exist.
        """
        if self._data is not None:
            return

        if not self.prompts_file.exists():
            raise FileNotFoundError(
                f"프롬프트 파일을 찾을 수 없습니다: {self.prompts_file}"
            )

        with open(self.prompts_file, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self._styles = self._data.get("styles", [])

        self._by_name = {style["name"]: style for style in self._styles}

        self._by_category: Dict[str, List[Dict[str, Any]]] = {}
        for style in self._styles:
            category = style.get("category", "기타")
            self._by_category.setdefault(category, []).append(style)

        logger.debug(
            "Loaded %d slide styles from %s", len(self._styles), self.prompts_file
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def source(self) -> str:
        """Source URL from which the prompts were curated."""
        self._load()
        return self._data.get("source", "")

    @property
    def default_style(self) -> str:
        """Name of the default design style."""
        self._load()
        return self._data.get("default_style", _DEFAULT_STYLE)

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def list_styles(self) -> List[Dict[str, str]]:
        """Return a summary list of all available styles.

        Returns:
            List of ``{"name": ..., "category": ...}`` dictionaries.
        """
        self._load()
        return [{"name": s["name"], "category": s["category"]} for s in self._styles]

    def list_categories(self) -> List[str]:
        """Return the list of unique category names.

        Returns:
            Category names in insertion order, e.g. ``["심플", "모던", "비즈니스", ...]``.
        """
        self._load()
        return list(self._by_category.keys())

    def get_by_category(self, category: str) -> List[Dict[str, str]]:
        """Return all styles belonging to the given category.

        Args:
            category: Category name (e.g. ``"심플"``, ``"모던"``).

        Returns:
            List of ``{"name": ..., "category": ...}`` dictionaries for the
            category, or an empty list when the category is unknown.
        """
        self._load()
        styles = self._by_category.get(category, [])
        return [{"name": s["name"], "category": s["category"]} for s in styles]

    def get_prompt(self, style_name: str) -> Optional[str]:
        """Return the prompt text for the named style.

        Falls back to a generated template when the style has no stored prompt.

        Args:
            style_name: Style name, e.g. ``"미니멀 젠"``.

        Returns:
            Prompt string, or ``None`` when the style does not exist.
        """
        self._load()
        style = self._by_name.get(style_name)
        if not style:
            logger.debug("Style '%s' not found in prompt library", style_name)
            return None

        if style.get("prompt"):
            return style["prompt"]

        return self._generate_prompt(style["name"], style["category"])

    def _generate_prompt(self, name: str, category: str) -> str:
        """Generate a fallback prompt from the style name and category.

        Args:
            name: Style name.
            category: Style category.

        Returns:
            A generic prompt string referencing the style and category.
        """
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
        """Return the full style record for the named style.

        Args:
            style_name: Style name to look up.

        Returns:
            Style dictionary (including ``"index"``, ``"name"``, ``"category"``,
            ``"prompt"``), or ``None`` when not found.
        """
        self._load()
        return self._by_name.get(style_name)

    def search(self, query: str) -> List[Dict[str, str]]:
        """Search for styles whose name contains the query string.

        Args:
            query: Case-insensitive search term.

        Returns:
            List of matching ``{"name": ..., "category": ...}`` dictionaries.
        """
        self._load()
        query_lower = query.lower()
        return [
            {"name": s["name"], "category": s["category"]}
            for s in self._styles
            if query_lower in s["name"].lower()
        ]

    def get_random(self) -> Dict[str, Any]:
        """Return a randomly selected style record.

        Returns:
            Full style dictionary for a randomly chosen style.
        """
        import random
        self._load()
        return random.choice(self._styles)

    def get_default_prompt(self) -> str:
        """Return the prompt for the default style.

        Returns:
            Prompt string for :attr:`default_style`.
        """
        return self.get_prompt(self.default_style)

    def format_prompt(self, style_name: str, **kwargs: Any) -> Optional[str]:
        """Return a (potentially formatted) prompt for the named style.

        Currently returns the raw prompt. Reserved for future template-variable
        support.

        Args:
            style_name: Target style name.
            **kwargs: Reserved for future template variable injection.

        Returns:
            Prompt string, or ``None`` when the style does not exist.
        """
        return self.get_prompt(style_name)

    # ------------------------------------------------------------------
    # Special methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the total number of available styles."""
        self._load()
        return len(self._styles)

    def __iter__(self):
        """Iterate over all style records."""
        self._load()
        return iter(self._styles)

    def __contains__(self, style_name: str) -> bool:
        """Return ``True`` when *style_name* exists in the library.

        Args:
            style_name: Style name to check.
        """
        self._load()
        return style_name in self._by_name


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

_prompts_instance: Optional[SlidePrompts] = None


def get_slide_prompts() -> SlidePrompts:
    """Return the process-wide :class:`SlidePrompts` singleton.

    Returns:
        Shared :class:`SlidePrompts` instance.
    """
    global _prompts_instance
    if _prompts_instance is None:
        _prompts_instance = SlidePrompts()
    return _prompts_instance


def list_slide_styles() -> List[Dict[str, str]]:
    """Return the full list of available slide styles.

    Returns:
        List of ``{"name": ..., "category": ...}`` dictionaries.
    """
    return get_slide_prompts().list_styles()


def get_slide_prompt(style_name: str) -> Optional[str]:
    """Return the prompt text for a named style.

    Args:
        style_name: Target style name.

    Returns:
        Prompt string, or ``None`` when not found.
    """
    return get_slide_prompts().get_prompt(style_name)


def search_slide_styles(query: str) -> List[Dict[str, str]]:
    """Search the style library by name.

    Args:
        query: Case-insensitive search term.

    Returns:
        Matching ``{"name": ..., "category": ...}`` dictionaries.
    """
    return get_slide_prompts().search(query)


def print_style_catalog() -> None:
    """Print the full style catalog grouped by category (CLI helper)."""
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
