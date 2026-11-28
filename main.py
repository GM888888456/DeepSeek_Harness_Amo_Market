# -*- coding: utf-8 -*-
"""我想永远陪着你-市场：只提供目录数据（药/菜/外卖/服装/首饰）。

判定不在这里：医疗按病挑药、她按口味挑菜、出门按场景搭衣服，都在各自的引擎里。
这里只保证「东西够多、价格稳定、名字真实」，面板能看，插件能查。
"""

from __future__ import annotations

import asyncio
import os
import random
import time

from astrbot.api import logger

try:
    from . import config_watch as _config_watch
except ImportError:
    import mk_config_watch as _config_watch  # type: ignore

try:
    from .chain import Chain
except ImportError:
    from mk_chain import Chain  # type: ignore
from astrbot.api.event import filter
from astrbot.api.star import Context, Star

try:  # 面板 POST 的 kind/q 靠它读；缺了这个导入，异常会被 except 吞掉，永远只回药品
    from astrbot.api.web import request as web_request
except Exception:  # pragma: no cover - 单测/CI 里没有 astrbot
    web_request = None

try:
    from .np_compat import CATALOGS, counts, pick, persona_catalog
    from .pricing import PriceBook
    from . import nexus
except ImportError:  # 单测/CI 按文件加载
    from np_compat import CATALOGS, counts, pick, persona_catalog  # type: ignore
    from mk_pricing import PriceBook  # type: ignore
    import mk_nexus  # type: ignore

try:
    from .config_guard import heal as _cfg_heal, fallback_data_dir as _cfg_data_dir, remember as _cfg_remember
except Exception:  # pragma: no cover
    try:
        from mk_config_guard import heal as _cfg_heal, fallback_data_dir as _cfg_data_dir, remember as _cfg_remember  # type: ignore
    except Exception:
        _cfg_heal = None

PLUGIN_NAME = "DeepSeek_Harness_Amo_Market"
PLUGIN_VERSION = "1.0.0"
DISPLAY_NAME = "DeepSeek Harness Amo Market"


class AmoMarketPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        # 插件目录是 <data>/plugins/<名>，plugin_data 与 plugins 同级：
        # 以前只往上跳一级，market_data.json 落到了 plugins/plugin_data 里。
        self.data_dir = os.path.join(
            os.path.dirname(os.path.dirname(self.plugin_dir)), "plugin_data", PLUGIN_NAME)
        self.price_book = PriceBook(self.data_dir)
        self.nexus_path = os.path.join(self.data_dir, "market_data.json")
        self._nexus = nexus.load(self.nexus_path)
        self._nexus_day = str(self._nexus.get("day") or "")
        # 并入金融后由宿主指定前缀（/market），避免和金融的 /status 撞车
        self.web_prefix = str((self.config or {}).get("web_prefix") or "").rstrip("/")
        self._price_task = None
        self._start_price_loop()
        self._register_web_apis()
        logger.info("[amo_market] %s %s 已加载：%s" % (DISPLAY_NAME, PLUGIN_VERSION,
                                                      " / ".join(
                                                          "%s %d" % (k, v)
                                                          for k, v in counts().items())))

    # ---------- 给别的插件/终端用 ----------

    def _companion(self):
        try:
            try:
                from .link import _find, TERMINAL_NAMES, TERMINAL_MARKERS
            except ImportError:
                from mk_link import _find, TERMINAL_NAMES, TERMINAL_MARKERS  # type: ignore
            return _find(self.context, TERMINAL_NAMES, TERMINAL_MARKERS)
        except Exception:
            return None

    def _city(self) -> tuple[str, str]:
        """她的城市/省份：从终端世界观读；读不到就空（价格系数 1.0）。"""
        try:
            companion = self._companion()
            state = getattr(companion, "state", None)
            world = getattr(state, "worldview", {}) or {}
            return (str(world.get("city") or "").strip(),
                    str(world.get("province") or "").strip())
        except Exception:
            return "", ""

    def _start_price_loop(self) -> None:
        """06:30 拉菜价的后台循环；没有事件循环就跳过，面板请求时仍会读缓存。"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._price_task = loop.create_task(self._price_loop())
        except Exception:
            self._price_task = None

    async def _price_loop(self) -> None:
        while True:
            try:
                # 抓菜价/金价是同步 urllib：必须丢进线程，别卡事件循环（审核项）
                await self.price_book.atick()
                day = time.strftime("%Y-%m-%d")
                if day != self._nexus_day:
                    self.market_data(refresh=True)
            except Exception as exc:
                logger.debug("[amo_market] 价格定时失败: %s" % exc)
                # 每分钟一条链会刷屏：只有失败才留痕，方便回头看是哪天的刷新坏了
                Chain("market.price", logger=logger).fail("tick", str(exc))
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                return

    def _persona_text(self) -> str:
        """人格 + 世界观里能读到的描述：城市、日常、规则、人设。"""
        try:
            companion = self._companion()
            state = getattr(companion, "state", None)
            world = getattr(state, "worldview", {}) or {}
            parts = [str(world.get(key) or "") for key in
                     ("city", "daily_life", "world_rules", "persona", "style")]
            conf = getattr(companion, "config", {}) or {}
            for key in ("persona", "persona_name", "outfit_gender",
                        "character_appearance", "character_hairstyle"):
                parts.append(str(conf.get(key) or ""))
            return " ".join(part for part in parts if part).strip()
        except Exception:
            return ""

    def items(self, kind: str) -> list:
        """商品目录已退役：她买东西靠 SPEND 报价 + charge 扣款。"""
        return []

    def net_rows(self, kind: str, place: str = "") -> list:
        return []

    def price_snapshot(self) -> dict:
        city, province = self._city()
        state = dict(self.price_book.cache.get("groceries") or {})
        return {
            "city": city, "province": province,
            "grocery_index": self.price_book.grocery_index(city, province),
            "grocery_day": state.get("day") or "",
            "grocery_ok": bool(state.get("ok")),
            "grocery_error": state.get("error") or "",
            "grocery_closed": not self.price_book.market_open(),
            "source": state.get("source") or "xinfadi",
            "drug_factor": self.price_book.drug_factor(),
            "gold_factor": self.price_book.gold_factor(),
            "sale": self.price_book.sale_factor(),
        }

    # ---------- 真实世界枢纽：统一数据 + 询价 ----------

    def market_data(self, city: str = "", refresh: bool = False) -> dict:
        """五个版块统一成一份：价格、单位、来源、更新时间、城市系数。"""
        city_now, province = self._city()
        city = str(city or city_now or "").strip()
        day = time.strftime("%Y-%m-%d")
        cached = self._nexus if isinstance(self._nexus, dict) else {}
        if (not refresh and cached and str(cached.get("day") or "") == day
                and str(cached.get("city") or "") == city
                and int(cached.get("version") or 0) == int(nexus.DATA_VERSION)):
            return cached
        try:
            data = nexus.build(self, city, province)
        except Exception as exc:
            logger.warning("[amo_market] 枢纽数据构建失败: %s" % exc)
            return cached or {}
        if nexus.save(self.nexus_path, data):
            self._nexus = data
            self._nexus_day = day
        return data

    def section(self, kind: str, city: str = "", keyword: str = "", limit: int = 400) -> list:
        """某一类（菜/药/服装/酒店/订阅…）的当前价；给终端和面板同一个口径。"""
        kind = str(kind or "").strip()
        if kind in ("hotel", "hotels"):
            return nexus.hotel_options(city or self._city()[0])
        if kind in ("subscription", "subscriptions"):
            return nexus.subscriptions()
        if kind in ("attraction", "attractions"):
            return nexus.attraction_options(city or self._city()[0])
        if kind in ("ticket", "tickets"):
            return nexus.ticket_options(city or self._city()[0])
        data = self.market_data(city)
        rows = list(((data.get("items") or {}).get(kind) or []))
        word = str(keyword or "").strip()
        if word:
            rows = [row for row in rows if word in str(row.get("name") or "")]
        return rows[:max(1, int(limit or 400))]

    def hotel_quote(self, city: str = "", budget: float = 0) -> dict:
        """按余额挑一档酒店；budget=0 时只给三档列表。"""
        city = str(city or self._city()[0] or "").strip()
        if budget and float(budget) > 0:
            return nexus.pick_hotel(city, budget)
        return {"city": city, "options": nexus.hotel_options(city)}

    def ticket_quote(self, from_city: str = "", to_city: str = "") -> dict:
        """两地之间的车票：里程、方式、耗时、票价区间。"""
        return nexus.ticket_quote(from_city or self._city()[0], to_city)

    def attraction_price(self, name: str, level: str = "", city: str = "") -> dict:
        return nexus.attraction(name, level, city or self._city()[0])

    def subscriptions(self) -> list[dict]:
        return nexus.subscriptions()

    def city_tag(self) -> dict:
        city, province = self._city()
        factor, level = nexus.city_factor(city)
        return {"city": city, "province": province, "level": level, "factor": factor}

    def drugs(self) -> list[dict]:
        return self.items("drugs")

    def groceries(self) -> list[dict]:
        return self.items("groceries")

    def takeout(self) -> list[dict]:
        return self.items("takeout")

    def outfits(self) -> list[dict]:
        return self.items("outfits")

    def jewelry(self) -> list[dict]:
        return self.items("jewelry")

    def counts(self) -> dict:
        return counts()

    def groceries_open(self, now=None) -> bool:
        """06:00–22:00 菜市场开门；22:00 后只能点外卖。"""
        return self.price_book.market_open(now)

    def pick(self, kind: str):
        rows = self.items(kind)
        return dict(random.choice(rows)) if rows else {}

    def search(self, kind: str, keyword: str) -> list[dict]:
        word = str(keyword or "").strip()
        rows = self.items(kind)
        if not word:
            return rows
        return [row for row in rows if word in str(row.get("name") or "")]

    # ---------- 面板 ----------

    def _json(self, payload):
        return payload

    def _register_web_apis(self) -> None:
        routes = [
            ("/status", self.api_status, ["GET"]),
            ("/health", self.api_health, ["GET"]),
            ("/link", self.api_link, ["GET"]),
            ("/items", self.api_items, ["GET", "POST"]),
            ("/catalog", self.api_catalog, ["GET", "POST"]),
            ("/nexus", self.api_nexus, ["GET", "POST"]),
            ("/data", self.api_market_data, ["GET"]),
            ("/company", self.api_company, ["GET", "POST"]),
            ("/query", self.api_query, ["POST"]),
            ("/hotel", self.api_hotel, ["POST"]),
            ("/ticket", self.api_ticket, ["POST"]),
        ]
        for path, handler, methods in routes:
            try:
                self.context.register_web_api("/" + PLUGIN_NAME + self.web_prefix + path, handler, methods, path)
            except TypeError:
                try:
                    self.context.register_web_api("/" + PLUGIN_NAME + self.web_prefix + path, methods, path, handler)
                except Exception as exc:
                    logger.warning("[amo_market] 接口 %s 注册失败: %s" % (path, exc))
            except Exception as exc:
                logger.warning("[amo_market] 接口 %s 注册失败: %s" % (path, exc))

    async def api_link(self):
        """市场自己不判定，但要告诉面板「终端在不在」。"""
        connected = False
        try:
            for meta in self.context.get_all_stars():
                text = (str(getattr(meta, "name", "") or "") + " "
                        + str(getattr(meta, "module_path", "") or ""))
                if "Amo_forever" in text or "我想永远陪着你-终端" in text:
                    connected = True
                    break
        except Exception as exc:
            logger.debug("[amo_market] 探测终端失败: %s" % exc)
        return self._json({"code": 0, "data": {
            "connected": connected, "target": "Amo 终端"}})

    def _link_probe(self):
        """直接调用同目录 link.py（不依赖 sys.path），拿到终端/记忆/版本/bot_id/心跳。"""
        try:
            import importlib.util
            import os
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "link.py")
            spec = importlib.util.spec_from_file_location("amo_market_link", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.probe(self)
        except Exception as exc:
            logger.debug("[amo_market] 连接探测失败: %s" % exc)
            return {}

    def _sync_config(self) -> None:
        """AstrBot 原生设置页改完，把配置文件的新值并进内存（面板与接口立刻一致）。"""
        try:
            _config_watch.reload_if_changed(self.config, logger)
        except Exception as exc:
            logger.debug("[config] 同步配置文件失败: %s" % exc)

    async def api_health(self):
        self._sync_config()
        payload = dict(self._link_probe())
        payload.update({"ok": True, "name": PLUGIN_NAME, "version": PLUGIN_VERSION,
                        "counts": counts()})
        return self._json({"code": 0, "data": payload})

    async def api_status(self):
        self._sync_config()
        return self._json({"code": 0, "data": {
            "name": PLUGIN_NAME, "display_name": DISPLAY_NAME,
            "version": PLUGIN_VERSION, "counts": counts(),
            "kinds": ["drugs", "groceries", "takeout", "outfits", "jewelry",
                      "dining", "cosmetics", "hotel", "subscriptions",
                      "supermarket", "snacks", "electronics"],
            "price": self.price_snapshot(),
            "city": self.city_tag(),
            "sections": [{"id": row["id"], "title": row["title"], "count": row["count"]}
                         for row in (self.market_data().get("sections") or [])],
        }})

    async def api_catalog(self):
        """五类目录一次给全，并带上当天盘面：天气、折扣、涨价、售空。"""
        day = time.strftime("%Y-%m-%d")
        # 盘面直接内联算，不再依赖外部模块（插件是按文件加载的，相对导入不一定成立）
        weather, base, note = random.Random("amo-market:%s" % day).choice((
            ("晴", 1.00, "天气好，菜多，价稳"),
            ("多云", 1.02, "货正常"),
            ("小雨", 1.08, "下雨，叶菜涨一点"),
            ("大雨", 1.16, "暴雨，菜少价高"),
            ("降温", 1.10, "天冷，火锅菜好卖"),
            ("升温", 1.05, "天热，瓜果走俏"),
        ))
        sensitive = {"drugs": 0.2, "groceries": 1.0, "takeout": 0.7, "dining": 0.7,
                     "outfits": 0.3, "jewelry": 0.1, "cosmetics": 0.2,
                     "supermarket": 0.15, "snacks": 0.1, "electronics": 0.02}
        factor_rnd = random.Random("amo-market-f:%s" % day)
        state = {"weather": weather, "note": note,
                 "factors": {k: 1.0 + (base - 1.0) * v * (1.0 + factor_rnd.uniform(-0.03, 0.03))
                             for k, v in sensitive.items()}}
        rnd = random.Random("amo-market-items:%s" % day)
        kinds = tuple(CATALOGS.keys())
        catalog = {}
        for kind in kinds:
            factor = float(state["factors"].get(kind) or 1.0)
            if kind in ("groceries", "takeout", "dining", "cosmetics"):
                factor = 1.0   # 现实价格已由 PriceBook 调过，不再叠天气系数
            rows = []
            for row in self.items(kind):
                item = dict(row)
                base = float(item.get("price") or 0)
                price = round(base * factor, 2)
                # 约 8% 今天打折，约 5% 售空
                mark = rnd.random()
                if mark < 0.08:
                    price = round(price * 0.8, 2)
                    item["discount"] = "8 折"
                elif mark < 0.10:
                    price = round(price * 1.15, 2)
                    item["surcharge"] = "涨价"
                item["list_price"] = base
                item["price"] = price
                item["soldout"] = rnd.random() < 0.05
                rows.append(item)
            catalog[kind] = rows
        return self._json({"code": 0, "data": {
            "catalog": catalog, "counts": counts(),
            "weather": {"day": day, "weather": state["weather"], "note": state["note"]},
            "price": self.price_snapshot(),
        }})

    async def _payload(self) -> dict:
        payload = {}
        try:
            if web_request is not None and hasattr(web_request, "json"):
                data = await web_request.json(default={})
                if isinstance(data, dict):
                    payload = data
            if not payload and web_request is not None:
                data = await web_request.get_json(silent=True)
                if isinstance(data, dict):
                    payload = data
        except Exception:
            payload = {}
        return payload

    async def api_nexus(self):
        """一个请求给全五个版块（面板首屏用）。"""
        self._sync_config()
        data = self.market_data()
        return self._json({"code": 0, "data": data})

    def _ops(self):
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
            spec = _ilu.spec_from_file_location("amo_ops_main", path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
        except Exception:
            return None

    def _quant(self):
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
            spec = _ilu.spec_from_file_location("amo_quant_main", path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
        except Exception:
            return None

    def office(self, action: str = "brief", target: str = "", note: str = "") -> dict:
        """经营台的动作总入口（面板和聊天工具都走这里）。"""
        cl = self._company_live()
        ops = self._ops()
        quant = self._quant()
        action = str(action or "brief").strip().lower()
        target = str(target or "").strip()
        data_dir = self.data_dir

        if action in ("brief", "today"):
            if ops is None:
                return {"ok": False, "msg": "日常层没加载上"}
            b = ops.brief(data_dir)
            return {"ok": True, "brief": b, "line": b["line"]}

        if action in ("approve", "reject"):
            if ops is None:
                return {"ok": False, "msg": "日常层没加载上"}
            res = ops.decide(data_dir, target, "approve" if action == "approve" else "reject", note)
            if res.get("ok") and res.get("cash_delta") and cl is not None:
                cl.adjust_cash(data_dir, res["cash_delta"],
                               "批「%s」占款 %.0f 万" % (res["doc"]["title"], abs(res["cash_delta"])))
            return res

        if action in ("policy", "bonus", "cut"):
            if ops is None:
                return {"ok": False, "msg": "日常层没加载上"}
            key = "bonus" if action == "bonus" else ("cut" if action == "cut" else target)
            res = ops.set_policy(data_dir, key or target)
            if res.get("ok") and cl is not None:
                pick = (res.get("policy") or {}).get("id")
                delta = -1200.0 if pick == "bonus" else 460.0
                cl.adjust_cash(data_dir, delta, "人事政策：" + ("发奖金" if pick == "bonus" else "降本增效"))
            return res

        if action in ("direction", "strategy", "set_strategy"):
            if ops is None:
                return {"ok": False, "msg": "日常层没加载上"}
            return ops.set_strategy(data_dir, target or note)

        if action == "fire_d":
            if ops is None or cl is None:
                return {"ok": False, "msg": "日常层没加载上"}
            res = ops.fire_perf_d(data_dir, target)
            if not res.get("ok"):
                return res
            for person in res.get("fired") or []:
                cl.fire_forced(data_dir, person["dept"], person["name"],
                               person.get("post", ""), person.get("severance", 0),
                               person.get("why", ""))
            return res

        if action in ("fill_gap", "fill"):
            if ops is None or cl is None:
                return {"ok": False, "msg": "日常层没加载上"}
            gaps = ops.gaps(data_dir)
            if not gaps:
                return {"ok": False, "msg": "没有待补的缺口"}
            pick = None
            for g in gaps:
                if not target or target in g.get("post", "") or target in g.get("dept", ""):
                    pick = g
                    break
            pick = pick or gaps[0]
            try:
                salary = float(str(pick.get("salary") or "1.5").split("~")[0])
            except Exception:
                salary = 1.5
            hired = cl.hire_custom(data_dir, pick["dept"], pick["post"],
                                   round(salary * 1.6, 2), pick.get("why", ""))
            if hired.get("ok"):
                ops.close_gap(data_dir, pick["dept"], pick["post"],
                              (hired.get("hired") or {}).get("name", ""))
            return {"ok": bool(hired.get("ok")), "hired": hired.get("hired"),
                    "msg": ("补上了：%s 接手 %s 的活" % ((hired.get("hired") or {}).get("name", ""), pick["post"]))
                    if hired.get("ok") else "补招没成"}

        if action == "quant":
            if quant is None:
                return {"ok": False, "msg": "幻方模块没加载上"}
            return {"ok": True, "summary": quant.summary(), "pnl": quant.pnl(),
                    "strategies": quant.STRATEGIES, "path": quant.PATH,
                    "risk": quant.RISK_LINES}

        if action in ("customer", "add_customer"):
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return cl.add_customer(data_dir, target, note or "政企")
        if action in ("contract", "sign_contract"):
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return cl.create_contract(data_dir, target, note or "项目合同",
                                     float(getattr(self, "_office_amount", 0) or 0),
                                     float(getattr(self, "_office_margin", 0.35) or 0.35))
        if action == "invoice":
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return cl.invoice(data_dir, target, float(getattr(self, "_office_amount", 0) or 0))
        if action in ("receive", "payment"):
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return cl.receive(data_dir, target, float(getattr(self, "_office_amount", 0) or 0))
        if action in ("project", "start_project"):
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return cl.project(data_dir, target, note or "方案部",
                              float(getattr(self, "_office_amount", 0) or 0))
        if action in ("spend", "expense"):
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return cl.spend(data_dir, float(getattr(self, "_office_amount", 0) or 0), note or "经营支出")
        if action in ("tick", "day_close"):
            if cl is None: return {"ok": False, "msg": "状态层没加载上"}
            return {"ok": True, "live": cl.tick(data_dir)}
        if action in ("live", "operations"):
            return {"ok": True, "live": cl.snapshot(data_dir) if cl is not None else {}}
        if action == "fire":
            return cl.fire(data_dir, target, note) if cl is not None else {"ok": False, "msg": "状态层没加载上"}
        if action == "hire":
            return cl.hire(data_dir, target, note) if cl is not None else {"ok": False, "msg": "状态层没加载上"}
        if action == "reset":
            return cl.reset(data_dir) if cl is not None else {"ok": False, "msg": "状态层没加载上"}
        if action == "timeline":
            return {"ok": True, "log": cl.timeline(data_dir) if cl is not None else []}
        if action == "report":
            return {"ok": True, "report": cl.report(data_dir) if cl is not None else {}}
        return {"ok": False, "msg": "不认识的动作：%s" % action}

    def _company_live(self):
        """集团实时状态层（company_live.py）。"""
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
            spec = _ilu.spec_from_file_location("amo_company_live", path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
        except Exception as exc:
            logger.debug("[amo_market] 集团状态层加载失败: %s" % exc)
            return None

    async def api_company(self):
        """经营台的动作接口：全部转给 office()。

        参数走 querystring 或 JSON body：action / target / note。
        """
        params = {}
        try:
            if web_request is not None and hasattr(web_request, "query"):
                params.update(dict(web_request.query))
        except Exception:
            pass
        try:
            body = await self._payload()
            if isinstance(body, dict):
                params.update(body)
        except Exception:
            pass
        action = str(params.get("action") or "report").strip().lower()
        try:
            try: self._office_amount = float(params.get("amount") or params.get("value") or 0)
            except Exception: self._office_amount = 0.0
            try: self._office_margin = float(params.get("margin") or 0.35)
            except Exception: self._office_margin = 0.35
            res = self.office(action, str(params.get("target") or params.get("dept") or params.get("name") or params.get("customer") or params.get("contract_id") or ""),
                              str(params.get("note") or params.get("post") or params.get("title") or params.get("sector") or ""))
        except Exception as exc:
            logger.warning("[amo_market] 经营动作失败: %s" % exc)
            return self._json({"code": 1, "msg": str(exc)})
        if action in ("approve", "reject", "direction", "strategy", "fire_d", "fill_gap", "fill",
                      "fire", "hire", "reset", "customer", "add_customer", "contract", "sign_contract",
                      "invoice", "receive", "payment", "project", "start_project", "spend", "expense", "tick", "day_close"):
            self._nexus = {}
            self._nexus_day = ""
        # 动作回包：前端拿 data 就行
        payload = dict(res) if isinstance(res, dict) else {"ok": False}
        payload.setdefault("action", action)
        return self._json({"code": 0, "data": payload, "ok": payload.get("ok", True),
                           "msg": payload.get("msg", "")})

    async def api_market_data(self):
        self._sync_config()
        return self._json({"code": 0, "data": self.market_data()})

    async def api_query(self):
        payload = await self._payload()
        kind = str(payload.get("kind") or "groceries")
        keyword = str(payload.get("q") or "")
        city = str(payload.get("city") or "")
        rows = self.section(kind, city=city, keyword=keyword)
        return self._json({"code": 0, "data": {
            "kind": kind, "total": len(rows), "items": rows[:400],
            "city": self.city_tag(),
        }})

    async def api_hotel(self):
        payload = await self._payload()
        city = str(payload.get("city") or "")
        try:
            budget = float(payload.get("budget") or 0)
        except (TypeError, ValueError):
            budget = 0.0
        if budget > 0:
            return self._json({"code": 0, "data": self.hotel_quote(city, budget)})
        return self._json({"code": 0, "data": {
            "city": city or self._city()[0], "options": nexus.hotel_options(city or self._city()[0]),
        }})

    async def api_ticket(self):
        payload = await self._payload()
        quote = self.ticket_quote(str(payload.get("from") or ""),
                                  str(payload.get("to") or ""))
        return self._json({"code": 0, "data": quote})

    async def api_items(self):
        kind = "drugs"
        keyword = ""
        payload = {}
        try:  # aiohttp 的请求体：面板 POST 的 kind 就靠它，取不到会永远回药品
            if web_request is not None and hasattr(web_request, "json"):
                data = await web_request.json(default={})
                if isinstance(data, dict):
                    payload = data
            if not payload and web_request is not None:
                data = await web_request.get_json(silent=True)
                if isinstance(data, dict):
                    payload = data
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            kind = str(payload.get("kind") or kind)
            keyword = str(payload.get("q") or "")
        rows = self.search(kind, keyword)
        return self._json({"code": 0, "data": {"kind": kind, "total": len(rows),
                                              "items": rows[:400]}})


def counts_text() -> str:
    return " / ".join("%s %d" % (key, value) for key, value in counts().items())
