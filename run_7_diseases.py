#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
7개 질환 노트북 생성 및 슬라이드 제작
- 대퇴골두무혈성괴사증
- 좌골신경통
- 아킬레스건염
- 중족골통
- 이상근증후군
- 고관절활액낭염
- 대퇴충돌증후군
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from noterang import Noterang


# 7개 질환 목록
DISEASES = [
    "대퇴골두무혈성괴사증",
    "좌골신경통",
    "아킬레스건염",
    "중족골통",
    "이상근증후군",
    "고관절활액낭염",
    "대퇴충돌증후군",
]


async def main():
    """7개 질환 순차 처리"""
    print("=" * 60)
    print("7개 질환 노트북 생성 및 슬라이드 제작")
    print("=" * 60)
    print(f"대상: {', '.join(DISEASES)}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    noterang = Noterang()
    results = []

    for i, disease in enumerate(DISEASES, 1):
        print(f"\n[{i}/7] {disease}")
        print("-" * 40)

        try:
            result = await noterang.run_browser(
                title=disease,
                sources=[],  # 자동 자료 수집
                focus=f"{disease}의 원인, 증상, 진단, 치료방법, 재활",
                language="ko"  # 반드시 한글!
            )

            if result.success:
                print(f"  [OK] 완료!")
                print(f"       PDF: {result.pdf_path}")
                print(f"       PPTX: {result.pptx_path}")
                print(f"       슬라이드: {result.slide_count}장")
            else:
                print(f"  [FAIL] {result.error}")

            results.append({
                "disease": disease,
                "success": result.success,
                "pdf": str(result.pdf_path) if result.pdf_path else None,
                "pptx": str(result.pptx_path) if result.pptx_path else None,
                "slides": result.slide_count,
                "error": result.error
            })

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            results.append({
                "disease": disease,
                "success": False,
                "error": str(e)
            })

        # 다음 질환 전 잠시 대기
        if i < len(DISEASES):
            print("  (다음 질환 처리 대기...)")
            await asyncio.sleep(5)

    # 최종 결과 요약
    print("\n" + "=" * 60)
    print("최종 결과 요약")
    print("=" * 60)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"성공: {success_count}/{len(DISEASES)}")

    for r in results:
        status = "[OK]" if r.get("success") else "[FAIL]"
        print(f"  {status} {r['disease']}")
        if r.get("pptx"):
            print(f"       -> {r['pptx']}")

    print("=" * 60)
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
