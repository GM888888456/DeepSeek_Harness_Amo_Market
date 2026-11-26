# -*- coding: utf-8 -*-
"""真实世界枢纽（The Real-World Nexus）：把「现实里的钱」收成一份统一数据。

五个版块：

| 版块 | 内容 | 价格从哪来 |
|---|---|---|
| 餐饮与生鲜 | 菜市场 / 外卖 / 堂食 | 新发地公开菜价 + 城市系数 + 配送费 |
| 医疗与健康 | 药房 | 医保指导价指数 + 季节系数 |
| 服饰与美妆 | 服装 / 首饰 / 美妆 | 电商均价 + 金价 + 大促 |
| 出行与住宿 | 车票 / 酒店 | 城市坐标算里程，按高铁/自驾/飞机计价；酒店按城市档位 |
| 娱乐与生活 | 会员订阅 / 景区门票 | 真实月费与 4A/5A 门票区间 |

只提供数据，不判断买不买：查价、开票、扣款都在终端和金融账本里。
所有价格都是**估算**，对外标注 `estimated`，不假装是实时挂牌价。
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from datetime import datetime

_FILE = "geo_cities.json"
_cities = None

#: 城市档位：酒店、门票、车票的服务费都乘这个系数。缺省按二线 1.0。
CITY_TIER = {
    "一线": 1.38, "新一线": 1.15, "二线": 1.0, "三线": 0.88, "四线": 0.8,
}
CITY_LEVEL = {}
for _names, _level in (
    (("北京", "上海", "广州", "深圳"), "一线"),
    (("成都", "杭州", "重庆", "西安", "苏州", "武汉", "南京", "天津", "郑州", "长沙",
      "东莞", "佛山", "宁波", "青岛", "沈阳", "合肥", "昆明"), "新一线"),
    (("贵阳", "南宁", "福州", "厦门", "济南", "哈尔滨", "长春", "大连", "太原", "石家庄",
      "南昌", "温州", "台州", "无锡", "常州", "徐州", "烟台", "泉州", "珠海", "中山",
      "惠州", "海口", "兰州", "乌鲁木齐", "呼和浩特", "银川", "西宁", "拉萨"), "二线"),
    (("遵义", "安顺", "六盘水", "毕节", "铜仁", "凯里", "都匀", "兴义", "柳州", "桂林",
      "北海", "九江", "赣州", "宜昌", "襄阳", "洛阳", "开封", "临沂", "潍坊", "唐山",
      "保定", "包头", "鄂尔多斯", "大理", "丽江", "张家界", "黄山"), "三线"),
):
    for _name in _names:
        CITY_LEVEL[_name] = _level

#: 酒店三档：品牌只是「参考档次」，价格按区间 × 城市系数，不写死某家店的房价。
HOTEL_TIERS = (
    {"id": "budget", "name": "快捷酒店", "brands": ("如家", "汉庭", "7天", "锦江之星"),
     "low": 150.0, "high": 268.0, "note": "干净能睡，隔音一般"},
    {"id": "comfort", "name": "中档酒店", "brands": ("亚朵", "全季", "桔子水晶", "维也纳"),
     "low": 320.0, "high": 528.0, "note": "床舒服、有早餐，出差常住"},
    {"id": "luxury", "name": "高档酒店", "brands": ("凯宾斯基", "万豪", "希尔顿", "洲际"),
     "low": 820.0, "high": 1680.0, "note": "大堂香氛、行政酒廊，贵得有理"},
)

ROOM_TYPES = ("大床房", "双床房", "高级大床房", "行政大床房", "家庭房")
ROOM_FACTOR = {"大床房": 1.0, "双床房": 1.06, "高级大床房": 1.24,
               "行政大床房": 1.58, "家庭房": 1.42}
#: 地段：同一家连锁在不同位置房价不一样，也让「120 家」不是同一家刷屏。
HOTEL_AREAS = {"市中心": 1.12, "火车站": 0.94, "机场路": 1.0,
               "老城区": 0.92, "新区": 1.05, "景区旁": 1.18}
PAGE_SIZE = 120
#: 数据结构/生成规则变了就 +1：旧缓存会被丢弃重建。
DATA_VERSION = 9

#: 数字订阅：真实月费的量级（按人民币，不含首月优惠）。
SUBSCRIPTIONS = (
    {"id": "video", "name": "视频会员", "price": 25.0, "note": "追番、看剧"},
    {"id": "music", "name": "音乐会员", "price": 15.0, "note": "听歌、下载"},
    {"id": "cloud", "name": "云盘会员", "price": 10.0, "note": "存照片和文件"},
    {"id": "novel", "name": "小说会员", "price": 12.0, "note": "看连载"},
)

#: 景区门票：先认这张「现实里查得到」的表，查不到按等级给区间。
ATTRACTIONS = {
    "黔灵山公园": ("贵阳", "4A", 5.0),
    "青岩古镇": ("贵阳", "5A", 60.0),
    "甲秀楼": ("贵阳", "3A", 0.0),
    "花溪公园": ("贵阳", "4A", 6.0),
    "天河潭": ("贵阳", "4A", 50.0),
    "黄果树瀑布": ("安顺", "5A", 180.0),
    "西江千户苗寨": ("黔东南", "4A", 90.0),
    "荔波小七孔": ("黔南", "5A", 130.0),
    "梵净山": ("铜仁", "5A", 110.0),
    "镇远古镇": ("黔东南", "5A", 60.0),
    "故宫博物院": ("北京", "5A", 60.0),
    "八达岭长城": ("北京", "5A", 40.0),
    "颐和园": ("北京", "5A", 30.0),
    "外滩": ("上海", "5A", 0.0),
    "上海迪士尼": ("上海", "5A", 475.0),
    "西湖": ("杭州", "5A", 0.0),
    "灵隐寺": ("杭州", "5A", 45.0),
    "乌镇": ("嘉兴", "5A", 150.0),
    "拙政园": ("苏州", "5A", 70.0),
    "黄山风景区": ("黄山", "5A", 190.0),
    "张家界国家森林公园": ("张家界", "5A", 228.0),
    "凤凰古城": ("湘西", "4A", 0.0),
    "丽江古城": ("丽江", "5A", 50.0),
    "玉龙雪山": ("丽江", "5A", 100.0),
    "大理古城": ("大理", "4A", 0.0),
    "鼓浪屿": ("厦门", "5A", 100.0),
    "武夷山": ("南平", "5A", 140.0),
    "泰山": ("泰安", "5A", 115.0),
    "峨眉山": ("乐山", "5A", 160.0),
    "九寨沟": ("阿坝", "5A", 190.0),
    "都江堰": ("成都", "5A", 80.0),
    "兵马俑": ("西安", "5A", 120.0),
    "敦煌莫高窟": ("敦煌", "5A", 238.0),
}
LEVEL_PRICE = {"5A": (90.0, 180.0), "4A": (45.0, 90.0), "3A": (20.0, 45.0), "免费": (0.0, 0.0)}

#: 车票计价：每公里单价（元），已含常见服务费；实际票价会随车次浮动。
FARE_PER_KM = {"drive": 0.62, "train": 0.46, "flight": 0.68}
SPEED = {"drive": 80.0, "train": 210.0, "flight": 620.0}
OVERHEAD_MIN = {"drive": 15, "train": 45, "flight": 110}


def _load_cities() -> dict:
    global _cities
    if _cities is not None:
        return _cities
    data = {}
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _FILE)
        with open(path, encoding="utf-8") as stream:
            raw = json.load(stream) or {}
        for name, value in raw.items():
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                try:
                    data[str(name)] = (float(value[0]), float(value[1]))
                except (TypeError, ValueError):
                    continue
    except Exception:
        data = {}
    _cities = data
    return data


def city_coords(city: str) -> tuple:
    """城市 → (lat, lng) 或 (0, 0)。只认精确名和最长包含匹配，不猜。"""
    name = str(city or "").strip()
    if not name:
        return 0.0, 0.0
    table = _load_cities()
    if name in table:
        return table[name]
    for suffix in ("特别行政区", "自治区", "自治州", "地区", "新区", "市", "盟", "县", "区"):
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
            break
    if name in table:
        return table[name]
    best, coords = "", (0.0, 0.0)
    for key, value in table.items():
        if key and key in name and len(key) > len(best):
            best, coords = key, value
    return coords


def haversine(a, b) -> float:
    try:
        lat1, lng1 = float(a[0]), float(a[1])
        lat2, lng2 = float(b[0]), float(b[1])
    except (TypeError, ValueError, IndexError):
        return 0.0
    if not (lat1 or lng1) or not (lat2 or lng2):
        return 0.0
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return round(2 * radius * math.asin(min(1.0, math.sqrt(h))), 1)


def city_factor(city: str) -> tuple:
    """城市消费系数 + 档位名。查不到按二线 1.0，不编。"""
    name = str(city or "").strip()
    if name.endswith("市") and len(name) > 1:
        name = name[:-1]
    level = CITY_LEVEL.get(name, "")
    if not level:
        return 1.0, "二线（默认）"
    return CITY_TIER.get(level, 1.0), level


def _weekend_factor(now: datetime = None) -> float:
    now = now or datetime.now()
    return 1.15 if now.weekday() in (4, 5) else 1.0


def _strip_city(name: str) -> str:
    """「安顺市 / 安顺地区 / 安顺」视为同一座城。"""
    value = str(name or "").strip()
    for suffix in ("特别行政区", "自治区", "自治州", "地区", "新区", "市", "盟", "县", "区"):
        if value.endswith(suffix) and len(value) > len(suffix):
            return value[: -len(suffix)]
    return value


def _round_price(value: float) -> float:
    """票价取整到 0.5 元，酒店取整到 5 元——像人报的价。"""
    value = max(0.0, float(value or 0))
    return round(value * 2) / 2.0


def hotel_options(city: str = "", now: datetime = None, limit: int = PAGE_SIZE) -> list[dict]:
    """本地 120 家酒店：三档 × 品牌 × 房型 × 地段，价格 = 档位区间 × 城市系数 × 周末。

    同一档里名字、价位、地段都不同，她（和终端）能真的挑一家，而不是只知道「中档 424」。
    """
    factor, level = city_factor(city)
    weekend = _weekend_factor(now)
    rows = []
    per_tier = max(1, int(limit) // max(1, len(HOTEL_TIERS)))
    for tier in HOTEL_TIERS:
        mid = (tier["low"] + tier["high"]) / 2.0
        combos = []
        for brand in tier["brands"]:
            for room in ROOM_TYPES:
                for area, area_factor in HOTEL_AREAS.items():
                    combos.append((brand, room, area, area_factor))
        for brand, room, area, area_factor in combos[:per_tier]:
            price = mid * factor * weekend * ROOM_FACTOR.get(room, 1.0) * area_factor
            rows.append({
                "kind": "hotel", "tier": tier["id"], "tier_name": tier["name"],
                "name": "%s·%s（%s）" % (brand, room, area), "brand": brand,
                "room": room, "area": area,
                "city": str(city or ""), "city_level": level,
                "price": _round_price(price),
                "price_low": _round_price(tier["low"] * factor * weekend
                                          * ROOM_FACTOR.get(room, 1.0) * area_factor),
                "price_high": _round_price(tier["high"] * factor * weekend
                                           * ROOM_FACTOR.get(room, 1.0) * area_factor),
                "unit": "晚", "note": tier["note"], "estimated": True,
                "source": "city_tier",
            })
    return rows[:max(1, int(limit))]


def pick_hotel(city: str = "", budget: float = 0.0, now: datetime = None) -> dict:
    """按余额挑一档，再从这一档的房里挑一家（同一天同一个结果）。"""
    rows = hotel_options(city, now)
    if not rows:
        return {}
    try:
        budget = float(budget or 0)
    except (TypeError, ValueError):
        budget = 0.0
    if budget >= 20000:
        want = "luxury"
    elif budget >= 5000:
        want = "comfort"
    else:
        want = "budget"
    pool = [row for row in rows if row["tier"] == want] or rows
    chooser = random.Random("amo-hotel:%s:%s" % (city, (now or datetime.now()).date()))
    return chooser.choice(pool)


def ticket_quote(from_city: str, to_city: str, now: datetime = None) -> dict:
    """两地之间：里程、方式、耗时、票价区间。"""
    a = city_coords(from_city)
    b = city_coords(to_city)
    km = haversine(a, b)
    if not km:
        return {"ok": False, "reason": "认不出这两个城市", "from": str(from_city or ""),
                "to": str(to_city or ""), "estimated": True}
    if km <= 30:
        mode = "drive"
    elif km <= 1200:
        mode = "train"
    else:
        mode = "flight"
    factor, level = city_factor(to_city or from_city)
    speed = SPEED.get(mode, 200.0)
    minutes = int(km / speed * 60) + OVERHEAD_MIN.get(mode, 30)
    # 票价不按城市档位放大（同一段高铁不会因为终点是一线就贵一倍），
    # 只让城市档位轻微影响 10% 以内，其余按里程公式。
    mild = 1.0 + (factor - 1.0) * 0.2
    if mode == "train":
        price = max(35.0, km * FARE_PER_KM["train"] * mild)
        low, high = price * 0.9, price * 1.15
    elif mode == "flight":
        price = max(380.0, (320.0 + km * 0.45) * mild)
        low, high = price * 0.7, price * 1.0
    else:
        price = max(20.0, km * FARE_PER_KM["drive"] * mild + km * 0.08)
        low, high = price * 0.85, price * 1.15
    low = _round_price(low)
    high = _round_price(high)
    if mode == "flight" and now is not None and now.weekday() in (4, 6):
        low, high = _round_price(low * 1.1), _round_price(high * 1.1)
    label = {"drive": "开车/大巴", "train": "高铁", "flight": "飞机"}[mode]
    return {
        "ok": True, "from": str(from_city or ""), "to": str(to_city or ""),
        "km": km, "mode": mode, "mode_name": label,
        "minutes": minutes, "price": _round_price((low + high) / 2),
        "price_low": low, "price_high": high,
        "city_level": level, "estimated": True, "source": "distance_formula",
        "text": "%s→%s 约 %d 公里，%s约 %d 小时 %d 分，票价约 %s～%s 元" % (
            from_city, to_city, int(km), label, minutes // 60, minutes % 60,
            ("%g" % low), ("%g" % high)),
    }


def attraction(name: str, level: str = "", city: str = "") -> dict:
    """景区门票：表里有的按表，没有的按等级给区间。"""
    key = str(name or "").strip()
    row = ATTRACTIONS.get(key)
    if row:
        city_name, lv, price = row
        return {"kind": "attraction", "name": key, "city": city_name or city, "level": lv,
                "price": float(price), "unit": "人", "source": "catalog", "estimated": False}
    lv = str(level or "4A").strip() or "4A"
    low, high = LEVEL_PRICE.get(lv, LEVEL_PRICE["4A"])
    seed = random.Random("amo-attraction:%s:%s" % (key, lv))
    price = low + (high - low) * seed.random()
    return {"kind": "attraction", "name": key or "景区", "city": str(city or ""), "level": lv,
            "price": _round_price(price), "unit": "人", "source": "level_estimate",
            "estimated": True}


#: 会员/生活服务：一个服务 × 六种买法，凑成 120 条，价格按月费折算。
SUBSCRIPTION_SERVICES = (
    ("视频会员", "追番、看剧", 25.0), ("音乐会员", "听歌、下载", 15.0),
    ("云盘会员", "存照片和文件", 10.0), ("小说会员", "看连载", 12.0),
    ("外卖会员", "每月免配送券", 15.0), ("打车月卡", "通勤打折", 20.0),
    ("健身月卡", "器械和操课", 199.0), ("瑜伽月卡", "每周三节课", 260.0),
    ("话费充值", "手机话费", 100.0), ("流量包", "每月 30G", 30.0),
    ("宽带", "家庭宽带", 80.0), ("视频彩铃", "来电视频", 6.0),
    ("读书会员", "电子书畅读", 18.0), ("网课会员", "技能课", 99.0),
    ("修图会员", "滤镜和模板", 12.0), ("游戏月卡", "手游月卡", 30.0),
    ("洗衣月卡", "上门取送", 99.0), ("家政月卡", "每周一次保洁", 320.0),
    ("宠物会员", "洗护打折", 68.0), ("意外险", "每月保费", 25.0),
)
SUBSCRIPTION_PLANS = (
    ("连续包月", 1.0), ("月卡", 1.0), ("季卡", 2.85),
    ("年卡", 10.8), ("家庭版", 1.45), ("学生版", 0.55),
)


def subscriptions(limit: int = PAGE_SIZE) -> list[dict]:
    """会员与生活服务：每项按连续包月/月卡/季卡/年卡/家庭版/学生版给价。"""
    rows = []
    for name, note, monthly in SUBSCRIPTION_SERVICES:
        for plan, factor in SUBSCRIPTION_PLANS:
            rows.append({
                "kind": "subscription", "id": "%s-%s" % (name, plan),
                "name": "%s·%s" % (name, plan), "service": name, "plan": plan,
                "price": round(monthly * factor, 2),
                "unit": "期" if plan in ("季卡", "年卡") else "月",
                "note": note, "source": "catalog", "estimated": False,
            })
    return rows[:max(1, int(limit))]


def ticket_options(from_city: str = "", limit: int = PAGE_SIZE,
                   now: datetime = None) -> list[dict]:
    """从她所在城市出发的 120 段路：按距离由近到远，票价/方式/耗时都是算出来的。"""
    base = str(from_city or "").strip()
    if not base:
        return []
    here = city_coords(base)
    if not here[0]:
        return []
    table = _load_cities()
    legs = []
    seen = {_strip_city(base)}
    for name in table:
        if not name:
            continue
        key = _strip_city(name)
        if not key or key in seen:      # 「安顺」和「安顺市」是同一段路
            continue
        km = haversine(here, table[name])
        # 5 公里以内是同一个城区（或她所在城市的区县），不是一段「车票」
        if km < 5:
            continue
        seen.add(key)
        legs.append((km, name))
    legs.sort()
    rows = []
    for _km, name in legs[: max(1, int(limit))]:
        quote = ticket_quote(base, name, now)
        if not quote.get("ok"):
            continue
        quote["name"] = "%s→%s" % (base, name)
        quote["category"] = "ticket"
        quote["unit"] = "人"
        quote["note"] = "%s · 约 %d 小时 %d 分" % (
            quote.get("mode_name") or "", int(quote.get("minutes") or 0) // 60,
            int(quote.get("minutes") or 0) % 60)
        rows.append(quote)
    return rows


_SCENIC_CACHE = None


def _scenic_rows() -> list:
    """真实景区清单（470 个，带城市/等级/区域），随版本走。"""
    global _SCENIC_CACHE
    if _SCENIC_CACHE is not None:
        return _SCENIC_CACHE
    rows = []
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenic_spots.json")
        with open(path, encoding="utf-8") as stream:
            raw = json.load(stream) or []
        for row in raw:
            if isinstance(row, dict) and row.get("name"):
                rows.append(row)
    except Exception:
        rows = []
    _SCENIC_CACHE = rows
    return rows


def attraction_options(city: str = "", limit: int = PAGE_SIZE) -> list[dict]:
    """本地和周边 120 个景区：自己城市的排前面，其余按距离；票价按真实档位。"""
    base = str(city or "").strip()
    here = city_coords(base)
    scored = []
    for row in _scenic_rows():
        spot_city = str(row.get("city") or "")
        same = 0 if (base and spot_city == base) else 1
        km = haversine(here, city_coords(spot_city)) if here[0] and spot_city else 9999.0
        scored.append((same, km, str(row.get("name") or ""), row))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    rows = []
    for same, km, name, raw in scored[: max(1, int(limit))]:
        price = attraction(name, str(raw.get("level") or ""), str(raw.get("city") or ""))
        item = dict(price)
        spot_city = str(raw.get("city") or "")
        level = str(raw.get("level") or "景区")
        if same == 0:
            # 本市的景区：写区名，不写「0 公里」
            where = str(raw.get("area") or "本市").strip() or "本市"
            tail = " · " + where
        elif km < 9999 and km >= 1:
            tail = " · 约 %d 公里" % max(1, int(round(km)))
        else:
            tail = ""
        item["note"] = "%s · %s%s" % (spot_city, level, tail)
        item["km"] = round(km, 1) if km < 9999 else None
        item["category"] = "attraction"
        rows.append(item)
    return rows


SECTIONS = (
    {"id": "group", "title": "经营总览", "kinds": ()},
    {"id": "departments", "title": "组织架构", "kinds": ()},
    {"id": "staff", "title": "人员与去留", "kinds": ()},
    {"id": "recruit", "title": "在招岗位", "kinds": ()},
)

KIND_TITLE = {
    "group": "总览", "departments": "部门", "staff": "人员", "recruit": "招聘",
}


def _load_company():
    """智脑集团的数据层（company.py，纯标准库）。"""
    try:
        from . import company as _co  # type: ignore
        return _co
    except Exception:
        pass
    try:
        import company as _co  # type: ignore
        return _co
    except Exception:
        pass
    import importlib.util as _ilu
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "company.py")
    spec = _ilu.spec_from_file_location("amo_company", path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _row(name, category, price, unit="", note="", source="catalog", estimated=False,
         list_price=None):
    return {
        "name": str(name or ""), "category": category, "price": float(price or 0),
        "list_price": float(list_price if list_price is not None else price or 0),
        "unit": str(unit or ""), "note": str(note or ""), "source": source,
        "estimated": bool(estimated), "updated_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def _load_ops():
    try:
        from . import ops as _o  # type: ignore
        return _o
    except Exception:
        pass
    try:
        import ops as _o  # type: ignore
        return _o
    except Exception:
        pass
    try:
        import importlib.util as _ilu
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ops.py")
        spec = _ilu.spec_from_file_location("amo_ops_nexus", path)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception:
        return None


def _load_quant():
    try:
        from . import quant as _q  # type: ignore
        return _q
    except Exception:
        pass
    try:
        import quant as _q  # type: ignore
        return _q
    except Exception:
        pass
    try:
        import importlib.util as _ilu
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quant.py")
        spec = _ilu.spec_from_file_location("amo_quant_nexus", path)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception:
        return None


def _load_company_live():
    try:
        from . import company_live as _cl  # type: ignore
        return _cl
    except Exception:
        pass
    try:
        import company_live as _cl  # type: ignore
        return _cl
    except Exception:
        pass
    try:
        import importlib.util as _ilu
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "company_live.py")
        spec = _ilu.spec_from_file_location("amo_company_live_nexus", path)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception:
        return None


def _item(name, category, price, unit="", note="", extra=None):
    row = _row(name, category, price, unit, note, source="company")
    if extra:
        row.update(extra)
    return row


def build(plugin, city: str = "", province: str = "", now: datetime = None) -> dict:
    """世态改成「智脑集团经营盘子」：总览 / 组织架构 / 人员去留 / 在招岗位。

    用户口径（2026-11-25）：原来那些市场品类全部删掉，不再摆菜价药价，
    买东西走「网络报价 → 扣款」（net_price.py），这里只反映自家公司。
    """
    now = now or datetime.now()
    co = _load_company()
    live = _load_company_live()
    data_dir = str(getattr(plugin, "data_dir", "") or "")
    if live is not None and data_dir:
        depts_src = live.departments(data_dir)
        staff_src = live.fireable(data_dir)
        recruit_src = live.recruit_plan(data_dir)
        rep = live.report(data_dir)
    else:
        depts_src = co.departments()
        staff_src = co.fireable()
        recruit_src = co.recruit_plan()
        rep = co.report()
    idmap = {d["name"]: d["id"] for d in depts_src}
    sections = []

    overview = [
        _item("月度营收", "总览", rep["revenue_total"], "万元", "确认收入合计，含算力租赁与模型授权"),
        _item("综合毛利率", "总览", round(float(rep["gross_total"]) * 100, 1), "%",
              "算力与授权撑住毛利，行业项目拉低"),
        _item("净利润", "总览", rep["net_profit"], "万元", "净利率 %.1f%%" % rep["margin"]),
        _item("账面现金", "总览", rep["cash"], "万元", "可动用头寸"),
        _item("应收账款", "总览", rep["receivable"], "万元", "政企项目回款慢，账期 90 天起"),
        _item("授信可用", "总览", rep["credit_available"], "万元",
              "总额度 %.0f 万，已用 %.0f 万" % (rep["credit_line"], rep["credit_used"])),
        _item("编制 / 在岗", "总览", rep["headcount"], "人",
              "在岗 %d 人，缺编 %d 人" % (rep["onboard"], rep["vacancy"])),
    ]
    sections.append({"id": "group", "title": "智脑集团 · 经营总览",
                     "count": len(overview), "items": overview})

    depts = []
    for d in depts_src:
        note = "%s · 编制 %d／在岗 %d · %s" % (d["head"], d["headcount"], d["onboard"], d["kpi"])
        depts.append(_item(
            d["name"], "部门", d["revenue"], "万/月", note,
            {"dept_id": d["id"], "head": d["head"], "budget": d["budget"],
             "gross": d["gross"],
             "teams": [t["name"] for t in d["teams"]]},
        ))
    sections.append({"id": "departments", "title": "组织架构 · %d 个部门" % len(depts),
                     "count": len(depts), "items": depts})

    staff_rows = []
    total_onboard = sum(int(d.get("onboard") or 0) for d in depts_src)
    staff_rows.append(_item(
        "在册人数", "名册", float(total_onboard), "人",
        "编制 %d，在岗 %d，缺编 %d；下面是抽样，不是全部" % (
            sum(int(d.get("headcount") or 0) for d in depts_src), total_onboard,
            max(0, sum(int(d.get("headcount") or 0) for d in depts_src) - total_onboard)),
        {"total": total_onboard},
    ))
    for d in depts_src:
        for row in (co.roster(d["id"]) if hasattr(co, "roster") else []):
            staff_rows.append(_item(
                row["name"], "人员", 0, "",
                "%s · %s（%s，绩效 %s，%s 年入职）" % (row["dept"], row["post"],
                                                  row["level"], row["perf"], row["since"]),
                {"dept_id": row["dept_id"], "dept": row["dept"], "post": row["post"],
                 "level": row["level"], "perf": row["perf"]},
            ))
    for row in staff_src:
        staff_rows.append(_item(
            row["name"], "可动", row["severance"], "万赔偿",
            "%s · %s（%s，绩效 %s）｜%s" % (row["dept"], row["post"], row["level"],
                                        row["perf"], row["why"]),
            {"dept_id": idmap.get(row["dept"], ""), "dept": row["dept"],
             "post": row["post"], "level": row["level"], "perf": row["perf"],
             "why": row["why"], "fireable": True},
        ))
    sections.append({"id": "staff", "title": "名册 · 在册 %d 人" % total_onboard,
                     "count": len(staff_rows), "items": staff_rows})

    recruit_rows = []
    for row in recruit_src:
        salary = str(row["salary"])
        low = salary.split("~")[0] if "~" in salary else salary
        try:
            price = float(low)
        except Exception:
            price = 0.0
        recruit_rows.append(_item(
            row["post"], "招聘", price, "万/月",
            "%s · 招 %d 人 · 到岗 %s ｜%s" % (row["dept"], row["need"], row["cycle"], row["why"]),
            {"dept_id": idmap.get(row["dept"], ""), "dept": row["dept"],
             "need": row["need"], "cycle": row["cycle"], "why": row["why"],
             "salary": row["salary"]},
        ))
    sections.append({"id": "recruit", "title": "在招岗位 · %d 个" % len(recruit_rows),
                     "count": len(recruit_rows), "items": recruit_rows})

    # ── 今日待批 / 大方向 / 绩效 D / 幻方量化 ────────────────────────
    ops_mod = _load_ops()
    quant_mod = _load_quant()
    if ops_mod is not None and data_dir:
        brief = ops_mod.brief(data_dir)
        docs = brief.get("docs") or []
        doc_rows = []
        for d in docs:
            doc_rows.append(_item(
                d["title"], "文件", d.get("amount") or 0, "万",
                "%s · %s · 限 %d 天｜%s" % (d.get("from") or "", d.get("kind") or "",
                                          int(d.get("days") or 3), d.get("ask") or ""),
                {"doc_id": d["id"], "kind": d.get("kind"), "dept_id": d.get("dept_id"),
                 "days": d.get("days"), "ask": d.get("ask"), "risk": d.get("risk"),
                 "day": d.get("day")},
            ))
        sections.append({"id": "docs", "title": "今日待批 · %d 份" % len(doc_rows),
                         "count": len(doc_rows), "items": doc_rows})

        cur = brief.get("strategy") or {}
        strat_rows = []
        for st in ops_mod.STRATEGIES:
            strat_rows.append(_item(
                st["name"], "方向", 0, "",
                "%s｜%s" % (st["line"], st["kpi"]),
                {"strategy_id": st["id"], "current": bool(cur and cur.get("id") == st["id"]),
                 "effect": st["effect"]},
            ))
        sections.append({"id": "strategy", "title": "大方向", "count": len(strat_rows),
                         "items": strat_rows})

        pol_rows = []
        cur_pol = (brief.get("policy") or {})
        for item in ops_mod.POLICIES:
            pol_rows.append(_item(
                item["name"], "人事", 0, "",
                "%s｜%s" % (item["line"], item["kpi"]),
                {"policy_id": item["id"], "current": bool(cur_pol and cur_pol.get("id") == item["id"]),
                 "effect": item["effect"]},
            ))
        sections.append({"id": "policy", "title": "人事政策", "count": len(pol_rows),
                         "items": pol_rows})

    if quant_mod is not None:
        summ = quant_mod.summary()
        day = quant_mod.pnl()
        qrows = [
            _item("管理规模", "幻方", summ["aum"], "亿元",
                  "自营 %.0f 亿 / 资管 %.0f 亿 · %d 人" % (summ["aum_own"], summ["aum_fund"], summ["staff"])),
            _item("今日盈亏", "幻方", day["pnl"], "万元",
                  "组合 %.2f%% · %s" % (day["ret_pct"], day.get("note", ""))),
            _item("今年收益", "幻方", summ["ytd"], "%", "各策略规模加权"),
            _item("给集团用算力", "幻方", float(str(summ["share_to_group"]).replace("%", "")), "%",
                  "萤火集群共享给智脑"),
        ]
        for st in quant_mod.STRATEGIES:
            qrows.append(_item(
                st["name"], "策略", st["ytd"], "%",
                "规模 %.0f 亿 · 回撤 %.1f%% · 夏普 %.1f｜%s" % (
                    st["aum"], st["drawdown"], st["sharpe"], st["note"]),
                {"aum": st["aum"], "drawdown": st["drawdown"], "sharpe": st["sharpe"]},
            ))
        sections.append({"id": "quant", "title": "幻方量化 · 老本行", "count": len(qrows),
                         "items": qrows})

    items = {sec["id"]: sec["items"] for sec in sections}
    return {
        "version": DATA_VERSION,
        "city": str(city or ""), "province": str(province or ""),
        "city_level": "", "city_factor": 1.0,
        "weekend": False,
        "built_at": now.strftime("%Y-%m-%d %H:%M"),
        "day": now.strftime("%Y-%m-%d"),
        "sections": sections,
        "items": items,
        "counts": {key: len(value) for key, value in items.items()},
        "note": "这是智脑集团的经营盘子，不是商品目录；她买东西走网络实时报价再扣款。",
    }


def save(path: str, payload: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}