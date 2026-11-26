# -*- coding: utf-8 -*-
"""文件价值判断：钱不是唯一尺度。

用户口径（2026-11-26）：大额不一定驳回——有些东西钱买不到，
比如政治资源、社会地位；反过来，纯花钱的也该压。

四维打分：
  政（政府/牌照/资质/军队/共建）  +2
  势（峰会/发布/品牌/大学/公益）  +1.5
  人（招聘/编制/骨干/专家）        +1
  产（上游/产能/机房/自研/独家）  +1.5
  钱：金额越大越扣分（>1500 万 -1.5，>3000 万 -3）
结论：总分 ≥1 批；≤ -1 驳；中间压着，留给她亲自定。
"""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

WEIGHTS = [
    ("政", 2.0, ("政务", "政府", "省委", "市委", "厅", "局", "国资", "央企", "协会",
                "牌照", "资质", "备案", "等保", "共建", "军", "院", "批文", "补贴")),
    ("势", 1.5, ("大会", "峰会", "论坛", "发布", "品牌", "媒体", "大学", "研究院",
                "捐", "公益", "标准", "联盟", "展")),
    ("人", 1.0, ("招聘", "编制", "骨干", "专家", "团队", "培训", "校招", "猎头")),
    ("产", 1.5, ("上游", "产能", "封测", "机房", "算力", "自研", "独家", "锁", "供应链",
                "芯片", "液冷", "电力", "专利")),
]

KIND_BIAS = {"合作": 1.0, "投资": -0.5, "法务": 0.8, "招聘": 0.8,
             "预算": 0.3, "采购": 0.0, "离职": 0.0}


def score(doc: Dict[str, Any]) -> Dict[str, Any]:
    text = "%s %s" % (doc.get("title") or "", doc.get("ask") or "")
    hits = []
    total = 0.0
    for name, w, words in WEIGHTS:
        if any(wd in text for wd in words):
            total += w
            hits.append(name)
    kind = str(doc.get("kind") or "")
    total += KIND_BIAS.get(kind, 0.0)
    try:
        amount = float(doc.get("amount") or 0)
    except Exception:
        amount = 0.0
    if amount >= 3000:
        total -= 3.0
        hits.append("钱-")
    elif amount >= 1500:
        total -= 1.5
        hits.append("钱-")
    return {"score": round(total, 1), "hits": hits, "amount": amount, "kind": kind}


def verdict(doc: Dict[str, Any]) -> Tuple[str, str]:
    """返回 (approve|reject|hold, 一句理由)。"""
    r = score(doc)
    s, hits = r["score"], r["hits"]
    why = "+".join(h for h in hits if not h.startswith("钱"))
    if s >= 1.0:
        return "approve", ("值这个钱（%s）" % (why or "综合")) if why else "值这个钱"
    if s <= -1.0:
        return "reject", ("纯花钱，没换到东西（%s）" % ("、".join(hits) or "无加分")) if hits else "纯花钱"
    return "hold", "可批可不批，留着她自己定"
