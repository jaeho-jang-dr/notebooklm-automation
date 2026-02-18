#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 설정 관리
- 환경 설정 로드/저장
- API 키 관리
- 경로 설정
"""
import logging
import os
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DOWNLOAD_DIR = Path("G:/내 드라이브/notebooklm")
DEFAULT_AUTH_DIR = Path.home() / ".notebooklm-mcp-cli"
DEFAULT_LANGUAGE = "ko"

# Timeout constants (seconds)
DEFAULT_TIMEOUT_SLIDES = 600    # 10 minutes – slide generation can be slow
DEFAULT_TIMEOUT_RESEARCH = 120  # 2 minutes
DEFAULT_TIMEOUT_DOWNLOAD = 60   # 1 minute
DEFAULT_TIMEOUT_LOGIN = 120     # 2 minutes

# Browser viewport defaults
DEFAULT_VIEWPORT_WIDTH = 1920
DEFAULT_VIEWPORT_HEIGHT = 1080

# Python version search paths for nlm executable discovery
_NLM_PYTHON_VERSIONS: List[str] = ["Python312", "Python311", "Python313"]


def _find_nlm_exe() -> Path:
    """Locate the nlm executable by searching PATH and common install locations.

    Returns:
        Path to the nlm executable, or ``Path("nlm")`` as a fallback.
    """
    import shutil

    nlm_path = shutil.which("nlm")
    if nlm_path:
        return Path(nlm_path)

    home = Path.home()
    search_paths: List[Path] = []
    for ver in _NLM_PYTHON_VERSIONS:
        search_paths.append(home / f"AppData/Local/Programs/Python/{ver}/Scripts/nlm.exe")
        search_paths.append(home / f"AppData/Roaming/Python/{ver}/Scripts/nlm.exe")

    for path in search_paths:
        if path.exists():
            return path

    logger.debug("nlm executable not found in PATH or standard locations; using bare 'nlm'")
    return Path("nlm")


def _find_nlm_auth_exe() -> Path:
    """Locate the notebooklm-mcp-auth executable.

    Returns:
        Path to the auth executable, or ``Path("notebooklm-mcp-auth")`` as a fallback.
    """
    import shutil

    auth_path = shutil.which("notebooklm-mcp-auth")
    if auth_path:
        return Path(auth_path)

    nlm_exe = _find_nlm_exe()
    if nlm_exe.parent.exists():
        auth_exe = nlm_exe.parent / "notebooklm-mcp-auth.exe"
        if auth_exe.exists():
            return auth_exe

    logger.debug(
        "notebooklm-mcp-auth executable not found; using bare 'notebooklm-mcp-auth'"
    )
    return Path("notebooklm-mcp-auth")


@dataclass
class NoterangConfig:
    """Configuration container for the Noterang automation agent.

    Attributes:
        download_dir: Directory where downloaded PDFs are saved.
        auth_dir: Directory used to store NLM auth state and browser profiles.
        nlm_exe: Path to the ``nlm`` CLI executable.
        nlm_auth_exe: Path to the ``notebooklm-mcp-auth`` CLI executable.
        apify_api_key: Apify API key for web research queries.
        notebooklm_app_password: App password in ``"xxxx xxxx xxxx xxxx"`` format.
        timeout_slides: Maximum seconds to wait for slide generation.
        timeout_research: Maximum seconds to wait for a research task.
        timeout_download: Maximum seconds to wait for a file download.
        timeout_login: Maximum seconds to wait for browser login.
        browser_headless: Whether to run the browser in headless mode.
        browser_viewport_width: Browser viewport width in pixels.
        browser_viewport_height: Browser viewport height in pixels.
        default_language: BCP-47 language code for generated slides (default ``"ko"``).
        debug: Enable verbose debug output.
        save_screenshots: Persist browser screenshots for diagnostics.
        worker_id: Identifier for this worker when running in parallel mode.
    """

    download_dir: Path = field(default_factory=lambda: DEFAULT_DOWNLOAD_DIR)
    auth_dir: Path = field(default_factory=lambda: DEFAULT_AUTH_DIR)

    nlm_exe: Path = field(default_factory=lambda: _find_nlm_exe())
    nlm_auth_exe: Path = field(default_factory=lambda: _find_nlm_auth_exe())

    apify_api_key: str = ""
    notebooklm_app_password: str = ""

    timeout_slides: int = DEFAULT_TIMEOUT_SLIDES
    timeout_research: int = DEFAULT_TIMEOUT_RESEARCH
    timeout_download: int = DEFAULT_TIMEOUT_DOWNLOAD
    timeout_login: int = DEFAULT_TIMEOUT_LOGIN

    browser_headless: bool = False
    browser_viewport_width: int = DEFAULT_VIEWPORT_WIDTH
    browser_viewport_height: int = DEFAULT_VIEWPORT_HEIGHT

    default_language: str = DEFAULT_LANGUAGE

    debug: bool = False
    save_screenshots: bool = True

    worker_id: Optional[int] = None

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def browser_profile(self) -> Path:
        """Return the browser profile directory, worker-scoped when applicable."""
        base = self.auth_dir / "browser_profile"
        if self.worker_id is not None:
            return base.parent / f"browser_profile_{self.worker_id}"
        return base

    @property
    def profile_dir(self) -> Path:
        """Return the default NLM profile directory."""
        return self.auth_dir / "profiles" / "default"

    @property
    def root_auth_file(self) -> Path:
        """Return the path to the root auth JSON file."""
        return self.auth_dir / "auth.json"

    @property
    def memory_file(self) -> Path:
        """Return the path to the agent memory JSON file."""
        return self.download_dir / "agent_memory.json"

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    def ensure_dirs(self) -> None:
        """Create all required directories if they do not already exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.browser_profile.mkdir(parents=True, exist_ok=True)
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialise configuration to a JSON-compatible dictionary.

        Returns:
            Dictionary with all config fields; ``Path`` values converted to strings.
        """
        data: Dict[str, Any] = {}
        for key, value in asdict(self).items():
            data[key] = str(value) if isinstance(value, Path) else value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoterangConfig':
        """Deserialise configuration from a dictionary.

        Args:
            data: Dictionary produced by :meth:`to_dict` or loaded from JSON.

        Returns:
            New :class:`NoterangConfig` instance populated from *data*.
        """
        data = {k: v for k, v in data.items() if v is not None}

        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        data = {k: v for k, v in data.items() if k in valid_fields}

        path_fields = ['download_dir', 'auth_dir', 'nlm_exe', 'nlm_auth_exe']
        for path_field in path_fields:
            if path_field in data and isinstance(data[path_field], str):
                data[path_field] = Path(data[path_field])

        return cls(**data)

    def save(self, path: Optional[Path] = None) -> None:
        """Persist configuration to a JSON file.

        Args:
            path: Target file path. Defaults to ``noterang_config.json`` in the
                project root.
        """
        save_path = path or (Path(__file__).parent.parent / "noterang_config.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug("Configuration saved to %s", save_path)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'NoterangConfig':
        """Load configuration from a JSON file or fall back to environment variables.

        Args:
            path: Source file path. Defaults to ``noterang_config.json`` in the
                project root.

        Returns:
            :class:`NoterangConfig` populated from the file or environment.
        """
        load_path = path or (Path(__file__).parent.parent / "noterang_config.json")

        if load_path.exists():
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug("Configuration loaded from %s", load_path)
            return cls.from_dict(data)

        logger.debug(
            "Config file %s not found; loading from environment variables", load_path
        )
        config = cls()
        config.apify_api_key = os.environ.get('APIFY_API_KEY', '')
        config.notebooklm_app_password = os.environ.get('NOTEBOOKLM_APP_PASSWORD', '')
        return config


# ---------------------------------------------------------------------------
# Global config helpers
# ---------------------------------------------------------------------------

_config: Optional[NoterangConfig] = None


def get_config() -> NoterangConfig:
    """Return the process-wide :class:`NoterangConfig` singleton.

    The instance is created on first access by calling :meth:`NoterangConfig.load`
    and :meth:`NoterangConfig.ensure_dirs`.

    Returns:
        The global :class:`NoterangConfig` instance.
    """
    global _config
    if _config is None:
        _config = NoterangConfig.load()
        _config.ensure_dirs()
    return _config


def set_config(config: NoterangConfig) -> None:
    """Replace the process-wide configuration singleton.

    Args:
        config: The new :class:`NoterangConfig` instance to use globally.
    """
    global _config
    _config = config
    config.ensure_dirs()


def init_config(
    apify_api_key: str = "",
    notebooklm_app_password: str = "",
    download_dir: Optional[str] = None,
    **kwargs: Any,
) -> NoterangConfig:
    """Initialise (or update) the global configuration and persist it to disk.

    Args:
        apify_api_key: Apify API key to set. Ignored when empty.
        notebooklm_app_password: NotebookLM app password to set. Ignored when empty.
        download_dir: Override the download directory path. Ignored when ``None``.
        **kwargs: Additional :class:`NoterangConfig` field overrides.

    Returns:
        The updated :class:`NoterangConfig` instance.
    """
    config = NoterangConfig.load()

    if apify_api_key:
        config.apify_api_key = apify_api_key
    if notebooklm_app_password:
        config.notebooklm_app_password = notebooklm_app_password
    if download_dir:
        config.download_dir = Path(download_dir)

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    config.ensure_dirs()
    config.save()
    set_config(config)

    return config
