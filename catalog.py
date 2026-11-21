# -*- coding: utf-8 -*-
"""市场目录：药品 / 菜市场 / 外卖 / 服装 / 首饰。

这些是**数据**，不是判定：医疗按病挑药、她按口味挑菜、出门按场景搭衣服，
判定都在各自的引擎里。数量：药 150+、菜市场 100+、外卖 100+、服装 150（汉服/JK/其他各 50）、首饰 100+。
全部确定性生成，重启不变。
"""

from __future__ import annotations

import random

DRUG_GROUPS = {
    "感冒": ("复方氨酚烷胺片", "感冒灵颗粒", "连花清瘟胶囊", "银翘解毒片", "板蓝根颗粒",
             "氨溴索口服液", "右美沙芬糖浆", "对乙酰氨基酚片", "伪麻黄碱缓释胶囊",
             "维C银翘片", "蒲地蓝消炎片", "双黄连口服液"),
    "退烧止痛": ("布洛芬缓释胶囊", "对乙酰氨基酚栓", "阿司匹林肠溶片", "洛索洛芬钠片",
                 "双氯芬酸钠缓释片", "吲哚美辛栓", "安乃近片"),
    "肠胃": ("蒙脱石散", "奥美拉唑肠溶胶囊", "铝碳酸镁咀嚼片", "多潘立酮片",
             "双歧杆菌三联活菌", "消旋山莨菪碱片", "复方谷氨酰胺颗粒", "乳果糖口服液",
             "健胃消食片", "藿香正气水"),
    "过敏": ("氯雷他定片", "西替利嗪片", "依巴斯汀片", "地氯雷他定干混悬剂",
             "糠酸莫米松鼻喷剂", "色甘酸钠滴眼液"),
    "皮肤": ("复方醋酸地塞米松乳膏", "炉甘石洗剂", "莫匹罗星软膏", "夫西地酸乳膏",
             "尿素维E乳膏", "酮康唑乳膏", "维A酸乳膏", "水杨酸软膏"),
    "眼耳": ("左氧氟沙星滴眼液", "玻璃酸钠滴眼液", "妥布霉素滴眼液", "氧氟沙星滴耳液",
             "碳酸氢钠滴耳液"),
    "口腔咽喉": ("复方氯己定含漱液", "西地碘含片", "西瓜霜含片", "甲硝唑口颊片",
                 "开喉剑喷雾剂"),
    "妇科": ("益母草颗粒", "妇科千金片", "乌鸡白凤丸", "逍遥丸", "当归养血丸",
             "布洛芬缓释片", "暖宫贴"),
    "外伤": ("碘伏消毒液", "无菌纱布", "创可贴", "云南白药气雾剂", "红霉素软膏",
             "弹力绷带", "生理盐水冲洗液"),
    "维生素与营养": ("复合维生素B片", "维生素C片", "维生素D3滴剂", "葡萄糖酸钙口服液",
                     "铁剂补血片", "叶酸片", "益生菌粉"),
    "慢病与常用": ("苯磺酸氨氯地平片", "二甲双胍缓释片", "阿托伐他汀钙片", "硝酸甘油片",
                   "氯吡格雷片", "左甲状腺素钠片"),
    "中药与调理": ("小柴胡颗粒", "六味地黄丸", "参苓白术散", "安神补脑液", "川贝枇杷膏",
                   "葛根汤颗粒", "玉屏风颗粒"),
}

PRICE_STEPS = (12.0, 18.0, 22.0, 28.0, 35.0, 42.0, 58.0, 76.0, 98.0, 128.0)


def build_drugs() -> list[dict]:
    rows = []
    for group, names in DRUG_GROUPS.items():
        for index, name in enumerate(names):
            rows.append({"name": name, "group": group, "kind": "药",
                         "price": PRICE_STEPS[index % len(PRICE_STEPS)], "note": group})
    return rows


VEGETABLES = ("西红柿", "黄瓜", "土豆", "白萝卜", "胡萝卜", "白菜", "娃娃菜", "菠菜",
              "油麦菜", "生菜", "韭菜", "芹菜", "西芹", "茄子", "青椒", "尖椒", "洋葱",
              "南瓜", "冬瓜", "丝瓜", "苦瓜", "莲藕", "山药", "豆角", "四季豆", "豌豆",
              "西兰花", "花菜", "莴笋", "茼蒿", "空心菜", "蒜苔", "香菜", "香葱", "生姜",
              "大蒜")
MEAT = ("猪里脊", "五花肉", "前腿肉", "排骨", "牛腩", "牛里脊", "羊腿肉", "鸡胸肉",
        "鸡腿", "鸡翅", "鸭腿", "鲈鱼", "草鱼", "鲫鱼", "带鱼", "虾仁", "基围虾", "鱿鱼")
STAPLE = ("大米", "珍珠米", "糯米", "面粉", "挂面", "米粉", "粉丝", "年糕", "馒头", "花卷")
BEAN_EGG = ("北豆腐", "南豆腐", "豆干", "腐竹", "豆皮", "黄豆", "绿豆", "鸡蛋", "鸭蛋",
            "咸鸭蛋")
FRUIT = ("苹果", "香蕉", "橙子", "砂糖橘", "葡萄", "西瓜", "哈密瓜", "草莓", "蓝莓",
         "桃子", "梨", "猕猴桃", "火龙果", "芒果")
SEASONING = ("生抽", "老抽", "香醋", "蚝油", "料酒", "食盐", "白糖", "冰糖", "花椒",
             "八角", "干辣椒", "五香粉", "豆瓣酱", "番茄酱", "芝麻油")


def build_groceries() -> list[dict]:
    rows = []
    pools = ((VEGETABLES, (2.0, 3.5, 4.5, 6.0)), (MEAT, (18.0, 26.0, 32.0, 45.0)),
             (STAPLE, (3.0, 4.5, 6.0, 9.0)), (BEAN_EGG, (2.5, 4.0, 6.5, 9.0)),
             (FRUIT, (4.0, 6.0, 8.5, 12.0)), (SEASONING, (5.0, 8.0, 12.0, 18.0)))
    for names, prices in pools:
        for index, name in enumerate(names):
            rows.append({"name": name, "price": prices[index % len(prices)],
                         "kind": "菜市场", "unit": "份"})
    return rows


TAKEOUT_SHOPS = {
    "面馆": ("牛肉面", "肥肠面", "酸菜肉丝面", "番茄鸡蛋面", "清汤抄手", "红油抄手"),
    "米粉店": ("牛肉粉", "羊肉粉", "酸汤粉", "拌粉", "螺蛳粉", "炒粉"),
    "家常菜": ("鱼香肉丝盖饭", "宫保鸡丁盖饭", "青椒肉丝盖饭", "番茄炒蛋盖饭",
               "回锅肉盖饭", "小炒黄牛肉盖饭", "辣子鸡盖饭", "土豆烧牛肉盖饭"),
    "快餐": ("鸡腿堡套餐", "双层牛肉堡套餐", "炸鸡桶", "鸡肉卷", "薯条可乐套餐",
             "照烧鸡排饭", "咖喱鸡肉饭"),
    "粥铺": ("皮蛋瘦肉粥", "南瓜小米粥", "鲜虾粥", "白粥配小菜", "山药排骨粥"),
    "烧烤": ("烤五花肉", "烤鸡翅", "烤茄子", "烤韭菜", "烤鸡胗", "蒜蓉生蚝"),
    "甜品奶茶": ("珍珠奶茶", "杨枝甘露", "柠檬茶", "生椰拿铁", "芋泥波波", "双皮奶"),
    "火锅冒菜": ("麻辣冒菜", "番茄冒菜", "肥牛小火锅", "酸汤鱼", "香锅鸡"),
    "轻食": ("鸡胸沙拉", "藜麦蔬菜碗", "牛油果三明治", "全麦鸡肉卷", "低脂酸奶碗"),
    "饭类": ("烤鱼饭", "煲仔饭", "腊味双拼饭", "黄焖鸡米饭", "猪脚饭", "卤肉饭"),
}


def build_takeout() -> list[dict]:
    rows = []
    prices = (12.0, 16.0, 19.0, 22.0, 26.0, 29.0, 33.0, 38.0, 42.0, 48.0, 56.0)
    for shop, dishes in TAKEOUT_SHOPS.items():
        for index, dish in enumerate(dishes):
            rows.append({"name": dish, "shop": shop, "kind": "外卖",
                         "price": prices[(len(shop) + index) % len(prices)]})
    return rows


# ---------- 服装：汉服 1/3、JK 1/3、其他 1/3（2026-11-14 用户定的比例，共 150 件） ----------
#: (名字, 槽位, 风格/朝代)：汉服按朝代成套，JK 按制服体系分件，其余是日常衣服。
HANFU_OUTFITS = (
    # 裙 / 深衣 / 袍（18）
    ("唐制齐胸襦裙", "dress", "汉服·唐制"),
    ("唐制坦领齐腰襦裙", "dress", "汉服·唐制"),
    ("唐制高腰襦裙", "dress", "汉服·唐制"),
    ("唐制圆领袍", "dress", "汉服·唐制"),
    ("唐制坦领襦裙", "dress", "汉服·唐制"),
    ("宋制对襟襦裙", "dress", "汉服·宋制"),
    ("宋制抹胸长裙", "dress", "汉服·宋制"),
    ("宋制圆领袍", "dress", "汉服·宋制"),
    ("宋制褙子长裙", "dress", "汉服·宋制"),
    ("明制立领斜襟长衫", "dress", "汉服·明制"),
    ("明制圆领袍", "dress", "汉服·明制"),
    ("明制立领对襟长衫", "dress", "汉服·明制"),
    ("魏晋交领襦裙", "dress", "汉服·晋制"),
    ("魏晋大袖衫裙", "dress", "汉服·晋制"),
    ("晋制杂裾深衣", "dress", "汉服·晋制"),
    ("汉制曲裾深衣", "dress", "汉服·汉制"),
    ("汉制直裾深衣", "dress", "汉服·汉制"),
    ("明制马面裙套装", "dress", "汉服·明制"),
    # 上衣（12）
    ("唐制坦领半臂", "top", "汉服·唐制"),
    ("唐制齐胸上襦", "top", "汉服·唐制"),
    ("宋制素色褙子", "top", "汉服·宋制"),
    ("宋制抹胸", "top", "汉服·宋制"),
    ("宋制对襟衫", "top", "汉服·宋制"),
    ("宋制半臂", "top", "汉服·宋制"),
    ("明制立领斜襟袄", "top", "汉服·明制"),
    ("明制比甲", "top", "汉服·明制"),
    ("明制披风", "top", "汉服·明制"),
    ("明制主腰", "top", "汉服·明制"),
    ("魏晋大袖衫", "top", "汉服·晋制"),
    ("汉制交领中衣", "top", "汉服·汉制"),
    # 下裙（8）
    ("明制织金马面裙", "bottom", "汉服·明制"),
    ("明制素面马面裙", "bottom", "汉服·明制"),
    ("明制月华裙", "bottom", "汉服·明制"),
    ("宋制宋裤", "bottom", "汉服·宋制"),
    ("宋制百迭裙", "bottom", "汉服·宋制"),
    ("宋制三裥裙", "bottom", "汉服·宋制"),
    ("唐制间色裙", "bottom", "汉服·唐制"),
    ("晋制褶裙", "bottom", "汉服·晋制"),
    # 鞋（6）
    ("唐制绣花翘头履", "shoes", "汉服·唐制"),
    ("明制绣花弓鞋", "shoes", "汉服·明制"),
    ("明制皂靴", "shoes", "汉服·明制"),
    ("宋制素缎绣鞋", "shoes", "汉服·宋制"),
    ("晋制软底布履", "shoes", "汉服·晋制"),
    ("汉制翘头履", "shoes", "汉服·汉制"),
    # 配饰（6）
    ("唐制金步摇", "accessory", "汉服·唐制"),
    ("唐制披帛", "accessory", "汉服·唐制"),
    ("宋制珍珠发夹", "accessory", "汉服·宋制"),
    ("明制珍珠云肩", "accessory", "汉服·明制"),
    ("汉制组玉佩", "accessory", "汉服·汉制"),
    ("魏晋白玉簪", "accessory", "汉服·晋制"),
)

JK_OUTFITS = (
    # 上衣（12）
    ("白色水手服", "jk_shirt", "JK·水手服"),
    ("浅蓝水手服", "jk_shirt", "JK·水手服"),
    ("藏青水手服", "jk_shirt", "JK·水手服"),
    ("粉格水手服", "jk_shirt", "JK·水手服"),
    ("黑红水手服", "jk_shirt", "JK·水手服"),
    ("海军领上衣", "jk_shirt", "JK·海军领"),
    ("奶白短袖衬衣", "jk_shirt", "JK·衬衫"),
    ("白色长袖衬衫", "jk_shirt", "JK·衬衫"),
    ("浅蓝JK衬衫", "jk_shirt", "JK·衬衫"),
    ("灰蓝衬衫", "jk_shirt", "JK·衬衫"),
    ("白色水手领衬衫", "jk_shirt", "JK·水手服"),
    ("藏青水手领上衣", "jk_shirt", "JK·水手服"),
    # 格裙（14）
    ("藏青格裙", "jk_skirt", "JK·格裙"),
    ("黑红格裙", "jk_skirt", "JK·格裙"),
    ("灰格百褶裙", "jk_skirt", "JK·格裙"),
    ("奶咖格裙", "jk_skirt", "JK·格裙"),
    ("深绿格裙", "jk_skirt", "JK·格裙"),
    ("酒红格裙", "jk_skirt", "JK·格裙"),
    ("浅蓝格裙", "jk_skirt", "JK·格裙"),
    ("米色格裙", "jk_skirt", "JK·格裙"),
    ("黑灰格裙", "jk_skirt", "JK·格裙"),
    ("樱粉格裙", "jk_skirt", "JK·格裙"),
    ("灰蓝格裙", "jk_skirt", "JK·格裙"),
    ("藏青纯色裙", "jk_skirt", "JK·格裙"),
    ("深棕格裙", "jk_skirt", "JK·格裙"),
    ("白格裙", "jk_skirt", "JK·格裙"),
    # 袜子（10）
    ("白色短袜", "socks", "JK·袜子"),
    ("黑色短袜", "socks", "JK·袜子"),
    ("棉质中筒袜", "socks", "JK·袜子"),
    ("过膝白袜", "socks", "JK·袜子"),
    ("黑色过膝袜", "socks", "JK·袜子"),
    ("白色中筒袜", "socks", "JK·袜子"),
    ("黑色长袜", "socks", "JK·袜子"),
    ("浅灰中筒袜", "socks", "JK·袜子"),
    ("白底黑边袜", "socks", "JK·袜子"),
    ("米色短袜", "socks", "JK·袜子"),
    # 鞋（8）
    ("黑色乐福鞋", "shoes", "JK·鞋"),
    ("棕色小皮鞋", "shoes", "JK·鞋"),
    ("米色制服鞋", "shoes", "JK·鞋"),
    ("白色系带帆布鞋", "shoes", "JK·鞋"),
    ("黑色玛丽珍", "shoes", "JK·鞋"),
    ("黑色小皮鞋", "shoes", "JK·鞋"),
    ("白色低帮运动鞋", "shoes", "JK·鞋"),
    ("棕色乐福鞋", "shoes", "JK·鞋"),
    # 配饰（6）
    ("学院领结", "accessory", "JK·配饰"),
    ("格纹领带", "accessory", "JK·配饰"),
    ("蝴蝶结领结", "accessory", "JK·配饰"),
    ("领绳", "accessory", "JK·配饰"),
    ("白色发带", "accessory", "JK·配饰"),
    ("蝴蝶结发圈", "accessory", "JK·配饰"),
)

OTHER_OUTFITS = (
    ("白色衬衫", "top", "日常"), ("米色针织衫", "top", "日常"),
    ("黑色小高领", "top", "日常"), ("浅灰卫衣", "top", "日常"),
    ("牛仔外套", "top", "日常"), ("奶油色开衫", "top", "日常"),
    ("条纹长袖", "top", "日常"), ("粉色卫衣", "top", "日常"),
    ("燕麦色毛衣", "top", "日常"), ("黑色西装外套", "top", "日常"),
    ("浅蓝衬衫", "top", "日常"), ("白色T恤", "top", "日常"),
    ("浅蓝牛仔裤", "bottom", "日常"), ("黑色直筒裤", "bottom", "日常"),
    ("米白阔腿裤", "bottom", "日常"), ("卡其工装裤", "bottom", "日常"),
    ("深色半裙", "bottom", "日常"), ("运动裤", "bottom", "日常"),
    ("白色短裤", "bottom", "日常"), ("灰色西装裤", "bottom", "日常"),
    ("牛仔短裙", "bottom", "日常"), ("黑色皮裤", "bottom", "日常"),
    ("黑色连衣裙", "dress", "日常"), ("奶茶色针织连衣裙", "dress", "日常"),
    ("白色吊带裙", "dress", "日常"), ("碎花长裙", "dress", "日常"),
    ("红色小礼裙", "dress", "正式"), ("藏青衬衫裙", "dress", "日常"),
    ("米色针织裙", "dress", "日常"), ("浅蓝牛仔裙", "dress", "日常"),
    ("肉色丝袜", "socks", "袜子"), ("黑色丝袜", "socks", "袜子"),
    ("蕾丝丝袜", "socks", "袜子"), ("渔网袜", "socks", "袜子"),
    ("棉质船袜", "socks", "袜子"), ("白色丝袜", "socks", "袜子"),
    ("白色帆布鞋", "shoes", "鞋"), ("白色运动鞋", "shoes", "鞋"),
    ("黑色短靴", "shoes", "鞋"), ("米色乐福鞋", "shoes", "鞋"),
    ("白色老爹鞋", "shoes", "鞋"), ("黑色高跟鞋", "shoes", "鞋"),
    ("棕色马丁靴", "shoes", "鞋"), ("米色平底鞋", "shoes", "鞋"),
    ("米色贝雷帽", "accessory", "配饰"), ("黑色鸭舌帽", "accessory", "配饰"),
    ("格纹围巾", "accessory", "配饰"), ("细框眼镜", "accessory", "配饰"),
    ("帆布托特包", "accessory", "配饰"), ("黑色小挎包", "accessory", "配饰"),
)


# ---------- 整套服装（2026-11-21：市场只卖整套，数量 汉服40 / 百褶40 / 日常30 / 寝衣4） ----------
#: 款式池：颜色只走清透系（她定的配色），朝代 / 款式组合出 110 套。
_SET_COLORS = ("白", "粉", "浅蓝", "月白", "杏", "鹅黄", "藕荷", "薄荷")
_HANFU = (
    ("唐制", "齐胸裙", "绣花翘头履"),
    ("宋制", "百迭裙", "素缎绣鞋"),
    ("明制", "马面裙", "绣花弓鞋"),
    ("魏晋", "褶裙", "软底布履"),
    ("汉制", "曲裾裙", "翘头履"),
)
_BAIZHE_TOPS = ("水手服", "海军领上衣", "长袖衬衫", "短袖衬衫", "针织水手领")
_BAIZHE_SKIRTS = ("24褶格裙", "28褶格裙", "箱褶裙", "轮褶裙", "纯色百褶裙")
_DAILY_TOPS = ("衬衫", "针织衫", "卫衣", "开衫", "T恤", "毛衣")
_DAILY_BOTTOMS = ("牛仔裤", "直筒裤", "阔腿裤", "半裙", "工装裤")


def _build_outfit_sets() -> tuple:
    """按款式池组合出整套：汉服 40 / 百褶 40 / 日常 30 / 寝衣 4。"""
    sets = []
    # 汉服：5 朝代 × 8 色 = 40
    for dynasty, skirt, shoe in _HANFU:
        for color in _SET_COLORS:
            sets.append((
                "汉服·%s%s抹胸长裙（整套）" % (dynasty, color),
                "汉服·%s" % dynasty,
                (("%s%s抹胸" % (dynasty, color), "top"),
                 ("%s%s%s" % (dynasty, color, skirt), "bottom"),
                 ("%s薄纱披帛" % color, "accessory"),
                 ("%s%s" % (dynasty, shoe), "shoes")),
            ))
    # 百褶（JK 制服）：8 色 × 5 种上衣 = 40
    for t_index, top in enumerate(_BAIZHE_TOPS):
        for c_index, color in enumerate(_SET_COLORS):
            skirt = _BAIZHE_SKIRTS[(t_index + c_index) % len(_BAIZHE_SKIRTS)]
            sets.append((
                "百褶·%s%s（整套）" % (color, top),
                "百褶·%s" % top,
                (("%s%s" % (color, top), "jk_shirt"),
                 ("%s%s" % (_SET_COLORS[(c_index + 3) % len(_SET_COLORS)], skirt), "jk_skirt"),
                 ("%s短袜" % color, "socks"),
                 ("乐福鞋", "shoes"),
                 ("领结", "accessory")),
            ))
    # 日常：6 上装 × 5 色 = 30
    for t_index, top in enumerate(_DAILY_TOPS):
        for c_index, color in enumerate(_SET_COLORS[:5]):
            bottom = _DAILY_BOTTOMS[(t_index + c_index) % len(_DAILY_BOTTOMS)]
            sets.append((
                "日常·%s%s（整套）" % (color, top),
                "日常",
                (("%s%s" % (color, top), "top"),
                 ("%s%s" % (_SET_COLORS[(c_index + 2) % len(_SET_COLORS)], bottom), "bottom"),
                 ("帆布鞋", "shoes"),
                 ("小挎包", "accessory")),
            ))
    # 寝衣（薄纱抹胸长裙）：保留 4 套，睡觉/在家穿
    sets.extend([
        ("寝衣·月纱（整套）", "寝衣",
         (("月白缎面抹胸", "top"), ("月白薄纱长裙", "bottom"), ("白纱披帛", "accessory"))),
        ("寝衣·樱雾（整套）", "寝衣",
         (("樱粉纱质抹胸", "top"), ("米白薄纱长裙", "bottom"), ("樱粉薄纱披帛", "accessory"))),
        ("寝衣·藕烟（整套）", "寝衣",
         (("藕荷缎面抹胸", "top"), ("藕荷薄纱长裙", "bottom"), ("藕荷薄纱披帛", "accessory"))),
        ("寝衣·雪绡（整套）", "寝衣",
         (("白色绣兰抹胸", "top"), ("白色薄纱长裙", "bottom"), ("白玉簪", "accessory"))),
    ])
    return tuple(sets)


OUTFIT_SETS = _build_outfit_sets()


#: 整套价：按类别给定区间（她买的是一整套，不再按单品算钱）
SET_PRICE_RANGE = {
    "汉服": (399.0, 899.0),
    "百褶": (259.0, 459.0),
    "JK": (259.0, 459.0),
    "日常": (199.0, 499.0),
    "寝衣": (299.0, 399.0),
}


def _set_price(style: str, index: int) -> float:
    style = str(style or "")
    for key, (low, high) in SET_PRICE_RANGE.items():
        if key in style:
            steps = 5
            return round(low + (high - low) * ((index * 3) % steps) / (steps - 1), 1)
    return 299.0


def build_outfits() -> list[dict]:
    """服装目录：**只卖整套**（2026-11-21 她的要求）。

    以前卖单件，她买一件上衣进衣柜就成了孤件，`compose_set` 认不出套名，
    日程里配装直接乱掉（她的原话「买了就炸了」）。现在一条商品就是一整套，
    `pieces` 里带齐每个槽位，买回来按「套名｜件名」展开写进衣柜。
    """
    rows = []
    for index, (name, style, pieces) in enumerate(OUTFIT_SETS):
        rows.append({
            "name": name,
            "slot": "set",
            "style": style,
            "kind": "服装",
            "price": _set_price(style, index),
            "pieces": [[piece, slot] for piece, slot in pieces],
        })
    return rows


JEWELRY = {
    "项链": ("细银链", "珍珠项链", "月亮吊坠", "星星项链", "蝴蝶锁骨链", "心形吊坠"),
    "耳饰": ("珍珠耳钉", "银色小圆环", "星星耳夹", "丝绒蝴蝶结耳钉", "月亮耳线",
             "小熊耳钉", "碎钻耳钉", "白色贝壳耳钉"),
    "戒指": ("素圈银戒", "细钻戒指", "珍珠开口戒", "猫爪戒指", "银月戒指"),
    "手链": ("红绳手链", "银珠手链", "珍珠手链", "细金链", "编织手绳", "樱花手链"),
    "发饰": ("珍珠发夹", "丝绒发带", "蝴蝶结发圈", "小抓夹", "星星发卡", "缎面发箍"),
}


def build_jewelry() -> list[dict]:
    rows = []
    prices = (29.0, 49.0, 69.0, 99.0, 129.0, 199.0, 299.0)
    for group, names in JEWELRY.items():
        for index, name in enumerate(names):
            rows.append({"name": name, "group": group, "kind": "首饰",
                         "price": prices[(index + len(group)) % len(prices)]})
    return rows




# ---------- 补量：按用户要求的数量把目录撑满（都是常见真实品名） ----------
EXTRA_DRUGS = {
    "抗生素与消炎": ("阿莫西林胶囊", "头孢克肟片", "阿奇霉素片", "甲硝唑片", "左氧氟沙星片",
                     "罗红霉素胶囊", "克林霉素胶囊"),
    "止咳化痰": ("复方甘草片", "蜜炼川贝枇杷膏", "乙酰半胱氨酸颗粒", "羧甲司坦口服液",
                 "急支糖浆", "止咳橘红丸"),
    "鼻炎与咽喉": ("布地奈德鼻喷雾剂", "鼻渊通窍颗粒", "鼻炎康片", "金嗓子喉片",
                   "咽炎片", "蓝芩口服液"),
    "消化与通便": ("开塞露", "聚乙二醇散", "复方消化酶胶囊", "枯草杆菌二联活菌颗粒",
                   "匹维溴铵片", "复方颠茄片"),
    "皮肤外用药": ("复方酮康唑洗剂", "尿素乳膏", "卤米松乳膏", "他克莫司软膏",
                   "阿昔洛韦乳膏", "清凉油", "风油精"),
    "跌打与止痛": ("活血止痛膏", "麝香壮骨膏", "扶他林软膏", "双氯芬酸二乙胺乳胶剂",
                   "正骨水", "云南白药膏"),
    "妇科与调经": ("坤泰胶囊", "艾附暖宫丸", "少腹逐瘀颗粒", "定坤丹", "桂枝茯苓丸"),
    "儿童常备": ("小儿氨酚黄那敏颗粒", "小儿豉翘清热颗粒", "小儿止咳糖浆",
                 "小儿健胃消食片", "口服补液盐"),
    "维生素与营养": ("维生素E软胶囊", "鱼油软胶囊", "锌硒宝片", "复合氨基酸口服液",
                     "钙镁锌片"),
    "镇静与睡眠": ("褪黑素片", "酸枣仁汤颗粒", "安神定志丸", "枣仁安神胶囊"),
    "心血管与降压": ("缬沙坦胶囊", "美托洛尔缓释片", "厄贝沙坦片", "复方丹参滴丸",
                     "稳心颗粒"),
    "降糖与代谢": ("格列美脲片", "阿卡波糖片", "西格列汀片", "达格列净片"),
    "眼科与护眼": ("七叶洋地黄双苷滴眼液", "聚乙烯醇滴眼液", "叶黄素片", "珍视明滴眼液"),
    "口腔与牙痛": ("甲硝唑芬布芬胶囊", "丁硼乳膏", "口腔溃疡贴", "氯己定漱口水"),
}

EXTRA_TAKEOUT = {
    "卤味": ("卤鸡爪", "卤藕片", "卤鸭脖", "卤蛋", "卤豆干", "卤牛肉"),
    "饺子馄饨": ("白菜猪肉饺", "韭菜鸡蛋饺", "三鲜馄饨", "虾仁水饺", "煎饺套餐"),
    "汤饭": ("砂锅粥", "番茄牛腩汤饭", "老鸭汤", "排骨汤", "酸汤肥牛饭"),
    "烧烤饭": ("烤鸡饭", "照烧鸡腿饭", "烤排骨饭", "盐焗鸡饭"),
    "甜品": ("提拉米苏", "杨枝甘露", "红豆双皮奶", "芋圆烧仙草", "抹茶千层"),
    "夜宵": ("小龙虾", "炒花甲", "烤冷面", "关东煮", "生煎包", "锅贴"),
    "早餐": ("豆浆油条", "豆腐脑", "小笼包", "糯米饭团", "茶叶蛋", "煎饼果子"),
    "饮品": ("鲜榨橙汁", "柠檬水", "豆乳", "美式咖啡", "热可可", "酸梅汤"),
}

EXTRA_JEWELRY = {
    "项链": ("樱花吊坠", "小雏菊项链", "星星锁骨链", "珍珠长链", "月亮石项链"),
    "耳饰": ("珍珠耳线", "银色水滴耳坠", "蝴蝶耳钉", "小雏菊耳夹", "星星耳骨夹"),
    "戒指": ("细银素圈", "月亮石戒指", "珍珠叠戴戒", "蝴蝶结戒指"),
    "手链": ("银色细链", "小雏菊手链", "月亮石手链", "珍珠串珠手链"),
    "发饰": ("珍珠发圈", "蝴蝶结发夹", "星星发圈", "丝绒发箍", "小雏菊发夹"),
    "手镯": ("细银手镯", "珍珠手镯", "藤编手镯", "月亮石手镯", "樱花手镯",
             "细金手镯", "玉髓手镯"),
    "脚链": ("细银脚链", "小铃铛脚链", "珍珠脚链", "红绳脚链", "星星脚链"),
    "胸针": ("小雏菊胸针", "珍珠胸针", "蝴蝶胸针", "月亮胸针", "樱花胸针"),
    "耳骨夹": ("银色耳骨夹", "星星耳骨夹", "小雏菊耳骨夹", "月亮耳骨夹"),
    "发簪": ("珍珠发簪", "木质发簪", "银色发簪", "花瓣发簪", "樱花发簪"),
    "颈链": ("丝绒颈链", "珍珠颈链", "细银颈链", "蝴蝶结颈链", "蕾丝颈链"),
    "戒指套装": ("珍珠叠戒", "细银三件套", "月亮石套装", "小雏菊套装"),
    "耳坠": ("长款珍珠耳坠", "银色流苏耳坠", "月亮石耳坠", "樱花耳坠",
             "星星流苏耳坠", "水钻耳坠"),
    "手串": ("白玉菩提手串", "檀木手串", "水晶手串", "黑曜石手串", "草莓晶手串",
             "石榴石手串", "月光石手串", "碧玺手串", "玛瑙手串"),
}


def _extra_rows(groups, kind, price_pool):
    rows = []
    for group, names in groups.items():
        for index, name in enumerate(names):
            rows.append({"name": name, "group": group, "kind": kind,
                         "price": price_pool[index % len(price_pool)]})
    return rows

def _extend_drugs() -> list[dict]:
    rows = build_drugs()
    for group, names in EXTRA_DRUGS.items():
        for index, name in enumerate(names):
            rows.append({"name": name, "group": group, "kind": "药",
                         "price": PRICE_STEPS[(index + 2) % len(PRICE_STEPS)],
                         "note": group})
    return rows


def _extend_takeout() -> list[dict]:
    rows = build_takeout()
    prices = (13.0, 17.0, 21.0, 25.0, 30.0, 35.0, 40.0, 46.0)
    for shop, dishes in EXTRA_TAKEOUT.items():
        for index, dish in enumerate(dishes):
            rows.append({"name": dish, "shop": shop, "kind": "外卖",
                         "price": prices[(index + len(shop)) % len(prices)]})
    return rows


#: 每个槽位的价格区间（元）：上衣/裤子便宜，外套裙鞋贵，袜子最便宜
OUTFIT_PRICE_RANGE = {
    "top": (69.0, 259.0), "bottom": (89.0, 229.0), "dress": (159.0, 399.0),
    "jk_skirt": (119.0, 199.0), "jk_shirt": (99.0, 169.0),
    "socks": (9.9, 39.0), "shoes": (159.0, 499.0), "accessory": (19.0, 99.0),
}


def _outfit_price(slot: str, index: int) -> float:
    low, high = OUTFIT_PRICE_RANGE.get(str(slot or ""), (49.0, 199.0))
    steps = 7
    return round(low + (high - low) * ((index * 3) % steps) / (steps - 1), 1)


def _extend_outfits() -> list[dict]:
    rows = build_outfits()
    for index, row in enumerate(rows):
        if not row.get("price"):
            row["price"] = _outfit_price(row.get("slot"), index)
        row.setdefault("kind", "服装")
    return rows


def _extend_jewelry() -> list[dict]:
    rows = build_jewelry()
    prices = (29.0, 39.0, 59.0, 79.0, 89.0, 129.0, 169.0, 199.0, 259.0)
    for group, names in EXTRA_JEWELRY.items():
        for index, name in enumerate(names):
            rows.append({"name": name, "group": group, "kind": "首饰",
                         "price": prices[(index + len(group)) % len(prices)]})
    return rows


#: 美妆护肤：不写具体品牌名（价格会失真），按「品类 × 档位」给真实区间。
COSMETIC_ITEMS = {
    "口红": (("豆沙色口红", "平价"), ("正红色口红", "中档"), ("丝绒雾面口红", "中档"),
             ("镜面唇釉", "平价"), ("高定唇膏", "大牌")),
    "底妆": (("持妆粉底液", "中档"), ("哑光气垫", "平价"), ("遮瑕膏", "平价"),
             ("控油散粉", "平价"), ("贵妇粉霜", "大牌")),
    "眼妆": (("细头眉笔", "平价"), ("大地色眼影盘", "中档"), ("防水眼线液", "平价"),
             ("纤长睫毛膏", "平价")),
    "腮红": (("蜜桃腮红", "平价"), ("膏状腮红", "中档")),
    "护肤": (("氨基酸洁面乳", "平价"), ("保湿面膜", "平价"), ("玻尿酸精华", "中档"),
             ("修护面霜", "中档"), ("抗老精华", "大牌"), ("防晒霜", "中档"),
             ("卸妆水", "平价"), ("眼霜", "中档")),
    "身体": (("氨基酸洗发水", "平价"), ("护发精油", "中档"), ("身体乳", "平价"),
             ("沐浴露", "平价"), ("护手霜", "平价")),
    "香氛": (("柑橘调淡香水", "中档"), ("木质调香水", "大牌"), ("花香调香水", "大牌")),
}
COSMETIC_PRICE = {
    "平价": (39.0, 99.0),
    "中档": (139.0, 359.0),
    "大牌": (420.0, 1280.0),
}


def build_cosmetics() -> list[dict]:
    rows = []
    for group, items in COSMETIC_ITEMS.items():
        for index, (name, tier) in enumerate(items):
            low, high = COSMETIC_PRICE.get(tier, (49.0, 199.0))
            price = round(low + (high - low) * ((index * 2 + len(group)) % 5) / 4.0, 1)
            rows.append({"name": name, "group": group, "tier": tier, "kind": "美妆",
                         "price": price, "unit": "件"})
    return rows


#: 堂食：菜名 + 餐馆类型，价格比外卖高一点（有服务费和茶位）。
DINING_ITEMS = (
    ("丝娃娃", "小吃店", 26.0), ("肠旺面", "面馆", 18.0), ("酸汤鱼", "黔菜馆", 88.0),
    ("辣子鸡", "黔菜馆", 68.0), ("豆米火锅", "火锅店", 78.0), ("烙锅", "夜市摊", 55.0),
    ("牛肉粉", "粉店", 15.0), ("羊肉粉", "粉店", 18.0), ("遵义豆花面", "面馆", 16.0),
    ("烤鱼", "烤鱼店", 98.0), ("小龙虾", "大排档", 128.0), ("烧烤拼盘", "烧烤店", 68.0),
    ("火锅双人餐", "火锅店", 168.0), ("酸菜鱼", "川菜馆", 88.0), ("回锅肉", "川菜馆", 42.0),
    ("麻婆豆腐", "川菜馆", 26.0), ("水煮牛肉", "川菜馆", 58.0), ("宫保鸡丁", "川菜馆", 38.0),
    ("北京烤鸭", "京菜馆", 168.0), ("小笼包", "点心店", 22.0), ("生煎", "点心店", 18.0),
    ("牛肉火锅", "潮汕火锅", 158.0), ("猪脚饭", "快餐店", 22.0), ("黄焖鸡米饭", "快餐店", 20.0),
    ("煲仔饭", "粤菜馆", 32.0), ("艇仔粥", "粤菜馆", 18.0), ("虾饺", "茶餐厅", 28.0),
    ("日式拉面", "日料店", 42.0), ("寿司拼盘", "日料店", 78.0), ("咖喱饭", "日料店", 36.0),
    ("意面", "西餐厅", 48.0), ("牛排", "西餐厅", 128.0), ("披萨", "西餐厅", 78.0),
    ("汉堡套餐", "快餐店", 35.0), ("炸鸡桶", "快餐店", 69.0), ("沙拉", "轻食店", 32.0),
    ("甜品拼盘", "甜品店", 38.0), ("咖啡", "咖啡店", 28.0), ("奶茶", "奶茶店", 16.0),
    ("早茶套餐", "茶餐厅", 68.0),
)


def build_dining() -> list[dict]:
    return [{"name": name, "shop": shop, "kind": "堂食", "price": float(price),
             "unit": "份"} for name, shop, price in DINING_ITEMS]


def _pad(rows: list[dict], target: int, suffixes, factors) -> list[dict]:
    """把目录补到 target 条：同一样东西的规格/分量/档位，价格按比例走。

    只补「规格」，不编新商品：名字唯一、价格有依据，衣柜和市场都不会重名合并。
    """
    base = []
    seen = set()
    for row in rows:
        name = str(row.get("name") or "")
        if not name or name in seen:
            continue
        seen.add(name)
        base.append(dict(row))
    out = [dict(row) for row in base]
    index = 0
    guard = 0
    while len(out) < target and base and guard < target * 6:
        guard += 1
        row = dict(base[index % len(base)])
        suffix = suffixes[(index // len(base)) % len(suffixes)]
        factor = float(factors[(index // len(base)) % len(factors)])
        row["name"] = "%s%s" % (row.get("name") or "", suffix)
        row["price"] = round(float(row.get("price") or 0) * factor, 1)
        row["spec"] = suffix.strip("（）()")
        index += 1
        if row["name"] in seen:
            continue
        seen.add(row["name"])
        out.append(row)
    return out


DRUGS = _extend_drugs()
GROCERIES = _pad(build_groceries(), 126,
                 ("（本地）", "（精品）", "（特价）"),
                 (0.95, 1.35, 0.8))
TAKEOUT = _pad(_extend_takeout(), 126,
               ("（大份）", "（小份）", "（加辣）", "（加蛋）"),
               (1.35, 0.75, 1.0, 1.1))
OUTFITS = _extend_outfits()
JEWELRY_ITEMS = _pad(_extend_jewelry(), 126,
                     ("（细款）", "（加长）", "（礼盒）"),
                     (1.0, 1.15, 1.4))


COSMETICS = _pad(build_cosmetics(), 126,
                 ("·限定色", "·旅行装", "·礼盒装", "·替换装"),
                 (1.0, 0.45, 1.35, 0.8))
DINING = _pad(build_dining(), 120,
              ("（单人）", "（双人）", "（套餐）"),
              (1.0, 1.8, 1.45))

CATALOGS = {
    "drugs": DRUGS,
    "groceries": GROCERIES,
    "takeout": TAKEOUT,
    "outfits": OUTFITS,
    "jewelry": JEWELRY_ITEMS,
    "cosmetics": COSMETICS,
    "dining": DINING,
}


def counts() -> dict:
    return {key: len(value) for key, value in CATALOGS.items()}


def pick(kind: str, rng: random.Random | None = None) -> dict:
    rows = CATALOGS.get(str(kind or "")) or []
    if not rows:
        return {}
    chooser = rng or random.Random()
    return dict(chooser.choice(rows))
