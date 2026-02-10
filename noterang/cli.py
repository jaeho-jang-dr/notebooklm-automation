#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 CLI (Command Line Interface)

Usage:
    python -m noterang run "제목" --queries "쿼리1,쿼리2,쿼리3"
    python -m noterang list
    python -m noterang delete <notebook_id>
    python -m noterang login
    python -m noterang config --apify-key "..." --app-password "..."
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description="노트랑 - NotebookLM 완전 자동화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 전체 자동화
  python -m noterang run "견관절회전근개 파열" --queries "원인,치료,재활" --focus "병인, 치료방법"

  # 노트북 목록
  python -m noterang list

  # 노트북 삭제
  python -m noterang delete abc123

  # 로그인
  python -m noterang login --show

  # 설정
  python -m noterang config --apify-key "your_key" --app-password "xxxx xxxx xxxx xxxx"

  # 기존 노트북 슬라이드 재생성
  python -m noterang regenerate abc123 --title "제목"

  # 배치 실행
  python -m noterang batch topics.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="명령")

    # run 명령
    run_parser = subparsers.add_parser("run", help="전체 자동화 실행")
    run_parser.add_argument("title", help="노트북 제목")
    run_parser.add_argument("--queries", "-q", help="연구 쿼리 (쉼표 구분)")
    run_parser.add_argument("--focus", "-f", help="슬라이드 집중 주제")
    run_parser.add_argument("--language", "-l", default="ko", help="언어 (기본: ko)")
    run_parser.add_argument("--skip-research", action="store_true", help="연구 단계 건너뛰기")
    run_parser.add_argument("--skip-download", action="store_true", help="다운로드 건너뛰기")
    run_parser.add_argument("--skip-convert", action="store_true", help="PPTX 변환 건너뛰기")

    # regenerate 명령
    regen_parser = subparsers.add_parser("regenerate", help="기존 노트북 슬라이드 재생성")
    regen_parser.add_argument("notebook_id", help="노트북 ID")
    regen_parser.add_argument("--title", "-t", help="제목 (파일명용)")
    regen_parser.add_argument("--focus", "-f", help="집중 주제")
    regen_parser.add_argument("--language", "-l", default="ko", help="언어")

    # list 명령
    subparsers.add_parser("list", help="노트북 목록 조회")

    # delete 명령
    delete_parser = subparsers.add_parser("delete", help="노트북 삭제")
    delete_parser.add_argument("notebook_id", help="노트북 ID")

    # login 명령
    login_parser = subparsers.add_parser("login", help="로그인")
    login_parser.add_argument("--show", action="store_true", help="브라우저 표시")
    login_parser.add_argument("--check", action="store_true", help="인증 상태만 확인")

    # config 명령
    config_parser = subparsers.add_parser("config", help="설정 관리")
    config_parser.add_argument("--apify-key", help="Apify API 키")
    config_parser.add_argument("--app-password", help="NotebookLM 앱 비밀번호")
    config_parser.add_argument("--download-dir", help="다운로드 디렉토리")
    config_parser.add_argument("--show", action="store_true", help="현재 설정 표시")

    # batch 명령
    batch_parser = subparsers.add_parser("batch", help="배치 실행")
    batch_parser.add_argument("topics_file", help="토픽 JSON 파일")
    batch_parser.add_argument("--parallel", action="store_true", help="병렬 실행")

    # convert 명령
    convert_parser = subparsers.add_parser("convert", help="PDF를 PPTX로 변환")
    convert_parser.add_argument("pdf_path", help="PDF 파일 경로")
    convert_parser.add_argument("--output", "-o", help="출력 경로")

    # prompts 명령 (100개 슬라이드 디자인 프롬프트)
    prompts_parser = subparsers.add_parser("prompts", help="슬라이드 디자인 프롬프트 관리")
    prompts_parser.add_argument("--list", "-l", action="store_true", help="전체 스타일 목록")
    prompts_parser.add_argument("--categories", "-c", action="store_true", help="카테고리 목록")
    prompts_parser.add_argument("--get", "-g", help="특정 스타일 프롬프트 출력")
    prompts_parser.add_argument("--search", "-s", help="스타일 검색")
    prompts_parser.add_argument("--category", help="특정 카테고리 스타일 목록")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 명령 실행
    if args.command == "run":
        cmd_run(args)
    elif args.command == "regenerate":
        cmd_regenerate(args)
    elif args.command == "list":
        cmd_list()
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "login":
        cmd_login(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "convert":
        cmd_convert(args)
    elif args.command == "prompts":
        cmd_prompts(args)


def cmd_run(args):
    """전체 자동화 실행"""
    from .core import Noterang

    queries = args.queries.split(",") if args.queries else []

    noterang = Noterang()
    result = asyncio.run(noterang.run(
        title=args.title,
        research_queries=queries,
        focus=args.focus,
        language=args.language,
        skip_research=args.skip_research,
        skip_download=args.skip_download,
        skip_convert=args.skip_convert
    ))

    print(f"\n결과: {json.dumps(result.to_dict(), ensure_ascii=False, indent=2)}")


def cmd_regenerate(args):
    """슬라이드 재생성"""
    from .core import Noterang

    noterang = Noterang()
    result = asyncio.run(noterang.regenerate(
        notebook_id=args.notebook_id,
        notebook_title=args.title,
        language=args.language,
        focus=args.focus
    ))

    print(f"\n결과: {json.dumps(result.to_dict(), ensure_ascii=False, indent=2)}")


def cmd_list():
    """노트북 목록"""
    from .notebook import list_notebooks

    notebooks = list_notebooks()

    if not notebooks:
        print("노트북이 없습니다.")
        return

    print(f"\n노트북 목록 ({len(notebooks)}개):")
    print("-" * 60)
    for nb in notebooks:
        print(f"  ID: {nb.get('id', 'N/A')[:20]}...")
        print(f"  제목: {nb.get('title', 'N/A')}")
        print("-" * 60)


def cmd_delete(args):
    """노트북 삭제"""
    from .notebook import delete_notebook

    if delete_notebook(args.notebook_id):
        print(f"✓ 삭제 완료: {args.notebook_id}")
    else:
        print(f"❌ 삭제 실패: {args.notebook_id}")


def cmd_login(args):
    """로그인"""
    from .auth import check_auth, run_auto_login

    if args.check:
        if check_auth():
            print("✓ 인증 유효")
        else:
            print("❌ 인증 만료 또는 없음")
        return

    success = run_auto_login(headless=not args.show)
    if success:
        print("✓ 로그인 성공")
    else:
        print("❌ 로그인 실패")


def cmd_config(args):
    """설정 관리"""
    from .config import get_config, init_config

    if args.show:
        config = get_config()
        print("\n현재 설정:")
        print("-" * 40)
        for key, value in config.to_dict().items():
            # 민감 정보 마스킹
            if 'key' in key.lower() or 'password' in key.lower():
                if value:
                    value = value[:4] + "****" + value[-4:] if len(str(value)) > 8 else "****"
            print(f"  {key}: {value}")
        return

    # 설정 업데이트
    kwargs = {}
    if args.apify_key:
        kwargs['apify_api_key'] = args.apify_key
    if args.app_password:
        kwargs['notebooklm_app_password'] = args.app_password
    if args.download_dir:
        kwargs['download_dir'] = args.download_dir

    if kwargs:
        init_config(**kwargs)
        print("✓ 설정 저장 완료")
    else:
        print("설정할 값이 없습니다. --help로 옵션을 확인하세요.")


def cmd_batch(args):
    """배치 실행"""
    from .core import run_batch

    topics_file = Path(args.topics_file)
    if not topics_file.exists():
        print(f"❌ 파일 없음: {topics_file}")
        return

    with open(topics_file, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    results = asyncio.run(run_batch(topics, parallel=args.parallel))

    print(f"\n배치 결과 ({len(results)}개):")
    success_count = sum(1 for r in results if r.success)
    print(f"  성공: {success_count}/{len(results)}")

    for r in results:
        status = "✓" if r.success else "❌"
        print(f"  {status} {r.notebook_title}: {r.slide_count}슬라이드")


def cmd_convert(args):
    """PDF to PPTX 변환"""
    from .convert import pdf_to_pptx

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ 파일 없음: {pdf_path}")
        return

    output_path = Path(args.output) if args.output else None
    pptx_path, count = pdf_to_pptx(pdf_path, output_path)

    print(f"✓ 변환 완료: {pptx_path} ({count}슬라이드)")


def cmd_prompts(args):
    """슬라이드 디자인 프롬프트 관리"""
    from .prompts import SlidePrompts

    prompts = SlidePrompts()

    if args.list:
        # 전체 스타일 목록
        print(f"\n슬라이드 디자인 스타일 ({len(prompts)}개)")
        print("=" * 50)
        for category in prompts.list_categories():
            styles = prompts.get_by_category(category)
            print(f"\n[{category}] ({len(styles)}개)")
            for style in styles:
                print(f"  - {style['name']}")
        return

    if args.categories:
        # 카테고리 목록
        categories = prompts.list_categories()
        print(f"\n카테고리 ({len(categories)}개):")
        for cat in categories:
            count = len(prompts.get_by_category(cat))
            print(f"  - {cat} ({count}개)")
        return

    if args.category:
        # 특정 카테고리 스타일
        styles = prompts.get_by_category(args.category)
        if not styles:
            print(f"❌ 카테고리 없음: {args.category}")
            return
        print(f"\n[{args.category}] 스타일 ({len(styles)}개):")
        for style in styles:
            print(f"  - {style['name']}")
        return

    if args.search:
        # 스타일 검색
        results = prompts.search(args.search)
        if not results:
            print(f"❌ 검색 결과 없음: {args.search}")
            return
        print(f"\n'{args.search}' 검색 결과 ({len(results)}개):")
        for style in results:
            print(f"  - {style['name']} ({style['category']})")
        return

    if args.get:
        # 특정 스타일 프롬프트
        prompt = prompts.get_prompt(args.get)
        if not prompt:
            print(f"❌ 스타일 없음: {args.get}")
            return
        print(f"\n[{args.get}] 프롬프트:")
        print("-" * 50)
        print(prompt)
        return

    # 기본: 간략 정보
    print(f"\n노트랑 슬라이드 프롬프트 ({len(prompts)}개 스타일)")
    print("=" * 50)
    print(f"기본 스타일: {prompts.default_style}")
    print(f"카테고리: {', '.join(prompts.list_categories())}")
    print("\n사용법:")
    print("  --list, -l      전체 스타일 목록")
    print("  --categories, -c 카테고리 목록")
    print("  --get, -g STYLE  특정 스타일 프롬프트")
    print("  --search, -s QUERY 스타일 검색")
    print("  --category CAT   특정 카테고리 스타일")


if __name__ == "__main__":
    main()
