#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF to Editable PPTX Webapp
- PaddleOCR 기반 텍스트 추출
- 편집 가능한 PPTX 생성
"""

from .config import WebappConfig, get_webapp_config
from .ocr_engine import OCREngine, TextBlock
from .pdf_processor import PDFProcessor
from .pptx_builder import EditablePPTXBuilder

__all__ = [
    'WebappConfig',
    'get_webapp_config',
    'OCREngine',
    'TextBlock',
    'PDFProcessor',
    'EditablePPTXBuilder',
]

__version__ = '1.0.0'
