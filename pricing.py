# -*- coding: utf-8 -*-
"""现实价格引擎：新发地真实菜价 + 城市系数 + 缓存/定时。

用户 2026-11-14 定：
- 菜价每天 06:30 拉新发地公开接口；周末不拉；失败不重试，用昨天缓存 ±3%。
- 22:00–06:00 菜市场关门，只能点外卖。
- 外卖不拉 API：当天菜价 ×1.5 + 配送费（午高峰 +3，深夜 +6，部分商家 +20%）。
- 城市价格：新发地底价 × 城市公开食品价格指数系数；系数表放本地
  `city_food_index.json`，由公开城市 CPI/食品价格数据维护，代码不编价格。

这个模块只算价格，不判定买不买；判定仍在终端/医疗/金融。

⚠️ 这里的 ``_post_xinfadi`` / ``_fetch_cpi`` / ``refresh_gold`` 都是**同步阻塞**的
urllib 调用（最长等到 timeout 秒）。它们只允许在线程里跑：事件循环里请用
``await book.atick()``（内部 ``asyncio.to_thread``），别直接调 ``tick()``——2026-11-18
审核打回的就是「菜价/金价到点把整条 AstrBot 事件循环卡 15 秒」。
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime

XINFADI_URL = "http://www.xinfadi.com.cn/getPriceData.html"
#: 公开、免密钥的总体 CPI（世界银行，年度）；药品价格稳定，用它做整体指数
CPI_URL = ("https://api.worldbank.org/v2/country/CHN/indicator/"
           "FP.CPI.TOTL?format=json&per_page=5")
CACHE_NAME = "price_cache.json"
CITY_INDEX_NAME = "city_food_index.json"
DRUG_INDEX_NAME = "drug_price_index.json"
GOLD_CACHE_NAME = "gold_price.json"
GOLD_URL = "https://api.gold-api.com/price/XAU"

#: 换季感冒/呼吸道药：春天和秋天各加 5%
COLD_WORDS = ("感冒", "咳嗽", "退烧", "清热", "抗病毒", "连花", "板蓝根",
              "阿莫西林", "头孢", "止咳", "咽喉", "鼻炎")

#: 新发地篮子：只取这些常见品算指数，避免某个冷门菜把整体带偏
BASKET = ("大白菜", "土豆", "西红柿", "黄瓜", "青椒", "茄子",
          "鸡蛋", "猪肉", "大米", "面粉", "苹果", "香蕉")

#: 外卖基础加工系数（菜价 × 1.5 是餐饮毛利+加工）
TAKEOUT_MARKUP = 1.5


def _now():
    return datetime.now()


def _day_key(now=None):
    return (now or _now()).strftime("%Y-%m-%d")


def _fetch_cpi(timeout: int = 15) -> float:
    """世界银行公开 CPI：最新年 / 上一年；只请求一次，失败不重试。"""
    with urllib.request.urlopen(CPI_URL, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    values = []
    for row in rows or []:
        try:
            year = int(row.get("date") or 0)
            value = float(row.get("value") or 0)
        except (TypeError, ValueError):
            continue
        if year and value > 0:
            values.append((year, value))
    values.sort(reverse=True)
    if len(values) < 2:
        return 1.0
    latest, previous = values[0][1], values[1][1]
    return round(latest / previous, 4)


def _post_xinfadi(limit: int = 800, timeout: int = 15) -> list[dict]:
    """拉新发地当天公开均价；只请求一次，不做任何重试。"""
    body = urllib.parse.urlencode({
        "limit": str(max(1, int(limit))),
        "current": "1",
        "pubDateStartTime": "",
        "pubDateEndTime": "",
        "prodPestLosses": "",
        "prodCatId": "",
        "prodName": "",
    }).encode("utf-8")
    request = urllib.request.Request(
        XINFADI_URL, data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (AmoMarket price book)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("list") if isinstance(payload, dict) else []
    return [row for row in (rows or []) if isinstance(row, dict)]


class PriceBook:
    """一份本地价格缓存：谁问都读它，不在请求里现拉。"""

    def __init__(self, data_dir: str, fetcher=None, clock=None, cpi_fetcher=None):
        self.data_dir = str(data_dir or ".")
        self.cache_path = os.path.join(self.data_dir, CACHE_NAME)
        self.city_path = os.path.join(self.data_dir, CITY_INDEX_NAME)
        self._fetch = fetcher or _post_xinfadi
        self._fetch_cpi = cpi_fetcher or _fetch_cpi
        self._clock = clock or _now
        self.cache = self._load_cache()

    # ---------- 缓存 ----------

    def _load_cache(self) -> dict:
        try:
            with open(self.cache_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_cache(self) -> None:
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            tmp = self.cache_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as handle:
                json.dump(self.cache, handle, ensure_ascii=False, indent=2)
            os.replace(tmp, self.cache_path)
        except Exception:
            pass

    # ---------- 城市系数 ----------

    def city_table(self) -> dict:
        """城市/省份 → 公开食品价格指数系数；读不到就空表。"""
        try:
            with open(self.city_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}
        rows = data.get("cities") if isinstance(data.get("cities"), dict) else data
        return rows if isinstance(rows, dict) else {}

    def city_factor(self, city: str = "", province: str = "") -> tuple[float, str]:
        """返回 (系数, 来源说明)。没有公开数据时老实返回 1.0。"""
        table = self.city_table()
        for key in (str(city or "").strip(), str(province or "").strip()):
            row = table.get(key)
            if isinstance(row, dict):
                try:
                    factor = float(row.get("factor") or 1.0)
                except (TypeError, ValueError):
                    factor = 1.0
                return factor, str(row.get("source") or "city_food_index")
            if isinstance(row, (int, float)):
                return float(row), "city_food_index"
        return 1.0, "default"

    # ---------- 菜价 ----------

    def _basket_value(self, rows: list[dict]) -> float:
        values = []
        for row in rows or []:
            name = str(row.get("prodName") or "").strip()
            if name not in BASKET:
                continue
            try:
                price = float(row.get("avgPrice") or 0)
            except (TypeError, ValueError):
                price = 0.0
            if price > 0:
                values.append(price)
        if values:
            return round(sum(values) / len(values), 4)
        # 篮子没命中：退回全部有价蔬菜的均价
        fallback = []
        for row in rows or []:
            if "蔬菜" not in str(row.get("prodCat") or ""):
                continue
            try:
                price = float(row.get("avgPrice") or 0)
            except (TypeError, ValueError):
                price = 0.0
            if price > 0:
                fallback.append(price)
        return round(sum(fallback) / len(fallback), 4) if fallback else 0.0

    def refresh_groceries(self, force: bool = False, now=None) -> dict:
        """拉一次当天菜价；失败不重试，保留缓存并打 ±3% 微调标记。"""
        now = now or self._clock()
        today = _day_key(now)
        state = dict(self.cache.get("groceries") or {})
        if not force:
            if now.weekday() >= 5:          # 周末官方接口不更新，不拉
                return {"ok": True, "skipped": "weekend"}
            if state.get("day") == today and state.get("ok"):
                return {"ok": True, "skipped": "already"}
            if state.get("day") == today and state.get("failed"):
                return {"ok": False, "skipped": "failed_today"}
        try:
            rows = self._fetch()
            basket = self._basket_value(rows)
            if basket <= 0:
                raise ValueError("empty basket")
            baseline = float(self.cache.get("baseline") or 0) or basket
            self.cache["baseline"] = baseline
            self.cache["groceries"] = {
                "day": today, "ts": now.timestamp(), "ok": True,
                "basket": basket, "count": len(rows), "jitter": 1.0,
                "source": "xinfadi",
            }
            self._save_cache()
            return {"ok": True, "basket": basket, "count": len(rows)}
        except Exception as exc:
            state.update({
                "day": today, "failed": True, "ok": False,
                "ts": now.timestamp(), "error": str(exc)[:160],
                "jitter": round(random.uniform(0.97, 1.03), 4),
            })
            self.cache["groceries"] = state
            self._save_cache()
            return {"ok": False, "reason": str(exc)[:160], "stale": True}

    def grocery_index(self, city: str = "", province: str = "") -> float:
        """今天菜价 / 首次基线；失败日再乘 ±3%。"""
        state = self.cache.get("groceries") or {}
        basket = float(state.get("basket") or 0)
        baseline = float(self.cache.get("baseline") or 0)
        index = (basket / baseline) if basket > 0 and baseline > 0 else 1.0
        index *= float(state.get("jitter") or 1.0)
        factor, _ = self.city_factor(city, province)
        return round(index * factor, 4)

    def market_open(self, now=None) -> bool:
        """06:00–22:00 菜市场开门；22:00 后只能外卖。"""
        hour = (now or self._clock()).hour
        return 6 <= hour < 22

    # ---------- 金价 / 大促 ----------

    def gold_state(self) -> dict:
        path = os.path.join(self.data_dir, GOLD_CACHE_NAME)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_gold(self, state: dict) -> None:
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            path = os.path.join(self.data_dir, GOLD_CACHE_NAME)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception:
            pass

    def refresh_gold(self, force: bool = False, now=None) -> dict:
        """每月 1 号拿一次公开金价；失败不重试，保留上月缓存。"""
        now = now or self._clock()
        month = now.strftime("%Y-%m")
        state = self.gold_state()
        if not force and state.get("month") == month and state.get("price"):
            return {"ok": True, "skipped": "already"}
        if not force and state.get("failed_month") == month:
            return {"ok": False, "skipped": "failed_month"}
        try:
            request = urllib.request.Request(
                GOLD_URL, headers={"User-Agent": "Mozilla/5.0 (AmoMarket price book)"})
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            price = float(payload.get("price") or 0)
            if price <= 0:
                raise ValueError("bad gold price")
            baseline = float(state.get("baseline") or 0) or price
            state = {"month": month, "price": price, "baseline": baseline,
                     "source": "gold-api.com", "ts": now.timestamp()}
            self._save_gold(state)
            return {"ok": True, "price": price, "baseline": baseline}
        except Exception as exc:
            state.update({"failed_month": month, "error": str(exc)[:160]})
            self._save_gold(state)
            return {"ok": False, "reason": str(exc)[:160]}

    def gold_factor(self) -> float:
        state = self.gold_state()
        price = float(state.get("price") or 0)
        baseline = float(state.get("baseline") or 0)
        return round(price / baseline, 4) if price > 0 and baseline > 0 else 1.0

    @staticmethod
    def sale_factor(now=None) -> float:
        """双 11 / 618 服装首饰五折。"""
        now = now or _now()
        return 0.5 if (now.month, now.day) in ((11, 11), (6, 18)) else 1.0

    # ---------- 外卖 ----------

    @staticmethod
    def delivery_fee(now=None) -> tuple[float, float]:
        """返回 (配送费, 商家加价系数)：午高峰 +3；22 点后 +6、部分 +20%。"""
        hour = (now or _now()).hour
        if 11 <= hour < 13:
            return 3.0, 1.0
        if hour >= 22 or hour < 6:
            return 6.0, 1.2
        return 0.0, 1.0

    def takeout_price(self, base: float, city: str = "", province: str = "",
                      now=None, name: str = "") -> float:
        """外卖 = 菜价指数 × 1.5 × base + 配送费；深夜部分商家 +20%。"""
        try:
            value = float(base or 0)
        except (TypeError, ValueError):
            value = 0.0
        index = self.grocery_index(city, province)
        fee, markup = self.delivery_fee(now)
        price = value * index * TAKEOUT_MARKUP
        if markup > 1.0:
            chooser = random.Random("amo-takeout:%s:%s" % (_day_key(now), name))
            if chooser.random() < 0.35:
                price *= markup
        return round(max(0.0, price) + fee, 2)

    # ---------- 药品指数 ----------

    def refresh_drug_index(self, force: bool = False, now=None) -> dict:
        """周一 08:00 更新一次；失败不重试，保留上次指数。"""
        now = now or self._clock()
        today = _day_key(now)
        state = dict(self.cache.get("drug_index") or {})
        if not force:
            if now.weekday() != 0:
                return {"ok": True, "skipped": "not_monday"}
            if state.get("day") == today and state.get("ok"):
                return {"ok": True, "skipped": "already"}
            if state.get("day") == today and state.get("failed"):
                return {"ok": False, "skipped": "failed_today"}
        try:
            factor = float(self._fetch_cpi())
            if not (0.9 <= factor <= 1.2):
                raise ValueError("cpi factor out of range")
            self.cache["drug_index"] = {
                "day": today, "ts": now.timestamp(), "ok": True,
                "factor": round(factor, 4), "source": "worldbank_cpi",
            }
            self._save_cache()
            return {"ok": True, "factor": round(factor, 4)}
        except Exception as exc:
            state.update({"day": today, "ok": False, "failed": True,
                          "ts": now.timestamp(), "error": str(exc)[:160]})
            self.cache["drug_index"] = state
            self._save_cache()
            return {"ok": False, "reason": str(exc)[:160], "stale": True}

    def drug_factor(self, now=None) -> float:
        state = self.cache.get("drug_index") or {}
        try:
            return float(state.get("factor") or 1.0)
        except (TypeError, ValueError):
            return 1.0

    @staticmethod
    def seasonal_drug_factor(name: str, now=None) -> float:
        """春天/秋天感冒呼吸道药 +5%。"""
        month = (now or _now()).month
        if month in (3, 4, 5, 9, 10, 11) and any(
                word in str(name or "") for word in COLD_WORDS):
            return 1.05
        return 1.0

    # ---------- 定时 ----------

    def tick(self, now=None) -> dict:
        """每分钟调用：06:30 拉菜价；每月 1 号拉金价；都不重试。"""
        now = now or self._clock()
        if now.day == 1 and self.gold_state().get("month") != now.strftime("%Y-%m"):
            return self.refresh_gold(now=now)
        if now.weekday() < 5 and (now.hour, now.minute) >= (6, 30):
            state = self.cache.get("groceries") or {}
            if state.get("day") != _day_key(now) and not state.get("failed"):
                return self.refresh_groceries(now=now)
        if now.weekday() == 0 and (now.hour, now.minute) >= (8, 0):
            state = self.cache.get("drug_index") or {}
            if state.get("day") != _day_key(now) and not state.get("failed"):
                return self.refresh_drug_index(now=now)
        return {"ok": True, "skipped": "not_due"}

    async def atick(self, now=None) -> dict:
        """事件循环安全版 ``tick()``：到点抓的是外网，必须丢到线程里跑。

        直接 ``await`` 这个，别在协程里同步调 ``tick()``，否则一次抓取就能把整条
        AstrBot 事件循环（消息收发、别的插件）卡住最长 timeout 秒。
        """
        return await asyncio.to_thread(self.tick, now)

    # ---------- 给目录行调价 ----------

    def adjust_rows(self, kind: str, rows: list[dict], city: str = "",
                    province: str = "", now=None) -> list[dict]:
        """按现实指数调整目录价；不判断买不买。"""
        now = now or self._clock()
        out = []
        for row in rows or []:
            item = dict(row)
            base = float(item.get("price") or 0)
            item["list_price"] = base
            if kind == "groceries":
                item["price"] = round(base * self.grocery_index(city, province), 2)
                item["grocery_closed"] = not self.market_open(now)
            elif kind == "takeout":
                item["price"] = self.takeout_price(base, city, province, now,
                                                   str(item.get("name") or ""))
            elif kind == "drugs":
                factor = self.drug_factor(now) * self.seasonal_drug_factor(
                    str(item.get("name") or ""), now)
                item["price"] = round(base * factor, 2)
                item["drug_index"] = round(factor, 4)
            elif kind in ("outfits", "jewelry"):
                factor = self.sale_factor(now)
                if kind == "jewelry":
                    factor *= self.gold_factor()
                item["price"] = round(base * factor, 2)
                if self.sale_factor(now) < 1.0:
                    item["sale"] = "5 折"
            out.append(item)
        return out
