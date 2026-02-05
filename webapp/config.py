#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹앱 설정 관리
"""
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class WebappConfig:
    """웹앱 설정"""

    # 슬라이드 크기 (인치)
    slide_width_inches: float = 13.333
    slide_height_inches: float = 7.5

    # 기본 DPI 옵션
    dpi_options: List[int] = field(default_factory=lambda: [72, 150, 300])
    default_dpi: int = 150

    # 폰트 설정
    available_fonts: List[str] = field(default_factory=lambda: [
        "맑은 고딕",
        "나눔고딕",
        "Pretendard",
        "Arial",
        "Calibri",
    ])
    default_font: str = "맑은 고딕"

    # 폰트 크기 범위
    min_font_size: int = 8
    max_font_size: int = 72
    default_font_size: int = 12

    # 배경 설정
    include_background: bool = True
    default_background_opacity: int = 100  # 0-100%

    # OCR 설정
    ocr_lang: str = "korean"
    ocr_use_gpu: bool = False
    ocr_confidence_threshold: float = 0.5

    # 임시 파일 경로
    temp_dir: Path = field(default_factory=lambda: Path.home() / ".webapp_temp")

    # 출력 경로
    output_dir: Path = field(default_factory=lambda: Path("G:/내 드라이브/notebooklm"))

    def ensure_dirs(self):
        """필요한 디렉토리 생성"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def slide_size_pixels(self) -> Tuple[int, int]:
        """슬라이드 크기를 픽셀로 반환 (150 DPI 기준)"""
        return (
            int(self.slide_width_inches * 150),
            int(self.slide_height_inches * 150)
        )


# 전역 설정 인스턴스
_webapp_config: Optional[WebappConfig] = None


def get_webapp_config() -> WebappConfig:
    """전역 웹앱 설정 반환"""
    global _webapp_config
    if _webapp_config is None:
        _webapp_config = WebappConfig()
        _webapp_config.ensure_dirs()
    return _webapp_config


def set_webapp_config(config: WebappConfig):
    """전역 웹앱 설정 설정"""
    global _webapp_config
    _webapp_config = config
    config.ensure_dirs()
