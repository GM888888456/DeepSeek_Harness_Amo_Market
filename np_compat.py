# -*- coding: utf-8 -*-
"""兼容层（已精简）：商品目录这套东西退役了。

现在她买东西走「自己报价 → charge 扣款 → 记一条账单」，不再有本地目录，
也没有网络报价模块。这里只保留同名接口，防止老代码 import 失败。
"""

CATALOGS: dict = {}
KINDS: tuple = ()


def counts() -> dict:
    return {}


def rows_for(kind, place="") -> list:
    return []


def pick(kind, place="") -> dict:
    return {}


class persona_catalog:
    @staticmethod
    def ensure_catalog(data_dir, kind, persona_text="", city="", month=""):
        return []


def ensure_catalog(data_dir, kind, persona_text="", city="", month=""):
    return []
