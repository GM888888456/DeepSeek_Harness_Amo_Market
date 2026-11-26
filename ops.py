# -*- coding: utf-8 -*-
"""集团日常：每天要批的文件、大方向、绩效 D 的清退与补招。

用户口径（2026-11-25）：
- 得让她自己操作：每天批文件、给大方向；
- 绩效 D 的直接开除，然后招新的补上。

状态跟 company_live 放在同一个目录下（ops_state.json），
company_live 管人，这边管「事」。

文档结构
    doc = {id, kind, title, dept, dept_id, amount, days, from, ask, risk, hint}
    kind: 采购 / 招聘 / 预算 / 离职 / 法务 / 投资 / 合作
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional

STATE = "ops_state.json"


def _path(data_dir: str) -> str:
    return os.path.join(str(data_dir or "."), STATE)


def load(data_dir: str) -> Dict[str, Any]:
    try:
        with open(_path(data_dir), encoding="utf-8") as stream:
            state = json.load(stream)
        if not isinstance(state, dict):
            raise ValueError
    except Exception:
        state = {}
    state.setdefault("strategy", "")
    state.setdefault("pending", {})      # day -> [doc]
    state.setdefault("done", [])         # 已批/已驳
    state.setdefault("fired_d", [])
    state.setdefault("gaps", [])         # 待补招
    return state


def save(data_dir: str, state: Dict[str, Any]) -> bool:
    path = _path(data_dir)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def today() -> str:
    return time.strftime("%Y-%m-%d")


# ── 大方向 ────────────────────────────────────────────────────────────
STRATEGIES = [
    {
        "id": "compute", "name": "算力先行",
        "line": "把现金砸进贵安三期和液冷，先把算力卖成现金牛，模型慢半步不要紧。",
        "effect": "采购类文件金额上调、基建与芯片招聘优先、行业项目收敛",
        "kpi": "算力售出率 ≥90%，PUE ≤1.18",
    },
    {
        "id": "model", "name": "模型降本",
        "line": "不铺新机房，把推理成本压下来，用更低的价把 API 打进行业客户。",
        "effect": "研发院预算上调、招聘偏推理优化、采购文件偏软件与授权",
        "kpi": "推理单位成本每季降 15%，API 毛利 ≥55%",
    },
    {
        "id": "industry", "name": "行业深耕",
        "line": "少做新客户，把政企、能源、金融做成可复制的方案，先把回款抓回来。",
        "effect": "解决方案预算上调、交付与客户成功招聘优先、应收压降",
        "kpi": "验收后 90 天回款率 ≥85%，续约率 ≥90%",
    },
    {
        "id": "quant", "name": "量化反哺",
        "line": "幻方那边的策略收益和自建算力反哺集团，AI 选股与模型共建一起推。",
        "effect": "幻方算力投入上调、量化与 AI 交叉岗位优先、集团自有项目让路",
        "kpi": "幻方净值回撤 ≤8%，集团自用算力占比 ≥35%",
    },
]


def strategy(data_dir: str = "") -> Optional[Dict[str, Any]]:
    sid = str(load(data_dir).get("strategy") or "")
    for s in STRATEGIES:
        if s["id"] == sid:
            return s
    return None


def set_strategy(data_dir: str, key: str) -> Dict[str, Any]:
    key = str(key or "").strip().lower()
    picked = None
    for s in STRATEGIES:
        if key in (s["id"], s["name"]) or key and (key in s["name"] or key in s["line"]):
            picked = s
            break
    if not picked:
        return {"ok": False, "msg": "没有这个方向，可选：%s" % "、".join(s["name"] for s in STRATEGIES)}
    state = load(data_dir)
    state["strategy"] = picked["id"]
    save(data_dir, state)
    return {"ok": True, "strategy": picked,
            "msg": "大方向定成「%s」：%s" % (picked["name"], picked["line"])}


# ── 每天要批的文件 ────────────────────────────────────────────────────
_TEMPLATES = [
    ("采购", "贵安三期液冷改造增补预算", "idc", 1860.0,
     "三期 2 号楼全上冷板液冷，比风冷省 11% 电，工期 45 天。",
     "币价与铜价波动；施工期机房降容"),

    ("采购", "H200 服务器 128 台（含三年保）", "supply", 3920.0,
     "客户留了 20 天窗口，先付 30% 定金锁产能。",
     "出口管制口径变化；机位与电力要同步"),

    ("招聘", "大模型研发院补 6 名训练工程师", "research", 32.4,
     "MoE 这代缺人，靠外包一天烧三万。",
     "薪资倒挂；新人爬产期 2 个月"),

    ("招聘", "客户成功部补 3 人（续约季）", "success", 5.4,
     "人均带 18 家太多，续约季前补上。",
     "短期成本上升，续约率见效果在季度末"),

    ("预算", "市场部 Q1 品牌预算追加", "marketing", 380.0,
     "行业展会 + 开发者大会，去年线索转化 1.8。",
     "线索接不住就白花；去年就吃过一次"),

    ("预算", "安全部等保三级复测与整改", "security", 96.0,
     "测评机构已排期，整改项 14 个。",
     "不整改影响政企投标"),

    ("离职", "财务中心会计主管转岗或离职", "finance", 9.6,
     "连续两季结账超期、错账 7 笔，绩效 D。",
     "人手紧，走了要补"),

    ("离职", "芯片部量产经理绩效 D 处理", "silicon", 19.2,
     "封测厂排产压错，交期延后两周。",
     "量产正在爬坡，交接风险高"),

    ("法务", "某行业客户合同违约条款争议", "legal", 0.0,
     "对方要加无限责任条款，建议不签。",
     "丢单风险；签了风险更大"),

    ("投资", "参股上游封测厂 8% 股权", "strategy", 2600.0,
     "锁产能，估值按上轮 8 折谈。",
     "资金占用；关联交易要披露"),

    ("合作", "与省政务云共建算力专区", "solution", 0.0,
     "三年框架，第一年不赚钱，占位。",
     "回款慢；要垫资"),

    ("采购", "幻方量化萤火三号集群扩容（800P）", "idc", 5400.0,
     "量化那边策略容量不够，扩容后集团可借用 30%。",
     "折旧压力；策略收益不达预期就成包袱"),
]


def _num(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:6], 16)


def generate_day(data_dir: str, day: str = "", count: int = 4) -> List[Dict[str, Any]]:
    """按天生成待批文件（同一天同一份，不会每次刷新都变）。"""
    day = day or today()
    state = load(data_dir)
    # 只要这一天已经生成过（哪怕是空列表，说明都批完了），就不要再生成
    if day in state["pending"]:
        return state["pending"][day]
    seed = _num(day)
    picked = []
    idx = 0
    while len(picked) < count and idx < len(_TEMPLATES) * 3:
        i = (seed + idx * 5) % len(_TEMPLATES)
        tpl = _TEMPLATES[i]
        if tpl not in picked:
            picked.append(tpl)
        idx += 1
    docs = []
    for n, (kind, title, dept_id, amount, ask, risk) in enumerate(picked, start=1):
        docs.append({
            "id": "%s-%02d" % (day.replace("-", ""), n),
            "kind": kind, "title": title, "dept_id": dept_id,
            "amount": float(amount), "days": 3 + (n % 4),
            "from": _dept_name(dept_id), "ask": ask, "risk": risk,
            "day": day,
        })
    state["pending"][day] = docs
    save(data_dir, state)
    return docs


def _dept_name(dept_id: str) -> str:
    try:
        import company as _co
        for d in _co.departments():
            if d["id"] == dept_id:
                return d["name"]
    except Exception:
        pass
    return {"strategy": "战略投资部"}.get(dept_id, dept_id)


def pending(data_dir: str, day: str = "") -> List[Dict[str, Any]]:
    day = day or today()
    return list(load(data_dir)["pending"].get(day) or [])


def decide(data_dir: str, doc_id: str, verdict: str = "approve", note: str = "") -> Dict[str, Any]:
    """批一份文件。approve 才动钱，reject 只留痕。"""
    state = load(data_dir)
    day = today()
    docs = state["pending"].get(day) or []
    target = None
    for d in docs:
        if d["id"] == doc_id or doc_id in d["title"]:
            target = d
            break
    if not target:
        return {"ok": False, "msg": "今天的待批里没有这份（%s）" % doc_id}
    docs.remove(target)
    verdict = "approve" if str(verdict).lower() in ("approve", "ok", "批", "同意", "1") else "reject"
    target = dict(target)
    target["verdict"] = verdict
    target["note"] = str(note or "")
    target["at"] = time.strftime("%Y-%m-%d %H:%M")
    state["done"].append(target)
    state["done"] = state["done"][-200:]
    delta = 0.0
    if verdict == "approve" and target["kind"] in ("采购", "预算", "招聘", "投资"):
        delta = -float(target.get("amount") or 0)
    if verdict == "approve" and target["kind"] == "离职":
        # 离职批了就等于同意清退，钱由 company_live 的 N+1 走
        delta = 0.0
    save(data_dir, state)
    return {
        "ok": True, "doc": target, "verdict": verdict, "cash_delta": round(delta, 2),
        "msg": "%s：%s「%s」%s" % (
            "已批" if verdict == "approve" else "已驳",
            target["from"], target["title"],
            ("，占款 %.0f 万" % abs(delta)) if delta else ""),
    }


# ── 绩效 D：走人 + 补招 ───────────────────────────────────────────────
D_PEOPLE = [
    {"dept": "finance", "name": "王小满", "post": "会计主管", "level": "M1", "salary": 1.6,
     "why": "连续两季绩效 D：结账超期两个月、错账 7 笔"},
    {"dept": "silicon", "name": "苏离", "post": "量产经理", "level": "M2", "salary": 3.2,
     "why": "绩效 D：封测厂排产压错，交期延后两周"},
    {"dept": "hr", "name": "孟小舟", "post": "员工关系专员", "level": "P4", "salary": 1.0,
     "why": "绩效 D：去年一起仲裁漏了关键证据，赔 18 万"},
    {"dept": "cloud", "name": "石见", "post": "客户支持主管", "level": "P6", "salary": 1.3,
     "why": "绩效 D：大客户投诉三次超时未回"},
    {"dept": "solution", "name": "齐国安", "post": "交付经理", "level": "P6", "salary": 1.8,
     "why": "绩效 D：两个项目验收资料不全，被扣 40 万尾款"},
]


def perf_d(data_dir: str = "") -> List[Dict[str, Any]]:
    """绩效 D 名单（已经走掉的会从这里消掉）。"""
    state = load(data_dir)
    gone = {f.get("name") for f in state.get("fired_d") or []}
    rows = []
    for p in D_PEOPLE:
        if p["name"] in gone:
            continue
        row = dict(p)
        row["months"] = 4
        row["severance"] = round(float(p["salary"]) * 4, 2)
        rows.append(row)
    return rows


def fire_perf_d(data_dir: str, name: str = "") -> Dict[str, Any]:
    """绩效 D 直接清退，并自动开出一个补招缺口。"""
    rows = perf_d(data_dir)
    if not rows:
        return {"ok": False, "msg": "现在没有绩效 D 的人"}
    targets = [r for r in rows if not name or name in r["name"]]
    if not targets:
        return {"ok": False, "msg": "名单里没有 %s 的绩效 D 记录" % name}
    state = load(data_dir)
    out = []
    for t in targets:
        state.setdefault("fired_d", []).append({
            "name": t["name"], "dept": t["dept"], "post": t["post"],
            "severance": t["severance"], "at": time.strftime("%Y-%m-%d %H:%M"),
        })
        state.setdefault("gaps", []).append({
            "dept": t["dept"], "post": t["post"], "level": t["level"],
            "salary": str(t["salary"]), "why": "补 %s 的空位（绩效 D 清退）" % t["name"],
            "at": time.strftime("%Y-%m-%d %H:%M"),
        })
        out.append(t)
    save(data_dir, state)
    names = "、".join(t["name"] for t in out)
    money = round(sum(float(t["severance"]) for t in out), 2)
    return {"ok": True, "fired": out, "severance": money,
            "msg": "%s 已按绩效 D 清退，赔偿合计 %.2f 万，补招缺口已开好" % (names, money)}


def gaps(data_dir: str) -> List[Dict[str, Any]]:
    return list(load(data_dir).get("gaps") or [])


def close_gap(data_dir: str, dept: str, post: str = "", person: str = "") -> Dict[str, Any]:
    state = load(data_dir)
    keep = []
    hit = None
    for g in state.get("gaps") or []:
        if not hit and (g.get("dept") == dept or dept in str(g.get("dept"))) and (not post or post in g.get("post", "")):
            hit = dict(g)
            hit["filled_by"] = person or "（新人）"
            hit["filled_at"] = time.strftime("%Y-%m-%d %H:%M")
            state.setdefault("filled", []).append(hit)
            continue
        keep.append(g)
    state["gaps"] = keep
    save(data_dir, state)
    return {"ok": bool(hit), "gap": hit,
            "msg": ("%s 的补招位已经补上" % hit["post"]) if hit else "没有对应的缺口"}



# ── 人事政策：发奖金 or 降本增效 ──────────────────────────────────
POLICIES = [
    {"id": "bonus", "name": "发奖金",
     "line": "把今年的利润切一块出来发下去，人稳住，士气也稳住；账上现金会薄一点。",
     "effect": "现金 -{bonus} 万，士气 +12，离职率下降",
     "kpi": "关键岗留存 ≥95%，主动离职率 ≤5%"},
    {"id": "cut", "name": "降本增效",
     "line": "不裁员，但冻结涨薪、砍差旅与外包，把成本压下来；短期人心会紧。",
     "effect": "月度成本 -{cut} 万，士气 -8，招聘放缓",
     "kpi": "人力成本占比 ≤18%，费用同比 -10%"},
]


def policy(data_dir: str = "") -> Optional[Dict[str, Any]]:
    pid = str(load(data_dir).get("policy") or "")
    for p in POLICIES:
        if p["id"] == pid:
            return p
    return None


def set_policy(data_dir: str, key: str) -> Dict[str, Any]:
    """她只做这个决定：发奖金还是降本增效。钱由本地引擎落账。"""
    key = str(key or "").strip().lower()
    pick = None
    for p in POLICIES:
        if key in (p["id"], p["name"]) or (key and key in p["name"]):
            pick = p
            break
    if not pick:
        return {"ok": False, "msg": "只有两条路：发奖金（bonus）／降本增效（cut）"}
    state = load(data_dir)
    state["policy"] = pick["id"]
    state["policy_at"] = time.strftime("%Y-%m-%d %H:%M")
    save(data_dir, state)
    bonus = 1200.0
    cut = 460.0
    if pick["id"] == "bonus":
        msg = "定了发奖金：奖金池 %.0f 万，从现金里出，士气往上走。" % bonus
    else:
        msg = "定了降本增效：月度成本压 %.0f 万，涨薪冻结、差旅砍半。" % cut
    return {"ok": True, "policy": pick, "msg": msg}


# ── 本地人力部：绩效 D 清退 + 补招，自动跑，不用她管 ─────────────
def hr_sweep(data_dir: str, force: bool = False) -> Dict[str, Any]:
    """人力部每日巡检：清退绩效 D、补齐缺口、按编制补人。

    由本地引擎在每次 brief 时调用（一天只跑一次），不经过模型。
    """
    day = today()
    state = load(data_dir)
    if not force and state.get("hr_last") == day:
        return {"ok": True, "skipped": True, "day": day,
                "summary": state.get("hr_summary") or ""}

    fired, hired = [], []
    # ① 绩效 D 清退（最多一天 2 个，别一次清光）
    rows = perf_d(data_dir)[:2]
    for person in rows:
        r = fire_perf_d(data_dir, person["name"])
        if r.get("ok"):
            fired.extend(r.get("fired") or [])

    # ② 补招：缺口优先，其次在招岗位，一天最多补 3 个
    gaps = gaps_all(data_dir)[:3]
    try:
        import company_live as _cl
    except Exception:
        _cl = None
    for g in gaps:
        cost = 0.0
        try:
            cost = round(float(str(g.get("salary") or "1.5").split("~")[0]) * 1.6, 2)
        except Exception:
            cost = 2.4
        if _cl is not None:
            got = _cl.hire_custom(data_dir, g.get("dept") or "", g.get("post") or "", cost,
                                  "人力部按编制补员")
            if got.get("ok"):
                person = (got.get("hired") or {}).get("name") or ""
                close_gap(data_dir, g.get("dept") or "", g.get("post") or "", person)
                hired.append({"dept": g.get("dept"), "post": g.get("post"),
                              "cost": cost, "name": person})
                continue
        hired.append({"dept": g.get("dept"), "post": g.get("post"), "cost": cost})

    state = load(data_dir)
    summary = []
    if fired:
        summary.append("清退绩效 D %d 人" % len(fired))
    if hired:
        summary.append("补招 %d 人" % len(hired))
    if not summary:
        summary.append("今日无人员变动")
    state["hr_last"] = day
    state["hr_summary"] = "；".join(summary)
    save(data_dir, state)
    return {"ok": True, "day": day, "fired": fired, "hired": hired,
            "summary": state["hr_summary"]}


def gaps_all(data_dir: str) -> List[Dict[str, Any]]:
    return list(load(data_dir).get("gaps") or [])



def judge_docs(data_dir: str, day: str = "") -> list:
    """给今天的待批文件各算一个价值判断（钱不是唯一尺度）。"""
    try:
        import doc_value as _dv
    except Exception:
        try:
            from . import doc_value as _dv  # type: ignore
        except Exception:
            return []
    out = []
    for d in pending(data_dir, day):
        try:
            act, why = _dv.verdict(d)
            sc = _dv.score(d)
        except Exception:
            act, why, sc = "hold", "", {}
        row = dict(d)
        row["suggest"] = act
        row["suggest_why"] = why
        row["value_score"] = sc.get("score")
        row["value_hits"] = sc.get("hits") or []
        out.append(row)
    return out


def brief(data_dir: str) -> Dict[str, Any]:
    """今天要她拍板的事，一段话说清。"""
    docs = generate_day(data_dir)
    hr = hr_sweep(data_dir)
    d = perf_d(data_dir)
    s = strategy(data_dir)
    total = sum(float(x.get("amount") or 0) for x in docs)
    line = "今天要做决定的有 %d 件事，涉及 %.0f 万；" % (len(docs), total)
    line += "人的事归人力部；" + (str(hr.get("summary")) + "；" if hr.get("summary") else "")
    line += ("大方向是「%s」。%s" % (s["name"], s["kpi"])) if s else "大方向还没定，先定一个。"
    pol = policy(data_dir)
    return {"docs": docs, "perf_d": d, "strategy": s, "policy": pol,
            "hr": hr, "gaps": gaps_all(data_dir), "line": line}
