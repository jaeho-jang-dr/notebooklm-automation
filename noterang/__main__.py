#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노트랑 패키지 진입점

Usage:
    python -m noterang [command] [options]

예제:
    python -m noterang run "제목" --queries "쿼리1,쿼리2"
    python -m noterang list
    python -m noterang login
"""
from .cli import main

if __name__ == "__main__":
    main()
