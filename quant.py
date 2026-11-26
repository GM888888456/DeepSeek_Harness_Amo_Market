# -*- coding: utf-8 -*-
"""幻方量化：集团的量化子公司，也是「量化 → 算力 → 大模型」这条路的起点。

用户口径（2026-11-25）：给她建一个幻方量化，让她走梁圣（梁文锋）那条路——
先用量化把现金流和算力攒起来，再把算力喂给模型，最后两条腿一起走。

纯数据 + 纯函数，不落库。金额：亿元（规模）/ 万元（日盈亏）/ % 收益。
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List

PROFILE = {
    "name": "幻方量化",
    "full": "幻方量化（贵阳）私募基金管理有限公司",
    "since": 2018,
    "hq": "贵阳·观山湖（与集团同楼）",
    "office": "北京·金融街（策略与研究）",
    "licence": "私募证券投资基金管理人（登记编号 P1069xxx）",
    "chair": "沈晓沫（集团总裁兼实控人）",
    "gm": "陆宗铭（总经理，合规与渠道出身）",
    "cio": "周慕之（投资总监，兼集团高级副总裁）",
    "research": "何书棠（研究总监，因子与另类数据）",
    "aum_own": 38.0,
    "aum_fund": 90.0,
    "staff": 96,
    "note": "2018 年拿牌照做指数增强起家，2021 年自建萤火算力，2023 年把算力与团队分出一支做智脑大模型；现在量化的钱养算力，算力喂模型。",
}

STRATEGIES = [
    {"id": "csi500", "name": "中证 500 指数增强", "aum": 40.0, "ytd": 18.6, "drawdown": -6.4,
     "sharpe": 2.1, "capacity": 260.0, "note": "超额主要来自量价与另类数据，换手 60 倍"},
    {"id": "csi1000", "name": "中证 1000 指数增强", "aum": 8.0, "ytd": 21.3, "drawdown": -8.1,
     "sharpe": 1.9, "capacity": 180.0, "note": "小市值弹性大，回撤也大"},
    {"id": "neutral", "name": "市场中性", "aum": 34.0, "ytd": 9.4, "drawdown": -2.8,
     "sharpe": 2.6, "capacity": 200.0, "note": "对冲成本随基差走，基差一紧收益就薄"},
    {"id": "cta", "name": "CTA 商品趋势", "aum": 6.0, "ytd": 6.2, "drawdown": -4.6,
     "sharpe": 1.4, "capacity": 80.0, "note": "跟股市不相关，用来稳净值"},
    {"id": "opt", "name": "期权套利", "aum": 8.0, "ytd": 7.8, "drawdown": -1.9,
     "sharpe": 3.0, "capacity": 40.0, "note": "容量小，赚的是波动的钱"},
    {"id": "ai", "name": "AI 选股（萤火因子）", "aum": 6.0, "ytd": 27.5, "drawdown": -9.3,
     "sharpe": 1.7, "capacity": 60.0, "note": "用集团模型做多模态因子，新线，容量还没打满"},
]

PRODUCTS = [
    {"code": "HF500-1", "name": "幻方中证 500 增强 1 号", "since": "2019-04", "aum": 18.0,
     "nav": 2.418, "ytd": 18.6, "drawdown": -6.4, "fee": "1.5% + 20%"},
    {"code": "HF1000-1", "name": "幻方中证 1000 增强 1 号", "since": "2021-08", "aum": 12.0,
     "nav": 1.587, "ytd": 21.3, "drawdown": -8.1, "fee": "1.5% + 20%"},
    {"code": "HFN-3", "name": "幻方中性 3 号", "since": "2020-11", "aum": 20.0,
     "nav": 1.392, "ytd": 9.4, "drawdown": -2.8, "fee": "1% + 15%"},
    {"code": "HFC-1", "name": "幻方 CTA 1 号", "since": "2022-03", "aum": 10.0,
     "nav": 1.244, "ytd": 6.2, "drawdown": -4.6, "fee": "1% + 15%"},
    {"code": "HFOP-1", "name": "幻方期权套利 1 号", "since": "2022-09", "aum": 6.0,
     "nav": 1.188, "ytd": 7.8, "drawdown": -1.9, "fee": "0.8% + 10%"},
    {"code": "HFAI-1", "name": "幻方 AI 选股 1 号", "since": "2025-06", "aum": 6.0,
     "nav": 1.131, "ytd": 27.5, "drawdown": -9.3, "fee": "2% + 25%"},
]

RISK = {
    "单票上限": "5%（指数增强）/ 3%（中性）",
    "行业偏离": "±8%",
    "组合杠杆": "≤1.2 倍",
    "预警线": "-6% 降杠杆，-10% 清仓线",
    "策略相关性": "各线相关系数 < 0.4，月度复核",
    "合规": "交易所程序化报备、异常交易监控、投资决策留痕",
}

COMPUTE = {
    "clusters": [
        {"name": "萤火一号", "since": 2021, "gpus": 1200, "power": "6MW", "use": "量化因子训练"},
        {"name": "萤火二号", "since": 2023, "gpus": 2600, "power": "18MW",
         "use": "量化 + 集团模型预训练（共享 40%）"},
        {"name": "萤火三号", "since": 2026, "gpus": 0, "power": "12MW",
         "use": "在建，规划 4000 卡，建成后集团可借 30%"},
    ],
    "share_to_group": "35%",
    "note": "量化先买卡，卡闲着的时候喂模型——集团的模型能力是这么长出来的。",
}

PATH = [
    {"year": 2018, "title": "拿牌做量化", "note": "四个人、一台服务器，做中证 500 增强，第一年规模 3 亿。"},
    {"year": 2021, "title": "自建算力", "note": "意识到因子拼的是算力，砸下萤火一号；不再租云。"},
    {"year": 2023, "title": "分出智脑", "note": "把算力与研究团队分出一支做大模型，幻方继续供血。"},
    {"year": 2026, "title": "双轮并行", "note": "量化管钱、模型管未来；萤火三号建成后两条腿都够用。"},
]

RISK_LINES = [
    {"item": "指数增强组合跟踪误差", "value": "4.2%", "limit": "≤6%", "state": "正常"},
    {"item": "中性策略基差成本", "value": "年化 3.1%", "limit": "≤4.5%", "state": "偏紧"},
    {"item": "单票集中度（最大）", "value": "3.8%", "limit": "≤5%", "state": "正常"},
    {"item": "组合杠杆", "value": "1.14 倍", "limit": "≤1.2 倍", "state": "正常"},
    {"item": "本月最大回撤", "value": "-2.6%", "limit": "-6% 预警", "state": "正常"},
]


def _seed(*parts: str) -> int:
    return int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def pnl(day: str = "") -> Dict[str, Any]:
    """当天/昨夜的盈亏（按日期确定性生成，同一天不会变）。"""
    day = day or time.strftime("%Y-%m-%d")
    rnd = _seed("pnl", day) % 10000 / 10000.0
    aum = PROFILE["aum_own"] + PROFILE["aum_fund"]
    ret = round((rnd - 0.42) * 1.6, 3)
    return {
        "day": day,
        "aum": round(aum, 2),
        "ret_pct": ret,
        "pnl": round(aum * 10000 * ret / 100.0, 2),
        "best": "中证 1000 增强",
        "worst": "市场中性",
        "note": "净值已扣费，盘后 18:00 结算",
    }


def summary() -> Dict[str, Any]:
    aum = PROFILE["aum_own"] + PROFILE["aum_fund"]
    weighted = sum(s["aum"] * s["ytd"] for s in STRATEGIES) / max(1.0, sum(s["aum"] for s in STRATEGIES))
    return {
        "name": PROFILE["name"], "aum": round(aum, 2),
        "aum_own": PROFILE["aum_own"], "aum_fund": PROFILE["aum_fund"],
        "staff": PROFILE["staff"], "ytd": round(weighted, 2),
        "strategies": len(STRATEGIES), "products": len(PRODUCTS),
        "share_to_group": COMPUTE["share_to_group"],
        "line": PROFILE["note"],
    }


if __name__ == "__main__":   # python3 quant.py
    import json
    print(json.dumps(summary(), ensure_ascii=False))
    print(json.dumps(pnl(), ensure_ascii=False))
