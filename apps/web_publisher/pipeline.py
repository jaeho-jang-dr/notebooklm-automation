#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPublishPipeline - NotebookLM → PDF 분석 → 자료실 등록
"""
import logging
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# noterang 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from noterang import Noterang, WorkflowResult
from noterang.config import NoterangConfig, get_config
from noterang.prompts import SlidePrompts

from .config import WebPublisherConfig
from .body_parts import BODY_PARTS, match_body_part
from .pdf_analyzer import PDFAnalyzer
from .file_manager import FileManager
from .firestore_client import FirestoreClient


class WebPublishPipeline:
    """전체 파이프라인: NotebookLM → PDF 분석 → 자료실 등록"""

    def __init__(
        self,
        title: str,
        queries: List[str] = None,
        pdf_path: str = None,
        register: bool = True,
        visible: bool = True,
        article_type: str = "disease",
        design: str = "인포그래픽",
        slide_count: int = 15,
        noterang_config: NoterangConfig = None,
        publisher_config: WebPublisherConfig = None,
    ):
        self.title = title
        self.queries = queries
        self.pdf_path = Path(pdf_path) if pdf_path else None
        self.register = register
        self.visible = visible
        self.article_type = article_type
        self.design = design
        self.slide_count = slide_count
        self.noterang_config = noterang_config or get_config()
        self.publisher_config = publisher_config or WebPublisherConfig.load()

    def get_research_queries(self) -> List[str]:
        """한의학 제외, 정형외과 관점 검색 쿼리 생성"""
        if self.queries:
            return [f"{q} -한의학 -한방 -침 -뜸 -한의원" for q in self.queries]

        topic = self.title
        return [
            f"{topic} 정형외과 원인 증상 치료 -한의학 -한방 -침 -뜸 -한의원",
            f"{topic} 최신 치료법 수술 비수술 재활 -한의학 -한방치료",
            f"{topic} 진단 검사 예방 운동 -한의학 -한방",
        ]

    def get_focus_prompt(self) -> str:
        """디자인 스타일 + 한글 + 쉬운 설명 프롬프트"""
        prompts = SlidePrompts()
        design_prompt = prompts.get_prompt(self.design) or ""

        return f"""{design_prompt}

[추가 요청사항]
- 반드시 한글로 작성해주세요
- 영어는 의학 전문용어만 괄호 안에 최소한으로 병기
- 환자도 이해할 수 있는 쉽고 친근한 표현 사용
- 한의학/한방/침/뜸 관련 내용 완전히 제외
- 정형외과 관점에서만 설명
- 슬라이드 {self.slide_count}장으로 구성
- 인포그래픽 플랫 디자인: 깔끔한 아이콘, 도표, 플로우차트 활용
- 각 슬라이드마다 핵심 포인트를 시각적으로 전달
- 핵심 주제: {self.title}
- 구성 예시: 정의 → 원인/분류 → 증상 → 진단 → 치료법 → 예방/재활"""

    def generate_tags(self, pdf_keywords: List[str] = None) -> List[str]:
        """제목 + PDF 분석 키워드로 태그 생성"""
        design_tag = self.design.replace(" ", "")
        tags = ["자동생성", "노트랑", design_tag]

        # 부위 감지
        body_part = match_body_part(pdf_keywords or [], self.title)
        if body_part != "etc":
            part_info = next((p for p in BODY_PARTS if p["id"] == body_part), None)
            if part_info:
                tags.append(part_info["label"])

        # 제목 키워드
        for word in self.title.split():
            if len(word) >= 2 and word not in tags:
                tags.append(word)

        # PDF에서 추출한 키워드 (상위 5개)
        if pdf_keywords:
            for kw in pdf_keywords[:5]:
                if kw not in tags and len(kw) >= 2:
                    tags.append(kw)

        return tags

    async def run_noterang(self) -> WorkflowResult:
        """NotebookLM 자동화 (PDF만 다운로드, PPTX 변환 건너뛰기)"""
        noterang = Noterang(config=self.noterang_config)
        return await noterang.run(
            title=self.title,
            research_queries=self.get_research_queries(),
            focus=self.get_focus_prompt(),
            language="ko",
            skip_convert=True,
        )

    def _validate_pdf_path(self, pdf_path: Path) -> Optional[str]:
        """
        PDF 파일 경로 유효성 검사.

        Returns:
            오류 메시지 문자열, 또는 유효하면 None.
        """
        if not pdf_path.exists():
            return f"PDF 파일을 찾을 수 없습니다: {pdf_path}"
        if not pdf_path.is_file():
            return f"PDF 경로가 파일이 아닙니다: {pdf_path}"
        if pdf_path.suffix.lower() != '.pdf':
            return f"PDF 확장자가 아닙니다: {pdf_path.suffix}"
        try:
            size = pdf_path.stat().st_size
        except OSError as e:
            return f"PDF 파일 정보를 읽을 수 없습니다: {e}"
        if size == 0:
            return f"PDF 파일이 비어 있습니다 (0 bytes): {pdf_path}"
        return None

    async def run(self) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        start_time = time.time()

        # 입력 검증
        if not self.title or not self.title.strip():
            return {"success": False, "error": "제목이 비어 있습니다"}

        print("\n" + "=" * 60)
        print(f"  웹 자료실 퍼블리셔")
        print(f"  제목: {self.title}")
        print(f"  디자인: {self.design}")
        print(f"  자료실 등록: {'예' if self.register else '아니오'}")
        if self.pdf_path:
            print(f"  기존 PDF: {self.pdf_path}")
        print("=" * 60)

        notebook_id = None
        pdf_path = self.pdf_path

        # Step 1: NotebookLM으로 PDF 생성 (기존 PDF가 없을 때만)
        if not pdf_path:
            print("\n[1/4] NotebookLM 슬라이드 생성...")
            try:
                result = await self.run_noterang()
            except Exception as e:
                elapsed = int(time.time() - start_time)
                error_msg = f"NotebookLM 자동화 예외: {e}"
                print(f"\n  파이프라인 실패: {error_msg} ({elapsed}초)")
                logger.error("run_noterang raised an exception", exc_info=True)
                return {"success": False, "error": error_msg, "duration": elapsed}

            if not result.success or not result.pdf_path:
                elapsed = int(time.time() - start_time)
                error_msg = result.error or "PDF 생성 실패 (이유 불명)"
                print(f"\n  파이프라인 실패: {error_msg} ({elapsed}초)")
                return {"success": False, "error": error_msg, "duration": elapsed}

            pdf_path = Path(result.pdf_path)
            notebook_id = result.notebook_id
            print(f"  PDF 생성 완료: {pdf_path}")
        else:
            print("\n[1/4] 기존 PDF 사용")
            path_error = self._validate_pdf_path(pdf_path)
            if path_error:
                return {"success": False, "error": path_error}

        # Step 2: PDF 분석
        print("\n[2/4] PDF 슬라이드 분석...")
        analyzer = None
        try:
            analyzer = PDFAnalyzer(pdf_path, self.publisher_config.vision_api_key)
            try:
                analysis = analyzer.analyze()
            except Exception as e:
                elapsed = int(time.time() - start_time)
                error_msg = f"PDF 분석 실패: {e}"
                print(f"  ❌ {error_msg}")
                logger.error(f"PDFAnalyzer.analyze failed: {pdf_path}", exc_info=True)
                return {"success": False, "error": error_msg, "duration": elapsed}

            try:
                thumbnail = analyzer.generate_thumbnail(0) if getattr(analyzer, 'page_count', 0) > 0 else None
                analysis["thumbnail"] = thumbnail if thumbnail else None
            except Exception as e:
                # 썸네일 실패는 치명적이지 않음 — 경고 후 계속
                print(f"  ⚠️ 썸네일 생성 실패 (건너뜀): {e}")
                logger.warning(f"Thumbnail generation failed: {e}")
                analysis["thumbnail"] = None

        finally:
            if analyzer is not None:
                try:
                    analyzer.close()
                except Exception as e:
                    logger.warning(f"PDFAnalyzer.close() error (ignored): {e}")

        # Step 3: 파일 복사
        print("\n[3/4] 웹앱에 파일 복사...")
        try:
            file_mgr = FileManager(self.publisher_config.uploads_dir)
            pdf_url, thumb_url = file_mgr.copy_pdf_and_thumbnail(
                pdf_path, self.title, analysis.get("thumbnail")
            )
        except PermissionError as e:
            elapsed = int(time.time() - start_time)
            error_msg = f"파일 복사 권한 없음: {e}"
            print(f"  ❌ {error_msg}")
            logger.error("File copy PermissionError", exc_info=True)
            return {"success": False, "error": error_msg, "duration": elapsed}
        except OSError as e:
            elapsed = int(time.time() - start_time)
            error_msg = f"파일 복사 실패 (디스크 공간 또는 경로 오류): {e}"
            print(f"  ❌ {error_msg}")
            logger.error("File copy OSError", exc_info=True)
            return {"success": False, "error": error_msg, "duration": elapsed}
        except Exception as e:
            elapsed = int(time.time() - start_time)
            error_msg = f"파일 복사 중 예외: {e}"
            print(f"  ❌ {error_msg}")
            logger.error("File copy unexpected error", exc_info=True)
            return {"success": False, "error": error_msg, "duration": elapsed}

        # Step 4: 자료실 등록
        doc_id = None
        if self.register:
            print("\n[4/4] 자료실 등록...")
            tags = self.generate_tags(analysis.get("keywords", []))
            client = FirestoreClient(self.publisher_config.firebase_project_id)
            try:
                doc_id = client.register_article(
                    title=self.title,
                    pdf_url=pdf_url,
                    thumb_url=thumb_url,
                    analysis=analysis,
                    tags=tags,
                    article_type=self.article_type,
                    visible=self.visible,
                )
            except Exception as e:
                # Firestore 등록 실패는 파이프라인 전체를 실패로 보지 않음 —
                # PDF 파일은 이미 복사됐으므로 경고 후 계속
                print(f"  ⚠️ 자료실 등록 실패 (파일은 복사됨): {e}")
                logger.error("Firestore register_article raised an exception", exc_info=True)
                doc_id = None

            if doc_id is None:
                print("  ⚠️ 자료실 등록 실패. PDF는 웹앱에 복사되었습니다.")
        else:
            print("\n[4/4] 자료실 등록 건너뜀 (--no-register)")

        elapsed = int(time.time() - start_time)

        # 결과 요약
        print("\n" + "=" * 60)
        print("  파이프라인 완료")
        print("=" * 60)
        print(f"  제목: {self.title}")
        print(f"  PDF: {pdf_path}")
        print(f"  슬라이드: {analysis.get('page_count', '?')}장")
        print(f"  URL: {pdf_url}")
        if thumb_url:
            print(f"  썸네일: {thumb_url}")
        if doc_id:
            print(f"  자료 ID: {doc_id}")
        print(f"  소요시간: {elapsed}초")
        print("=" * 60)

        return {
            "success": True,
            "title": self.title,
            "notebook_id": notebook_id,
            "pdf_path": str(pdf_path),
            "pdf_url": pdf_url,
            "thumb_url": thumb_url,
            "doc_id": doc_id,
            "page_count": analysis.get("page_count", 0),
            "duration": elapsed,
        }
