"""每日市场：进货、天气、折扣、涨价、售空。

同一个日期只有一种盘面（确定性随机），聊天、面板、账号本看到的价格一致。
"""
from __future__ import annotations

import random
from typing import Any

WEATHERS = (
    ("晴", 1.00, "天气好，菜多，价稳"),
    ("多云", 1.02, "货正常"),
    ("小雨", 1.08, "下雨，叶菜涨一点"),
    ("大雨", 1.16, "暴雨，菜少价高"),
    ("降温", 1.10, "天冷，火锅菜好卖"),
    ("升温", 1.05, "天热，瓜果走俏"),
)

#: 每类对天气的敏感度（乘在天气系数上）
KIND_SENSITIVE = {"drugs": 0.2, "groceries": 1.0, "takeout": 0.7,
                  "outfits": 0.3, "jewelry": 0.1}


def state_for(day: str) -> dict[str, Any]:
    """当天盘面：天气、每类系数、折扣、售空名单。"""
    rnd = random.Random("amo-market:%s" % str(day))
    weather, base, note = rnd.choice(WEATHERS)
    kinds: dict[str, float] = {}
    soldout: dict[str, list[str]] = {}
    discount: dict[str, float] = {}
    for kind, sensitive in KIND_SENSITIVE.items():
        factor = 1.0 + (base - 1.0) * sensitive
        factor *= 1.0 + rnd.uniform(-0.03, 0.03)
        kinds[kind] = round(factor, 3)
    return {"day": str(day), "weather": weather, "note": note,
            "factors": kinds, "soldout": soldout, "discount": discount}
