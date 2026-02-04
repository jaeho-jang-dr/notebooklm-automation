"""
노트랑 (Noterang) - NotebookLM 완전 자동화 에이전트

Usage:
    from noterang import Noterang, init_config

    # 설정 초기화 (최초 1회)
    init_config(
        apify_api_key="your_api_key",
        notebooklm_app_password="xxxx xxxx xxxx xxxx"
    )

    # 자동화 실행
    noterang = Noterang()
    result = await noterang.run(
        title="주제 제목",
        research_queries=["쿼리1", "쿼리2"],
        focus="핵심 주제"
    )

    # 또는 간편 함수
    from noterang import run_automation
    result = await run_automation("제목", ["쿼리1", "쿼리2"])
"""

__version__ = "2.0.0"

# Config
from .config import (
    NoterangConfig,
    get_config,
    set_config,
    init_config,
)

# Core
from .core import (
    Noterang,
    WorkflowResult,
    run_automation,
    run_automation_sync,
    run_batch,
)

# Auth
from .auth import (
    auto_login,
    ensure_auth,
    check_auth,
    sync_auth,
    run_auto_login,
    run_ensure_logged_in,
)

# Notebook
from .notebook import (
    NotebookManager,
    get_notebook_manager,
    list_notebooks,
    find_notebook,
    create_notebook,
    delete_notebook,
    get_or_create_notebook,
    start_research,
    check_research_status,
    import_research,
)

# Artifacts
from .artifacts import (
    ArtifactManager,
    create_slides,
    create_infographic,
    check_studio_status,
    is_generation_complete,
    wait_for_completion,
    create_slides_and_wait,
    create_infographic_and_wait,
)

# Download
from .download import (
    download_via_browser,
    download_with_retries,
    download_sync,
    take_screenshot,
)

# Convert
from .convert import (
    Converter,
    pdf_to_pptx,
    pdf_to_pptx_with_notes,
    add_notes_to_pptx,
    batch_convert,
    apply_template,
    create_styled_pptx,
    extract_text_from_pdf,
)

# Browser (Playwright 기반 직접 제어)
from .browser import (
    NotebookLMBrowser,
    run_with_browser,
)

# Prompts (100개 슬라이드 디자인 프롬프트)
from .prompts import (
    SlidePrompts,
    get_slide_prompts,
    list_slide_styles,
    get_slide_prompt,
    search_slide_styles,
    print_style_catalog,
)

__all__ = [
    # Version
    "__version__",

    # Config
    "NoterangConfig",
    "get_config",
    "set_config",
    "init_config",

    # Core
    "Noterang",
    "WorkflowResult",
    "run_automation",
    "run_automation_sync",
    "run_batch",

    # Auth
    "auto_login",
    "ensure_auth",
    "check_auth",
    "sync_auth",
    "run_auto_login",
    "run_ensure_logged_in",

    # Notebook
    "NotebookManager",
    "get_notebook_manager",
    "list_notebooks",
    "find_notebook",
    "create_notebook",
    "delete_notebook",
    "get_or_create_notebook",
    "start_research",
    "check_research_status",
    "import_research",

    # Artifacts
    "ArtifactManager",
    "create_slides",
    "create_infographic",
    "check_studio_status",
    "is_generation_complete",
    "wait_for_completion",
    "create_slides_and_wait",
    "create_infographic_and_wait",

    # Download
    "download_via_browser",
    "download_with_retries",
    "download_sync",
    "take_screenshot",

    # Convert
    "Converter",
    "pdf_to_pptx",
    "pdf_to_pptx_with_notes",
    "add_notes_to_pptx",
    "batch_convert",
    "apply_template",
    "create_styled_pptx",
    "extract_text_from_pdf",

    # Browser
    "NotebookLMBrowser",
    "run_with_browser",

    # Prompts
    "SlidePrompts",
    "get_slide_prompts",
    "list_slide_styles",
    "get_slide_prompt",
    "search_slide_styles",
    "print_style_catalog",
]
