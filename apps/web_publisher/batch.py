#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BatchPublisher - 병렬 오케스트레이터
"""
import asyncio
import sys
from typing import List, Dict, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang.config import NoterangConfig, get_config
from noterang.auth import ensure_auth

from .config import WebPublisherConfig
from .pipeline import WebPublishPipeline


class BatchPublisher:
    """병렬 배치 퍼블리셔"""

    def __init__(
        self,
        titles: List[str],
        design: str = "인포그래픽",
        max_workers: int = 3,
        register: bool = True,
        visible: bool = True,
        article_type: str = "disease",
        slide_count: int = 15,
        publisher_config: WebPublisherConfig = None,
    ):
        self.titles = titles
        self.design = design
        self.max_workers = max_workers
        self.register = register
        self.visible = visible
        self.article_type = article_type
        self.slide_count = slide_count
        self.publisher_config = publisher_config or WebPublisherConfig.load()

    async def run(self) -> List[Dict[str, Any]]:
        """병렬 배치 실행"""
        print(f"\n배치 실행: {len(self.titles)}개 주제, 최대 {self.max_workers} 워커")
        print(f"  주제: {', '.join(self.titles)}")

        # 공통 1회 인증
        print("\n인증 확인...")
        if not await ensure_auth():
            print("  인증 실패")
            return [{"success": False, "error": "인증 실패", "title": t} for t in self.titles]

        semaphore = asyncio.Semaphore(self.max_workers)
        tasks = [
            self._run_worker(i, title, semaphore)
            for i, title in enumerate(self.titles)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외를 결과로 변환
        final = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                final.append({
                    "success": False,
                    "title": self.titles[i],
                    "error": str(r),
                })
            else:
                final.append(r)

        # 결과 요약
        success_count = sum(1 for r in final if r.get("success"))
        print(f"\n배치 완료: {success_count}/{len(self.titles)} 성공")
        return final

    async def _run_worker(
        self,
        worker_id: int,
        title: str,
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """개별 워커 실행"""
        async with semaphore:
            print(f"\n[워커 {worker_id}] {title} 시작")

            # 독립 브라우저 프로필을 위한 config
            config = NoterangConfig.load()
            config.worker_id = worker_id
            config.ensure_dirs()

            pipeline = WebPublishPipeline(
                title=title,
                design=self.design,
                register=self.register,
                visible=self.visible,
                article_type=self.article_type,
                slide_count=self.slide_count,
                noterang_config=config,
                publisher_config=self.publisher_config,
            )

            result = await pipeline.run()
            print(f"\n[워커 {worker_id}] {title} → {'성공' if result.get('success') else '실패'}")
            return result
