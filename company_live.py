# -*- coding: utf-8 -*-
"""中国计算智脑集团 · 实时状态层（在 company.py 的静态架构上叠一层可变的经营动作）。

company.py 是不可改的底稿（部门、名册、在招岗位、月度报表）；
这里记录玩家/她做过的动作：开除了谁、招进了谁、现金怎么变。

状态落在 plugin_data/<插件>/company_state.json：
    {"fired": [{"dept","name","post","severance","at"}],
     "hired": [{"dept","post","salary","cost","at","name"}],
     "cash_delta": -6.4,
     "log": ["2026-11-25 22:40 开除 财务中心/王小满，赔偿 6.4 万", ...]}
"""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any, Dict, List, Optional

try:
    import company as base  # 同目录
except Exception:  # 被按文件路径加载时兜底
    import importlib.util as _ilu
    import os as _os
    _path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "company.py")
    _spec = _ilu.spec_from_file_location("amo_company_for_live", _path)
    base = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(base)  # type: ignore[union-attr]

STATE_NAME = "company_state.json"

SURNAMES = ("周", "吴", "郑", "冯", "陈", "褚", "卫", "蒋", "沈", "韩", "杨", "朱",
            "秦", "尤", "许", "何", "吕", "施", "张", "孔", "曹", "严", "华", "金")
GIVEN = ("嘉言", "亦舟", "致远", "书宁", "知行", "清和", "问渠", "长风", "若谷", "时雨",
         "南星", "景明", "令仪", "予怀", "怀瑾", "明夷", "见山", "临川")


def _path(data_dir: str) -> str:
    return os.path.join(str(data_dir or "."), STATE_NAME)


def load(data_dir: str) -> Dict[str, Any]:
    path = _path(data_dir)
    try:
        with open(path, encoding="utf-8") as stream:
            state = json.load(stream)
        if not isinstance(state, dict):
            raise ValueError("bad state")
    except Exception:
        state = {}
    state.setdefault("fired", [])
    state.setdefault("hired", [])
    state.setdefault("cash_delta", 0.0)
    state.setdefault("log", [])
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


def _log(state: Dict[str, Any], line: str) -> None:
    state["log"].append("%s %s" % (time.strftime("%Y-%m-%d %H:%M"), line))
    state["log"] = state["log"][-120:]


def _random_name(state: Dict[str, Any]) -> str:
    used = {m.get("name") for m in state.get("hired", [])}
    for _ in range(40):
        name = random.choice(SURNAMES) + random.choice(GIVEN)
        if name not in used:
            return name
    return "新同事%02d" % (len(state.get("hired", [])) + 1)


def fire(data_dir: str, dept_key: str, name: str) -> Dict[str, Any]:
    """开除一个人：能动的才让动，赔偿从账上走。"""
    state = load(data_dir)
    already = {f.get("name") for f in state["fired"]}
    if name in already:
        return {"ok": False, "msg": "%s 已经走了" % name}
    result = base.fire(dept_key, name)
    if not result.get("ok"):
        # 底稿说不能动 → 拒绝
        return result
    item = {
        "dept": result["dept"], "name": result["name"], "post": result.get("post", ""),
        "severance": float(result.get("severance") or 0),
        "at": time.strftime("%Y-%m-%d %H:%M"),
    }
    state["fired"].append(item)
    state["cash_delta"] = round(float(state.get("cash_delta") or 0) - item["severance"], 2)
    _log(state, "开除 %s／%s（%s），赔偿 %.2f 万" % (item["dept"], item["name"], item.get("post", ""), item["severance"]))
    save(data_dir, state)
    return {"ok": True, "fired": item, "cash_delta": state["cash_delta"],
            "msg": "%s 已办完离职，赔偿 %.2f 万" % (item["name"], item["severance"])}


def hire(data_dir: str, dept_key: str, post: str = "") -> Dict[str, Any]:
    """招一个人：扣首月成本，编制补上。"""
    state = load(data_dir)
    plan = base.hire(dept_key, post)
    if not plan.get("ok"):
        return plan
    person = _random_name(state)
    item = {
        "dept": plan["dept"], "post": plan["post"], "salary": plan["salary"],
        "cost": float(plan.get("cost_first_month") or 0), "name": person,
        "at": time.strftime("%Y-%m-%d %H:%M"),
    }
    state["hired"].append(item)
    state["cash_delta"] = round(float(state.get("cash_delta") or 0) - item["cost"], 2)
    _log(state, "招 %s 进 %s 做 %s（%s），首月成本 %.2f 万" % (person, item["dept"], item["post"], item["salary"], item["cost"]))
    save(data_dir, state)
    return {"ok": True, "hired": item, "cash_delta": state["cash_delta"],
            "msg": "%s 接了 offer，%s 到岗" % (person, plan.get("onboard_after") or "一个月内")}


def adjust_cash(data_dir: str, delta: float, reason: str = "") -> Dict[str, Any]:
    """按动作调现金（批预算、赔偿、首月成本都走这里）。"""
    state = load(data_dir)
    state["cash_delta"] = round(float(state.get("cash_delta") or 0) + float(delta or 0), 2)
    if reason:
        _log(state, reason)
    save(data_dir, state)
    return {"cash_delta": state["cash_delta"]}


def fire_forced(data_dir: str, dept_key: str, name: str, post: str = "",
                severance: float = 0.0, reason: str = "") -> Dict[str, Any]:
    """绩效 D 那种「不管你底稿怎么说都得走」的清退。"""
    state = load(data_dir)
    if name in {f.get("name") for f in state["fired"]}:
        return {"ok": False, "msg": "%s 已经走了" % name}
    dept_name = dept_key
    try:
        for d in base.departments():
            if dept_key in (d["id"], d["name"], d["short"]):
                dept_name = d["name"]
                break
    except Exception:
        pass
    item = {"dept": dept_name, "name": name, "post": post,
            "severance": float(severance or 0), "at": time.strftime("%Y-%m-%d %H:%M")}
    state["fired"].append(item)
    state["cash_delta"] = round(float(state.get("cash_delta") or 0) - item["severance"], 2)
    _log(state, "绩效 D 清退 %s／%s（%s），赔偿 %.2f 万%s"
         % (dept_name, name, post, item["severance"], ("｜" + reason) if reason else ""))
    save(data_dir, state)
    return {"ok": True, "fired": item, "cash_delta": state["cash_delta"]}


def hire_custom(data_dir: str, dept_key: str, post: str, cost: float = 0.0,
                reason: str = "") -> Dict[str, Any]:
    """按缺口补一个人（岗位不一定在在招表里）。"""
    state = load(data_dir)
    dept_name = dept_key
    try:
        for d in base.departments():
            if dept_key in (d["id"], d["name"], d["short"]):
                dept_name = d["name"]
                break
    except Exception:
        pass
    person = _random_name(state)
    item = {"dept": dept_name, "post": post, "salary": "—",
            "cost": float(cost or 0), "name": person,
            "at": time.strftime("%Y-%m-%d %H:%M")}
    state["hired"].append(item)
    state["cash_delta"] = round(float(state.get("cash_delta") or 0) - item["cost"], 2)
    _log(state, "补招 %s 进 %s 做 %s，首月成本 %.2f 万%s"
         % (person, dept_name, post, item["cost"], ("｜" + reason) if reason else ""))
    save(data_dir, state)
    return {"ok": True, "hired": item, "cash_delta": state["cash_delta"]}


def reset(data_dir: str) -> Dict[str, Any]:
    state = {"fired": [], "hired": [], "cash_delta": 0.0, "log": []}
    save(data_dir, state)
    return {"ok": True, "msg": "人员的进出记录清空了"}


def departments(data_dir: str) -> List[Dict[str, Any]]:
    """名册叠加：开除的人从名单里消失，招来的人加进去。"""
    state = load(data_dir)
    fired = {f.get("name") for f in state["fired"]}
    out = []
    for d in base.departments():
        row = dict(d)
        row["staff"] = [s for s in d["staff"] if s["name"] not in fired]
        for h in state["hired"]:
            if h.get("dept") == d["name"]:
                row["staff"].append({
                    "name": h.get("name"), "post": h.get("post"), "level": "新人",
                    "since": (h.get("at") or "")[:7], "salary": 0.0, "perf": "—",
                    "fire_note": "刚招进来的，先看着办",
                })
        row["onboard"] = max(0, int(d["onboard"]) - sum(1 for f in state["fired"] if f.get("dept") == d["name"])
                             + sum(1 for h in state["hired"] if h.get("dept") == d["name"]))
        out.append(row)
    return out


def fireable(data_dir: str) -> List[Dict[str, Any]]:
    """可动的名单（叠过离职/入职之后）。"""
    rows: List[Dict[str, Any]] = []
    for d in departments(data_dir):
        for s in d["staff"]:
            note = str(s.get("fire_note") or "")
            if not note.startswith(("可以", "能用")):
                continue
            try:
                since = int(str(s.get("since", "2020"))[:4])
            except Exception:
                since = 2020
            months = max(1, 2026 - since) + 1
            rows.append({
                "dept": d["name"], "dept_id": d["id"], "name": s["name"],
                "post": s.get("post", ""), "level": s.get("level", ""),
                "salary": s.get("salary", 0), "perf": s.get("perf", ""),
                "why": note, "severance": round(float(s.get("salary") or 0) * months, 2),
            })
    return rows


def recruit_plan(data_dir: str) -> List[Dict[str, Any]]:
    """在招岗位：招进一个人就少一个名额，招满了就不列。"""
    state = load(data_dir)
    taken: Dict[str, int] = {}
    for h in state.get("hired") or []:
        key = "%s|%s" % (h.get("dept"), h.get("post"))
        taken[key] = taken.get(key, 0) + 1
    idmap = {d["name"]: d["id"] for d in base.departments()}
    rows = []
    for row in base.recruit_plan():
        item = dict(row)
        key = "%s|%s" % (item.get("dept"), item.get("post"))
        left = int(item.get("need") or 1) - taken.get(key, 0)
        if left <= 0:
            continue
        item["need"] = left
        item["dept_id"] = idmap.get(item.get("dept"), "")
        rows.append(item)
    return rows


def report(data_dir: str) -> Dict[str, Any]:
    state = load(data_dir)
    row = base.report()
    delta = float(state.get("cash_delta") or 0)
    row["cash"] = round(float(row["cash"]) + delta, 2)
    row["cash_delta"] = round(delta, 2)
    row["fired_count"] = len(state.get("fired") or [])
    row["hired_count"] = len(state.get("hired") or [])
    row["headcount"] = int(row["headcount"]) - row["fired_count"] + row["hired_count"]
    row["onboard"] = max(0, int(row["onboard"]) - row["fired_count"] + row["hired_count"])
    row["vacancy"] = max(0, int(row["headcount"]) - int(row["onboard"]))
    # 人少了，人力成本按比例落一点
    if row["fired_count"] or row["hired_count"]:
        row["cost"]["人力"] = round(float(row["cost"]["人力"])
                                 - sum(float(f.get("severance") or 0) for f in state["fired"]) / 12.0
                                 + sum(float(h.get("cost") or 0) for h in state["hired"]), 2)
    return row


def timeline(data_dir: str) -> List[str]:
    return list(reversed(load(data_dir).get("log") or []))


# ---------------------------------------------------------------------------
# 真正经营层：客户 / 合同 / 发票 / 回款 / 供应商 / 项目 / 日结
# ---------------------------------------------------------------------------

def _ensure_ops(state):
    state.setdefault("customers", [])
    state.setdefault("contracts", [])
    state.setdefault("invoices", [])
    state.setdefault("projects", [])
    state.setdefault("suppliers", [])
    state.setdefault("operating_cash", 0.0)
    state.setdefault("receivable", 0.0)
    state.setdefault("payable", 0.0)
    state.setdefault("kpi", {})
    return state

def _op_id(prefix):
    return "%s-%d" % (prefix, int(time.time() * 1000))

def add_customer(data_dir: str, name: str, sector: str = "政企",
                credit: float = 0.0) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    name = str(name or "").strip()
    if not name:
        return {"ok": False, "reason": "客户名称不能为空"}
    if any(str(x.get("name")) == name for x in state["customers"]):
        return {"ok": False, "reason": "客户已经存在"}
    row = {"id": _op_id("CUS"), "name": name, "sector": sector or "政企",
           "credit": round(float(credit or 0), 2), "status": "active", "created_at": _now()}
    state["customers"].append(row)
    _log(state, "新增客户 %s（%s）" % (name, row["sector"]))
    save(data_dir, state)
    return {"ok": True, "customer": row}

def create_contract(data_dir: str, customer: str, title: str, amount: float,
                    gross_margin: float = 0.35, cycle_days: int = 90) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    amount = round(float(amount or 0), 2)
    if amount <= 0: return {"ok": False, "reason": "合同金额必须大于 0"}
    customer = str(customer or "").strip() or "未命名客户"
    row = {"id": _op_id("CTR"), "customer": customer, "title": str(title or "项目合同"),
           "amount": amount, "gross_margin": max(0.0, min(0.95, float(gross_margin or 0.35))),
           "cost_estimate": round(amount * (1 - max(0.0, min(0.95, float(gross_margin or 0.35)))), 2),
           "received": 0.0, "status": "signed", "signed_at": _now(),
           "due_at": time.strftime("%Y-%m-%d", time.localtime(time.time() + max(1, int(cycle_days or 90))*86400))}
    state["contracts"].append(row)
    state["receivable"] = round(float(state.get("receivable") or 0) + amount, 2)
    state["operating_cash"] = round(float(state.get("operating_cash") or 0) - row["cost_estimate"] * 0.10, 2)
    _log(state, "签约 %s／%s，合同 %.2f 万" % (customer, row["title"], amount))
    save(data_dir, state)
    return {"ok": True, "contract": row, "operating_cash": state["operating_cash"]}

def invoice(data_dir: str, contract_id: str, amount: float = 0.0) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    for contract in state["contracts"]:
        if contract.get("id") == contract_id:
            remaining = max(0.0, float(contract["amount"]) - float(contract.get("received") or 0))
            amount = round(min(remaining, float(amount or remaining)), 2)
            if amount <= 0: return {"ok": False, "reason": "没有可开票金额"}
            row = {"id": _op_id("INV"), "contract": contract_id, "customer": contract["customer"],
                   "amount": amount, "status": "issued", "issued_at": _now()}
            state["invoices"].append(row)
            _log(state, "开票 %s，金额 %.2f 万" % (contract["customer"], amount))
            save(data_dir, state)
            return {"ok": True, "invoice": row}
    return {"ok": False, "reason": "没有这份合同"}

def receive(data_dir: str, contract_id: str, amount: float) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    amount = round(float(amount or 0), 2)
    if amount <= 0: return {"ok": False, "reason": "回款必须大于 0"}
    for contract in state["contracts"]:
        if contract.get("id") == contract_id:
            remaining = max(0.0, float(contract["amount"]) - float(contract.get("received") or 0))
            got = min(amount, remaining)
            contract["received"] = round(float(contract.get("received") or 0) + got, 2)
            state["receivable"] = max(0.0, round(float(state.get("receivable") or 0) - got, 2))
            state["operating_cash"] = round(float(state.get("operating_cash") or 0) + got, 2)
            if contract["received"] >= contract["amount"] - 0.01: contract["status"] = "paid"
            _log(state, "客户回款 %s %.2f 万" % (contract["customer"], got))
            save(data_dir, state)
            return {"ok": True, "contract": dict(contract), "received": got,
                    "operating_cash": state["operating_cash"]}
    return {"ok": False, "reason": "没有这份合同"}

def project(data_dir: str, name: str, department: str = "方案部",
            budget: float = 0.0, progress: float = 0.0) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    row = {"id": _op_id("PRJ"), "name": str(name or "未命名项目"),
           "department": department or "方案部", "budget": round(float(budget or 0), 2),
           "spent": 0.0, "progress": max(0.0, min(1.0, float(progress or 0))),
           "status": "running", "created_at": _now()}
    state["projects"].append(row)
    _log(state, "启动项目 %s，预算 %.2f 万" % (row["name"], row["budget"]))
    save(data_dir, state)
    return {"ok": True, "project": row}

def spend(data_dir: str, amount: float, reason: str = "经营支出") -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    amount = round(float(amount or 0), 2)
    if amount <= 0: return {"ok": False, "reason": "支出必须大于 0"}
    state["operating_cash"] = round(float(state.get("operating_cash") or 0) - amount, 2)
    state["payable"] = round(float(state.get("payable") or 0) + amount, 2)
    _log(state, "经营支出 %.2f 万：%s" % (amount, reason))
    save(data_dir, state)
    return {"ok": True, "amount": amount, "operating_cash": state["operating_cash"]}

def tick(data_dir: str) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    today = time.strftime("%Y-%m-%d")
    last = str(state.get("ops_last_tick") or "")
    if last == today:
        return snapshot(data_dir)
    state["ops_last_tick"] = today
    for p in state["projects"]:
        if p.get("status") == "running":
            p["progress"] = min(1.0, round(float(p.get("progress") or 0) + 0.08, 2))
            if p["progress"] >= 1.0: p["status"] = "delivered"
    _log(state, "经营日结：项目推进，回款/应收 %.2f 万" % float(state.get("receivable") or 0))
    save(data_dir, state)
    return snapshot(data_dir)

def snapshot(data_dir: str) -> Dict[str, Any]:
    state = _ensure_ops(load(data_dir))
    active = [x for x in state["contracts"] if x.get("status") != "paid"]
    running = [x for x in state["projects"] if x.get("status") == "running"]
    return {
        "customers": len(state["customers"]), "contracts": len(state["contracts"]),
        "active_contracts": len(active), "receivable": round(float(state["receivable"] or 0), 2),
        "operating_cash": round(float(state["operating_cash"] or 0), 2),
        "projects_running": len(running), "projects": list(state["projects"][-20:]),
        "contracts": list(state["contracts"][-20:]), "invoices": list(state["invoices"][-20:]),
        "customers_live": list(state["customers"][-20:]), "events": list(state.get("log") or [])[-20:],
    }
