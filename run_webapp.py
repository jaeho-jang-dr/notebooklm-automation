#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF to Editable PPTX 웹앱 실행 스크립트
"""
import sys
import subprocess
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    """Streamlit 앱 실행"""
    app_path = Path(__file__).parent / "webapp" / "app.py"

    print("🚀 PDF → 편집 가능 PPTX 웹앱 시작...")
    print(f"   앱 경로: {app_path}")
    print()
    print("   브라우저에서 자동으로 열립니다.")
    print("   종료하려면 Ctrl+C를 누르세요.")
    print()

    try:
        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run",
                str(app_path),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
            ],
            check=True
        )
    except KeyboardInterrupt:
        print("\n👋 웹앱 종료")
    except subprocess.CalledProcessError as e:
        print(f"❌ 실행 실패: {e}")
        print()
        print("다음 명령으로 의존성을 설치하세요:")
        print("  pip install -r requirements-webapp.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
