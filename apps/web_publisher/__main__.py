"""python -m apps.web_publisher 진입점"""
import sys
from .cli import main

sys.exit(main() or 0)
