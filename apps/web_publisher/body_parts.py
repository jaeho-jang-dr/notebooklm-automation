#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
부위별 키워드 매칭 (body-parts.ts 동기화)
"""
from typing import List

BODY_PARTS = [
    {"id": "shoulder", "label": "어깨 (견관절)",
     "keywords": ["어깨", "견관절", "회전근개", "오십견", "석회성건염", "유착성피막염"]},
    {"id": "elbow", "label": "팔꿈치 (주관절)",
     "keywords": ["팔꿈치", "주관절", "테니스엘보", "골퍼엘보", "상과염"]},
    {"id": "hand_wrist", "label": "손/손목",
     "keywords": ["손목", "손가락", "수근관", "방아쇠", "건초염", "터널증후군"]},
    {"id": "hip", "label": "고관절",
     "keywords": ["고관절", "대퇴골두", "무혈성괴사", "대퇴골"]},
    {"id": "knee", "label": "무릎 (슬관절)",
     "keywords": ["무릎", "슬관절", "십자인대", "반월상", "연골"]},
    {"id": "foot_ankle", "label": "발/발목",
     "keywords": ["발목", "족저근막", "아킬레스", "발바닥", "발뒤꿈치", "족부", "족주상골", "부골", "부주상골", "무지외반"]},
    {"id": "spine", "label": "척추",
     "keywords": ["척추", "허리", "목", "디스크", "협착", "측만", "경추", "요추"]},
]


def match_body_part(tags: List[str], title: str) -> str:
    """태그와 제목으로 부위 판별 (최다 매칭)"""
    search_text = " ".join(tags + [title]).lower()
    best_id = "etc"
    best_count = 0
    for part in BODY_PARTS:
        count = sum(1 for kw in part["keywords"] if kw in search_text)
        if count > best_count:
            best_count = count
            best_id = part["id"]
    return best_id
