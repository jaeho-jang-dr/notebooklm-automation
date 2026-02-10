#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 슬라이드 분석기 (PyMuPDF + Vision OCR 폴백)
"""
import base64
import os
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class PDFAnalyzer:
    """PDF 슬라이드 분석기"""

    def __init__(self, pdf_path: Path, vision_api_key: str = ""):
        import fitz
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(self.pdf_path))
        self.page_count = len(self.doc)
        self.vision_api_key = vision_api_key or os.getenv('GOOGLE_CLOUD_VISION_API_KEY', '')

    def close(self):
        self.doc.close()

    def extract_all_text(self) -> List[str]:
        """페이지별 텍스트 추출 (PyMuPDF → Vision OCR 폴백)"""
        texts = []
        for page in self.doc:
            texts.append(page.get_text())

        total_chars = sum(len(t.strip()) for t in texts)
        if total_chars < 100:
            print(f"  PyMuPDF 텍스트 부족 ({total_chars}자) → Vision OCR 시도...")
            ocr_texts = self._ocr_with_vision()
            if ocr_texts:
                return ocr_texts

        return texts

    def _ocr_with_vision(self) -> Optional[List[str]]:
        """Google Cloud Vision API로 OCR 폴백"""
        import fitz
        import requests

        if not self.vision_api_key:
            print("  Vision API 키 없음. OCR 건너뜀.")
            return None

        api_url = "https://vision.googleapis.com/v1/images:annotate"
        texts = []

        for i, page in enumerate(self.doc):
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

            payload = {
                "requests": [{
                    "image": {"content": img_b64},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                }]
            }

            try:
                resp = requests.post(
                    f"{api_url}?key={self.vision_api_key}",
                    json=payload,
                    timeout=60,
                )
                result = resp.json()

                if 'error' in result:
                    print(f"  Vision API 오류 (페이지 {i+1}): {result['error']}")
                    texts.append("")
                    continue

                responses = result.get('responses', [{}])
                full_text = responses[0].get('fullTextAnnotation', {}).get('text', '')
                texts.append(full_text)
                print(f"  OCR 페이지 {i+1}/{self.page_count}: {len(full_text)}자")
            except Exception as e:
                print(f"  Vision OCR 실패 (페이지 {i+1}): {e}")
                texts.append("")

        total = sum(len(t.strip()) for t in texts)
        print(f"  Vision OCR 완료: 총 {total}자")
        return texts if total > 0 else None

    def extract_slide_titles(self) -> List[str]:
        """각 슬라이드의 제목(큰 글씨) 추출"""
        titles = []
        for page in self.doc:
            blocks = page.get_text("dict", flags=0)
            best_text = ""
            best_size = 0
            for block in blocks.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        size = span.get("size", 0)
                        if text and size > best_size and len(text) > 1:
                            best_size = size
                            best_text = text
            if best_text:
                titles.append(best_text)
        return titles

    def generate_thumbnail(self, page_num: int = 0, scale: float = 1.5) -> bytes:
        """특정 페이지의 썸네일 이미지 (PNG) 생성"""
        import fitz
        page = self.doc[page_num]
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def build_summary(self) -> str:
        """PDF 전체 내용 요약 생성"""
        titles = self.extract_slide_titles()
        if not titles:
            return ""
        lines = [f"{i}. {title}" for i, title in enumerate(titles, 1)]
        return "\n".join(lines)

    @staticmethod
    def clean_slide_text(text: str) -> str:
        """슬라이드 텍스트에서 NotebookLM 언급, OCR 아티팩트 등 제거"""
        # NotebookLM / Notebook LM 언급 제거 (대소문자 무시, 앞뒤 공백/마침표 포함)
        text = re.sub(r'[,.]?\s*A?\s*Notebook\s*LM\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[,.]?\s*노트북\s*LM\.?', '', text, flags=re.IGNORECASE)
        # 반복 ·E 패턴 제거 (OCR 아티팩트: ·E·E·E·E...)
        text = re.sub(r'(?:[·.]\s*E\s*){3,}', '', text)
        # ·가 3개 이상 반복되는 패턴 제거
        text = re.sub(r'(?:·\s*){3,}', '', text)
        # 0이 6개 이상 연속 → 빈 문자열 (OCR 실패한 숫자)
        text = re.sub(r'0{6,}', '', text)
        # 연속 공백 정리
        text = re.sub(r' {2,}', ' ', text)
        # 빈 줄이 3개 이상이면 2개로
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def build_content(self) -> str:
        """자료실 등록용 전체 텍스트 컨텐츠 생성"""
        texts = self.extract_all_text()
        parts = []
        for i, text in enumerate(texts, 1):
            clean = self.clean_slide_text(text)
            if clean:
                parts.append(f"[슬라이드 {i}]\n{clean}")
        return "\n\n\n".join(parts)

    def analyze(self) -> Dict[str, Any]:
        """PDF 전체 분석"""
        print(f"  PDF 분석: {self.pdf_path.name} ({self.page_count}페이지)")

        titles = self.extract_slide_titles()
        all_text = self.extract_all_text()
        full_text = " ".join(t.strip() for t in all_text if t.strip())

        keywords = self._extract_keywords(full_text)

        result = {
            "page_count": self.page_count,
            "titles": titles,
            "summary": self.build_summary(),
            "content": self.build_content(),
            "keywords": keywords,
            "total_chars": len(full_text),
        }

        print(f"  슬라이드: {self.page_count}장")
        print(f"  제목들: {titles[:5]}{'...' if len(titles) > 5 else ''}")
        print(f"  키워드: {keywords[:8]}")

        return result

    def _extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """텍스트에서 주요 키워드 추출"""
        stopwords = {
            "그리고", "하지만", "또한", "그래서", "때문에", "위해", "통해",
            "경우", "등의", "대한", "있는", "없는", "하는", "되는", "이는",
            "것이", "수술", "치료", "진단",
        }

        words = {}
        for word in text.split():
            clean = "".join(c for c in word if '\uac00' <= c <= '\ud7a3')
            if 2 <= len(clean) <= 6 and clean not in stopwords:
                words[clean] = words.get(clean, 0) + 1

        sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_n]]
