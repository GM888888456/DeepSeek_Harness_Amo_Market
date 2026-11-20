# -*- coding: utf-8 -*-
"""按人格生成服装/首饰目录：款式跟着她走，价格用现实大类基准 + 月初浮动。

不调 LLM：只从人格/世界观里读关键词（JK、汉服、颜色、金银珍珠），
款式用模板组合；价格只是“现实大类基准”，具体指数由 pricing.py 再接。
"""

from __future__ import annotations

import json
import os
import random
import re
import time

MONTH = lambda: time.strftime("%Y-%m")

COLORS = ("白", "粉", "蓝", "黑", "米", "灰", "红", "浅绿", "杏", "紫")
HANFU_DYNASTIES = ("唐制", "宋制", "明制", "魏晋", "汉制")
HANFU_PIECES = {
    "唐制": (("齐胸襦裙", "dress"), ("坦领半臂", "top"), ("齐腰褶裙", "bottom"),
             ("披帛", "accessory"), ("翘头绣履", "shoes")),
    "宋制": (("对襟褙子", "top"), ("百迭裙", "bottom"), ("抹胸长裙", "dress"),
             ("珍珠发夹", "accessory"), ("素缎绣鞋", "shoes")),
    "明制": (("立领斜襟袄", "top"), ("织金马面裙", "bottom"), ("圆领袍", "dress"),
             ("珍珠云肩", "accessory"), ("绣花弓鞋", "shoes")),
    "魏晋": (("交领襦裙", "dress"), ("大袖衫", "top"), ("褶裙", "bottom"),
             ("白玉簪", "accessory"), ("软底布履", "shoes")),
    "汉制": (("曲裾深衣", "dress"), ("直裾深衣", "dress"), ("组玉佩", "accessory"),
             ("翘头履", "shoes")),
}
JK_PIECES = (
    ("水手服上衣", "jk_shirt"), ("长袖白衬衫", "jk_shirt"), ("海军领上衣", "jk_shirt"),
    ("格裙", "jk_skirt"), ("百褶裙", "jk_skirt"),
    ("过膝袜", "socks"), ("中筒袜", "socks"), ("短袜", "socks"),
    ("乐福鞋", "shoes"), ("制服鞋", "shoes"), ("帆布鞋", "shoes"),
    ("领结", "accessory"), ("领带", "accessory"), ("发带", "accessory"),
)
DAILY_PIECES = (
    ("衬衫", "top"), ("针织衫", "top"), ("卫衣", "top"), ("开衫", "top"),
    ("风衣", "top"), ("T恤", "top"), ("牛仔裤", "bottom"), ("半身裙", "bottom"),
    ("阔腿裤", "bottom"), ("直筒裤", "bottom"), ("连衣裙", "dress"),
    ("长裙", "dress"), ("短袜", "socks"), ("帆布鞋", "shoes"),
    ("乐福鞋", "shoes"), ("小挎包", "accessory"), ("发夹", "accessory"),
)
JEWELRY_GROUPS = ("项链", "耳饰", "戒指", "手链", "发饰", "手镯")
JEWELRY_MATERIALS = ("金", "银", "珍珠", "玉", "水晶", "珐琅")

OUTFIT_FILE = "outfits_catalog.json"
JEWELRY_FILE = "jewelry_catalog.json"


COLOR_WORDS = (("白色", "白"), ("粉色", "粉"), ("黑色", "黑"), ("蓝色", "蓝"),
               ("米色", "米"), ("灰色", "灰"), ("红色", "红"), ("浅绿", "绿"),
               ("绿色", "绿"), ("杏色", "杏"), ("紫色", "紫"))


def _palette(text: str) -> tuple[str, ...]:
    """只认「白色/粉色/黑色」这种完整颜色词；不足 3 种就补中性色。"""
    body = str(text or "")
    hits = []
    for word, short in COLOR_WORDS:
        if word in body and short not in hits:
            hits.append(short)
    for short in ("白", "粉", "蓝", "米", "灰"):
        if len(hits) >= 3:
            break
        if short not in hits:
            hits.append(short)
    return tuple(hits[:4]) if hits else ("白", "粉", "蓝", "米")


def _price(base: float, month: str, name: str) -> float:
    """月初 ±5% 的确定性浮动；同一个名字同一个月价格稳定。"""
    chooser = random.Random("amo-price:%s:%s" % (month, name))
    return round(float(base) * chooser.uniform(0.95, 1.05), 2)


def _unique(used: set, name: str, index: int) -> str:
    candidate = name
    if candidate in used:
        candidate = "%s%d" % (name, index)
    while candidate in used:
        index += 1
        candidate = "%s%d" % (name, index)
    used.add(candidate)
    return candidate


def outfit_catalog(persona_text: str = "", city: str = "", month: str = "",
                   total: int = 150) -> list[dict]:
    """按人格生成 150 件服装；喜欢 JK/汉服就多给，颜色优先用她喜欢的。"""
    month = month or MONTH()
    text = "%s %s" % (str(persona_text or ""), str(city or ""))
    low = text.lower()
    likes_jk = any(word in low for word in ("jk", "制服", "学生", "水手", "格裙"))
    likes_hanfu = any(word in low for word in ("汉服", "古风", "襦裙", "马面", "褙子", "曲裾"))
    if likes_jk and not likes_hanfu:
        counts = {"JK": 70, "汉服": 50, "日常": 30}
    elif likes_hanfu and not likes_jk:
        counts = {"JK": 50, "汉服": 70, "日常": 30}
    else:
        counts = {"JK": 50, "汉服": 50, "日常": 50}
    palette = _palette(text)
    rows, used = [], set()

    def add(name: str, slot: str, category: str, base: float) -> None:
        name = _unique(used, name, len(rows) + 1)
        rows.append({"name": name, "slot": slot, "style": category, "kind": "服装",
                     "price": _price(base, month, name)})

    for index in range(counts["汉服"]):
        dynasty = HANFU_DYNASTIES[index % len(HANFU_DYNASTIES)]
        piece, slot = HANFU_PIECES[dynasty][index % len(HANFU_PIECES[dynasty])]
        color = palette[index % len(palette)]
        base = {"dress": 320, "top": 180, "bottom": 220,
                "accessory": 60, "shoes": 120}.get(slot, 150)
        add("汉服·%s%s%s" % (dynasty, color, piece), slot, "汉服", base)

    for index in range(counts["JK"]):
        piece, slot = JK_PIECES[index % len(JK_PIECES)]
        color = palette[index % len(palette)]
        base = {"jk_shirt": 120, "jk_skirt": 110, "socks": 25,
                "shoes": 140, "accessory": 30}.get(slot, 100)
        add("JK·%s%s" % (color, piece), slot, "JK", base)

    for index in range(counts["日常"]):
        piece, slot = DAILY_PIECES[index % len(DAILY_PIECES)]
        color = palette[index % len(palette)]
        base = {"top": 90, "bottom": 110, "dress": 160,
                "socks": 20, "shoes": 120, "accessory": 50}.get(slot, 100)
        add("%s%s" % (color, piece), slot, "日常", base)

    return rows[:max(1, int(total))]


def jewelry_catalog(persona_text: str = "", month: str = "", total: int = 126) -> list[dict]:
    """首饰：人格写了金银珍珠/玉就优先用；没写就随机材质+颜色。"""
    month = month or MONTH()
    text = str(persona_text or "")
    materials = [m for m in JEWELRY_MATERIALS if m in text] or list(JEWELRY_MATERIALS)
    palette = _palette(text)
    rows, used = [], set()
    for index in range(max(1, int(total))):
        group = JEWELRY_GROUPS[index % len(JEWELRY_GROUPS)]
        material = materials[index % len(materials)]
        color = palette[index % len(palette)]
        name = "%s%s%s" % (color, material, group[:-1] if group.endswith("饰") else group)
        if group == "项链":
            name = "%s%s项链" % (color, material)
        elif group == "耳饰":
            name = "%s%s耳饰" % (color, material)
        elif group == "戒指":
            name = "%s%s戒指" % (color, material)
        elif group == "手链":
            name = "%s%s手链" % (color, material)
        elif group == "发饰":
            name = "%s%s发夹" % (color, material)
        elif group == "手镯":
            name = "%s%s手镯" % (color, material)
        name = _unique(used, name, index + 1)
        base = 29 + (index % 12) * 40
        rows.append({"name": name, "group": group, "style": group,
                     "kind": "首饰", "price": _price(base, month, name)})
    return rows


def _path(data_dir: str, name: str) -> str:
    return os.path.join(str(data_dir or "."), name)


def _load(path: str, month: str) -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return []
    if not isinstance(data, dict) or data.get("month") != month:
        return []
    rows = data.get("items")
    return rows if isinstance(rows, list) else []


def _save(path: str, month: str, rows: list[dict]) -> None:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump({"month": month, "items": rows}, handle, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass


def ensure_catalog(data_dir: str, kind: str, persona_text: str = "",
                   city: str = "", month: str = "") -> list[dict]:
    """读取本月目录；没有就按人格生成并落盘。kind=outfits/jewelry。"""
    month = month or MONTH()
    if kind == "outfits":
        path = _path(data_dir, OUTFIT_FILE)
        rows = _load(path, month)
        if rows and len(rows) >= 120:
            return rows
        rows = outfit_catalog(persona_text, city, month)
        _save(path, month, rows)
        return rows
    if kind == "jewelry":
        path = _path(data_dir, JEWELRY_FILE)
        rows = _load(path, month)
        if rows and len(rows) >= 120:
            return rows
        rows = jewelry_catalog(persona_text, month)
        _save(path, month, rows)
        return rows
    return []
