# -*- coding: utf-8 -*-
"""我想永远陪着你-市场。"""
try:  # 正常包内加载
    from .main import AmoMarketPlugin, PLUGIN_NAME, PLUGIN_VERSION
except Exception:  # 单测/CI 按文件加载时没有包上下文
    from main import AmoMarketPlugin, PLUGIN_NAME, PLUGIN_VERSION

__all__ = ["AmoMarketPlugin", "PLUGIN_NAME", "PLUGIN_VERSION"]
