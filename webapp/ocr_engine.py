#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 엔진 - PaddleOCR 래퍼
"""
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path

import numpy as np
from PIL import Image

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class TextBlock:
    """OCR로 추출된 텍스트 블록"""
    text: str
    bbox: List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    confidence: float
    estimated_font_size: int = 12

    @property
    def x_min(self) -> float:
        return min(p[0] for p in self.bbox)

    @property
    def y_min(self) -> float:
        return min(p[1] for p in self.bbox)

    @property
    def x_max(self) -> float:
        return max(p[0] for p in self.bbox)

    @property
    def y_max(self) -> float:
        return max(p[1] for p in self.bbox)

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2


class OCREngine:
    """PaddleOCR 기반 OCR 엔진"""

    def __init__(
        self,
        lang: str = "korean",
        use_gpu: bool = False,
        confidence_threshold: float = 0.5
    ):
        """
        OCR 엔진 초기화

        Args:
            lang: 언어 설정 ("korean", "en", "ch" 등)
            use_gpu: GPU 사용 여부
            confidence_threshold: 신뢰도 임계값
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold
        self._ocr = None

    def _init_ocr(self):
        """PaddleOCR 초기화 (지연 로딩)"""
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False,
            )

    def extract_text_blocks(
        self,
        image: Image.Image,
        min_confidence: Optional[float] = None
    ) -> List[TextBlock]:
        """
        이미지에서 텍스트 블록 추출

        Args:
            image: PIL 이미지
            min_confidence: 최소 신뢰도 (None이면 기본값 사용)

        Returns:
            텍스트 블록 리스트
        """
        self._init_ocr()

        threshold = min_confidence or self.confidence_threshold

        # PIL 이미지를 numpy 배열로 변환
        img_array = np.array(image)

        # OCR 실행
        result = self._ocr.ocr(img_array, cls=True)

        text_blocks = []

        if result is None or len(result) == 0:
            return text_blocks

        # 결과 파싱
        for line in result[0]:
            if line is None:
                continue

            bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = line[1][0]
            confidence = line[1][1]

            if confidence < threshold:
                continue

            # bbox에서 폰트 크기 추정
            height = max(p[1] for p in bbox) - min(p[1] for p in bbox)
            estimated_font_size = self._estimate_font_size(height)

            block = TextBlock(
                text=text,
                bbox=bbox,
                confidence=confidence,
                estimated_font_size=estimated_font_size
            )
            text_blocks.append(block)

        return text_blocks

    def _estimate_font_size(self, pixel_height: float, dpi: int = 150) -> int:
        """
        픽셀 높이에서 폰트 크기 추정

        Args:
            pixel_height: 텍스트 높이 (픽셀)
            dpi: 이미지 DPI

        Returns:
            추정 폰트 크기 (pt)
        """
        # 포인트 = 픽셀 * 72 / DPI
        pt_size = pixel_height * 72 / dpi

        # 합리적인 범위로 제한
        pt_size = max(8, min(72, int(pt_size)))

        return pt_size

    def extract_text_only(self, image: Image.Image) -> str:
        """
        이미지에서 텍스트만 추출 (위치 정보 없이)

        Args:
            image: PIL 이미지

        Returns:
            추출된 텍스트
        """
        blocks = self.extract_text_blocks(image)

        # y좌표로 정렬 후 텍스트 합치기
        blocks.sort(key=lambda b: (b.y_min, b.x_min))

        lines = []
        current_line = []
        current_y = -1000

        for block in blocks:
            # 새로운 줄 감지 (y 좌표 차이가 폰트 크기보다 크면)
            if block.y_min - current_y > block.estimated_font_size * 0.5:
                if current_line:
                    # x좌표로 정렬하여 한 줄로 합치기
                    current_line.sort(key=lambda b: b.x_min)
                    lines.append(" ".join(b.text for b in current_line))
                current_line = [block]
                current_y = block.y_min
            else:
                current_line.append(block)

        # 마지막 줄 추가
        if current_line:
            current_line.sort(key=lambda b: b.x_min)
            lines.append(" ".join(b.text for b in current_line))

        return "\n".join(lines)

    def process_pdf_images(
        self,
        images: List[Image.Image],
        progress_callback=None
    ) -> List[List[TextBlock]]:
        """
        여러 이미지(PDF 페이지)에서 텍스트 추출

        Args:
            images: PIL 이미지 리스트
            progress_callback: 진행률 콜백 함수 (page_num, total)

        Returns:
            페이지별 텍스트 블록 리스트
        """
        all_blocks = []

        for i, image in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, len(images))

            blocks = self.extract_text_blocks(image)
            all_blocks.append(blocks)

        return all_blocks
