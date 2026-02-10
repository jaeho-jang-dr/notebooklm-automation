#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 처리기 - PDF를 이미지로 변환
"""
import sys
from pathlib import Path
from typing import List, Optional, Tuple, BinaryIO, Union

from PIL import Image

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class PDFProcessor:
    """PDF 파일 처리기"""

    def __init__(self, dpi: int = 150):
        """
        PDF 처리기 초기화

        Args:
            dpi: 렌더링 해상도
        """
        self.dpi = dpi
        self._doc = None

    def open(self, pdf_source: Union[Path, str, BinaryIO, bytes]) -> int:
        """
        PDF 파일 열기

        Args:
            pdf_source: PDF 파일 경로, 파일 객체, 또는 바이트 데이터

        Returns:
            총 페이지 수
        """
        import fitz

        if isinstance(pdf_source, (str, Path)):
            self._doc = fitz.open(pdf_source)
        elif isinstance(pdf_source, bytes):
            self._doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            # 파일 객체 (file-like object)
            data = pdf_source.read()
            self._doc = fitz.open(stream=data, filetype="pdf")

        return len(self._doc)

    def close(self):
        """PDF 닫기"""
        if self._doc:
            self._doc.close()
            self._doc = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def page_count(self) -> int:
        """총 페이지 수"""
        return len(self._doc) if self._doc else 0

    def get_page_size(self, page_num: int = 0) -> Tuple[float, float]:
        """
        페이지 크기 반환 (포인트 단위)

        Args:
            page_num: 페이지 번호 (0부터 시작)

        Returns:
            (너비, 높이) in points
        """
        if not self._doc:
            raise ValueError("PDF가 열려있지 않습니다")

        page = self._doc[page_num]
        return page.rect.width, page.rect.height

    def render_page(self, page_num: int, dpi: Optional[int] = None) -> Image.Image:
        """
        특정 페이지를 이미지로 렌더링

        Args:
            page_num: 페이지 번호 (0부터 시작)
            dpi: 렌더링 해상도 (None이면 기본값 사용)

        Returns:
            PIL 이미지
        """
        import fitz

        if not self._doc:
            raise ValueError("PDF가 열려있지 않습니다")

        if page_num < 0 or page_num >= len(self._doc):
            raise ValueError(f"잘못된 페이지 번호: {page_num}")

        render_dpi = dpi or self.dpi
        zoom = render_dpi / 72  # 72 DPI가 기본

        page = self._doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # RGB로 변환
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        return img

    def render_all_pages(
        self,
        dpi: Optional[int] = None,
        page_range: Optional[Tuple[int, int]] = None,
        progress_callback=None
    ) -> List[Image.Image]:
        """
        모든 페이지(또는 지정된 범위)를 이미지로 렌더링

        Args:
            dpi: 렌더링 해상도
            page_range: (시작, 끝) 페이지 범위 (None이면 전체)
            progress_callback: 진행률 콜백 (page_num, total)

        Returns:
            PIL 이미지 리스트
        """
        if not self._doc:
            raise ValueError("PDF가 열려있지 않습니다")

        start = 0
        end = len(self._doc)

        if page_range:
            start = max(0, page_range[0])
            end = min(len(self._doc), page_range[1])

        images = []
        total = end - start

        for i, page_num in enumerate(range(start, end)):
            if progress_callback:
                progress_callback(i + 1, total)

            img = self.render_page(page_num, dpi)
            images.append(img)

        return images

    def get_thumbnail(
        self,
        page_num: int,
        max_size: Tuple[int, int] = (200, 200)
    ) -> Image.Image:
        """
        썸네일 이미지 생성

        Args:
            page_num: 페이지 번호
            max_size: 최대 크기 (너비, 높이)

        Returns:
            썸네일 이미지
        """
        # 낮은 DPI로 렌더링
        img = self.render_page(page_num, dpi=72)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img

    def get_all_thumbnails(
        self,
        max_size: Tuple[int, int] = (200, 200),
        progress_callback=None
    ) -> List[Image.Image]:
        """
        모든 페이지의 썸네일 생성

        Args:
            max_size: 최대 크기
            progress_callback: 진행률 콜백

        Returns:
            썸네일 리스트
        """
        thumbnails = []

        for i in range(self.page_count):
            if progress_callback:
                progress_callback(i + 1, self.page_count)

            thumb = self.get_thumbnail(i, max_size)
            thumbnails.append(thumb)

        return thumbnails


def pdf_to_images(
    pdf_path: Union[Path, str, bytes, BinaryIO],
    dpi: int = 150,
    page_range: Optional[Tuple[int, int]] = None,
    progress_callback=None
) -> List[Image.Image]:
    """
    PDF를 이미지 리스트로 변환 (편의 함수)

    Args:
        pdf_path: PDF 파일 경로 또는 데이터
        dpi: 렌더링 해상도
        page_range: 페이지 범위
        progress_callback: 진행률 콜백

    Returns:
        PIL 이미지 리스트
    """
    with PDFProcessor(dpi=dpi) as processor:
        processor.open(pdf_path)
        return processor.render_all_pages(
            dpi=dpi,
            page_range=page_range,
            progress_callback=progress_callback
        )
