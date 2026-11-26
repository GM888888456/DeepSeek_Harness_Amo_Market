# -*- coding: utf-8 -*-
"""中国计算智脑集团：组织架构 / 人员名册 / 招聘 / 开除 / 经营报表（纯标准库）。

用户口径（2026-11-25）：
- 她的职业改为「中国计算智脑集团总裁」；
- 世态不再摆市场品类，改成自家公司的经营盘子（营收、架构、部门、人员）；
- 每个部门要能看出「能开除谁」，也要有在招岗位；
- 买东西不再翻目录，改成「网络报价 → 扣款」。

本模块只提供数据与纯函数，不落库、不发消息。金额单位：万元/月（元的地方单独标）。

结构约定
    dept = {
        id, name, short, duty, head, head_note,
        teams: [ {name, duty} ],
        headcount, onboard, band, budget, kpi, output,
        revenue, gross,           # 月度确认收入 / 毛利率
        staff: [ {name, post, level, since, salary, perf, fire_note} ],
        recruit: [ {post, level, salary, need, cycle, why} ],
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

GROUP = {
    "name": "中国计算智脑集团",
    "short": "智脑",
    "since": 2019,
    "hq": "贵阳·观山湖（总部）",
    "branch": "京都·海淀（分部）",
    "business": "智能算力基础设施、大模型训练与推理服务、政企行业解决方案、自研推理芯片与整机",
    "chair": "沈晓沫",
    "vice": ["林致远（常务副总裁·分管经营）", "周慕之（高级副总裁·分管技术）"],
    "board": ["董事长 沈晓沫", "董事 沈卫兰（家族代表・不参与经营）", "独立董事 陆宗铭", "独立董事 何书棠"],
    "headcount": 3733,
    "note": "2019 年在贵阳观山湖起家，先做机房与算力租赁，2021 年转做大模型训练服务，2023 年推出自研推理卡「知源一号」，现在是西南算力盘子里的头部。",
}

# ── 部门 ──────────────────────────────────────────────────────────────
DEPARTMENTS: List[Dict[str, Any]] = [
    {
        "id": "office", "name": "总裁办", "short": "总办",
        "duty": "战略落地、总裁日程、董事会与投资人关系、重大事项督办、对外政府事务",
        "head": "林致远", "head_note": "常务副总裁兼总办主任，跟了她六年，替她挡人挡事",
        "teams": [
            {"name": "战略组", "duty": "三年规划、年度经营目标拆解、季度复盘"},
            {"name": "秘书组", "duty": "日程、纪要、材料、公文流转"},
            {"name": "政府事务组", "duty": "园区、审批、专项资金、协会关系"},
        ],
        "headcount": 60, "onboard": 56, "band": "0.9~3.2", "budget": 180,
        "kpi": "重大事项闭环率 ≥95%，董事会材料零差错",
        "output": "战略与督办，不直接产生收入",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "郑书禾", "post": "总裁秘书", "level": "P5", "since": "2021-03", "salary": 1.4, "perf": "A", "fire_note": "不能动：她的日程和私人事务全靠这个人，换人会漏事"},
            {"name": "邵一鸣", "post": "战略组负责人", "level": "M2", "since": "2020-07", "salary": 2.6, "perf": "B", "fire_note": "可以动：规划写得漂亮，落地跟进差，季度复盘经常拖"},
            {"name": "柯敏", "post": "政府事务专员", "level": "P4", "since": "2022-11", "salary": 1.1, "perf": "C", "fire_note": "可以动：跑审批慢，靠关系吃饭，换人成本低"},
            {"name": "白露", "post": "督办专员", "level": "P4", "since": "2023-04", "salary": 1.0, "perf": "A", "fire_note": "留着：跨部门催办的活只有她压得住"},
        ],
        "recruit": [
            {"post": "投资者关系经理", "level": "M1", "salary": "2.0~2.6", "need": 1, "cycle": "45 天", "why": "今年要见两轮机构，缺一个能讲清算力毛利的"},
        ],
    },
    {
        "id": "finance", "name": "财务部", "short": "财务",
        "duty": "会计核算、资金与授信、税务筹划、成本管控、经营分析、子公司并表",
        "head": "顾清源", "head_note": "CFO，注册会计师出身，稳，只认数字",
        "teams": [
            {"name": "会计组", "duty": "总账、应收应付、并表"},
            {"name": "资金组", "duty": "现金流、授信、银承、外汇"},
            {"name": "税务组", "duty": "税筹、发票、汇算清缴"},
            {"name": "经营分析组", "duty": "月度经营分析、部门成本归集、定价测算"},
        ],
        "headcount": 140, "onboard": 132, "band": "0.8~4.5", "budget": 420,
        "kpi": "月结 3 个工作日内出表，资金零风险事件",
        "output": "成本管控与资金效率，间接支撑毛利 2~3 个点",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "顾清源", "post": "CFO", "level": "M4", "since": "2019-06", "salary": 4.5, "perf": "A", "fire_note": "不能动：银行授信和并表全在他手上"},
            {"name": "汤瑾", "post": "资金组负责人", "level": "M2", "since": "2020-09", "salary": 2.4, "perf": "B", "fire_note": "可以用：银承贴现慢，被银行客户经理牵着走"},
            {"name": "王小满", "post": "会计主管", "level": "M1", "since": "2021-05", "salary": 1.6, "perf": "C", "fire_note": "可以开：连续两个月结账超期，凭证错账 7 笔"},
            {"name": "祝云开", "post": "经营分析", "level": "P6", "since": "2022-03", "salary": 1.9, "perf": "A", "fire_note": "留着：部门成本归集和定价测算都靠她"},
        ],
        "recruit": [
            {"post": "税务经理", "level": "M1", "salary": "2.2~2.8", "need": 1, "cycle": "60 天", "why": "研发加计和跨省预缴越来越复杂，缺个能顶事的"},
        ],
    },
    {
        "id": "hr", "name": "人力部", "short": "人力",
        "duty": "组织与编制、招聘、薪酬绩效、员工关系、培训、干部管理",
        "head": "范允之", "head_note": "CHO，老练，说话绕着来",
        "teams": [
            {"name": "招聘组", "duty": "社招、校招、猎头对接"},
            {"name": "薪酬绩效组", "duty": "职级、调薪、绩效评审"},
            {"name": "员工关系组", "duty": "劳动合同、离职谈判、仲裁应诉"},
            {"name": "培训组", "duty": "新人训、干部梯队、技术分享"},
        ],
        "headcount": 90, "onboard": 84, "band": "0.8~3.6", "budget": 260,
        "kpi": "关键岗到位周期 ≤45 天，主动离职率 ≤8%",
        "output": "编制与人才供给",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "范允之", "post": "CHO", "level": "M4", "since": "2020-02", "salary": 3.6, "perf": "A", "fire_note": "不能动：干部梯队是她一手指起来的"},
            {"name": "舒桐", "post": "招聘负责人", "level": "M2", "since": "2021-08", "salary": 2.0, "perf": "B", "fire_note": "可以动：算法岗交付慢，猎头费花得多"},
            {"name": "孟小舟", "post": "员工关系专员", "level": "P4", "since": "2022-06", "salary": 1.0, "perf": "C", "fire_note": "可以开：去年一起仲裁他漏了证据，赔了 18 万"},
        ],
        "recruit": [
            {"post": "高级招聘经理（算法方向）", "level": "M1", "salary": "1.8~2.4", "need": 1, "cycle": "40 天", "why": "研发院今年缺口 30 人，现有团队啃不动"},
        ],
    },
    {
        "id": "legal", "name": "法务部", "short": "法务",
        "duty": "合同审查、投融资、知识产权、数据合规、诉讼",
        "head": "宋知微", "head_note": "法务总监，说话慢，句句留退路",
        "teams": [
            {"name": "商事组", "duty": "重大合同、采购与销售条款"},
            {"name": "知产组", "duty": "专利、软著、商标、开源合规"},
            {"name": "数据合规组", "duty": "数据出境、个人信息保护、算法备案"},
        ],
        "headcount": 48, "onboard": 45, "band": "1.0~3.0", "budget": 150,
        "kpi": "重大合同零重大遗漏，争议案件胜诉率 ≥70%",
        "output": "风险兜底",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "宋知微", "post": "法务总监", "level": "M3", "since": "2020-11", "salary": 3.0, "perf": "A", "fire_note": "不能动：算法备案和政企合同都压在她手上"},
            {"name": "曾以宁", "post": "知产律师", "level": "P6", "since": "2021-09", "salary": 1.8, "perf": "B", "fire_note": "可以动：专利布局拖沓，去年只报了三件"},
            {"name": "廉小乙", "post": "合同专员", "level": "P3", "since": "2023-08", "salary": 0.7, "perf": "C", "fire_note": "可以开：合同台账三次漏登，差点漏掉一个自动续约条款"},
        ],
        "recruit": [
            {"post": "数据合规顾问", "level": "M1", "salary": "2.2~3.0", "need": 1, "cycle": "50 天", "why": "海外客户要跨境数据方案，现在没人能签这个字"},
        ],
    },
    {
        "id": "audit", "name": "审计部", "short": "审计",
        "duty": "内控流程、采购与费用审计、子公司巡查、举报核查",
        "head": "贺守铭", "head_note": "审计负责人，退休返聘的老会计，最不怕得罪人",
        "teams": [
            {"name": "内控组", "duty": "流程穿行测试、权限复核"},
            {"name": "专项审计组", "duty": "采购、费用、工程项目"},
        ],
        "headcount": 30, "onboard": 28, "band": "0.9~2.8", "budget": 90,
        "kpi": "年度审计覆盖 100%，重大舞弊零发生",
        "output": "风控",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "贺守铭", "post": "审计负责人", "level": "M3", "since": "2021-01", "salary": 2.6, "perf": "A", "fire_note": "不能动：他手里有采购口的账，动他就是动自己"},
            {"name": "莫岚", "post": "内控专员", "level": "P5", "since": "2022-04", "salary": 1.2, "perf": "B", "fire_note": "可以用：流程文档写得细，但不敢碰人"},
        ],
        "recruit": [],
    },
    {
        "id": "idc", "name": "基建部", "short": "基建",
        "duty": "智算中心选址建设、机房运维、液冷与电力、算力资源调度、算力租赁业务",
        "head": "钟伯庸", "head_note": "干了二十年机房的老工程，贵安三个楼的电他都摸过",
        "teams": [
            {"name": "建设组", "duty": "选址、设计、机电施工、验收"},
            {"name": "运维组", "duty": "7x24 值班、故障处置、PUE 优化"},
            {"name": "资源调度组", "duty": "算力池编排、租户配额、计费"},
            {"name": "电力与制冷组", "duty": "变电站、柴发、液冷循环"},
        ],
        "headcount": 620, "onboard": 588, "band": "0.7~4.0", "budget": 2600,
        "kpi": "PUE ≤1.22，可用性 ≥99.95%，算力售出率 ≥85%",
        "output": "贵安智算中心 3 栋楼 / 折合 8600P（FP16）算力，对外租赁与自用",
        "revenue": 9800.0, "gross": 0.34,
        "staff": [
            {"name": "钟伯庸", "post": "事业部总经理", "level": "M5", "since": "2019-04", "salary": 4.0, "perf": "A", "fire_note": "不能动：贵安三栋楼的电力和验收关系全是他"},
            {"name": "鲁大川", "post": "运维总监", "level": "M3", "since": "2020-03", "salary": 2.8, "perf": "B", "fire_note": "可以用：凌晨那次断电他值班，处置慢了两小时"},
            {"name": "邱一得", "post": "建设组负责人", "level": "M2", "since": "2020-08", "salary": 2.4, "perf": "B", "fire_note": "可以动：三号楼工期拖了四十天，成本超了 6%"},
            {"name": "龚小满", "post": "值班班长", "level": "P4", "since": "2021-06", "salary": 0.9, "perf": "C", "fire_note": "可以开：三次巡检未按规程签字"},
        ],
        "recruit": [
            {"post": "液冷工程师", "level": "P6", "salary": "1.8~2.6", "need": 3, "cycle": "35 天", "why": "三号楼全上液冷，现有队伍不会调"},
            {"post": "电力工程师（高压）", "level": "P6", "salary": "1.6~2.2", "need": 2, "cycle": "50 天", "why": "110kV 变电站要自有值班资格"},
        ],
    },
    {
        "id": "research", "name": "研发院", "short": "研发院",
        "duty": "基座预训练、后训练与对齐、推理优化、数据工程、多模态",
        "head": "周慕之", "head_note": "高级副总裁兼院长，她自己从架构师时代带出来的人",
        "teams": [
            {"name": "预训练组", "duty": "数据配比、训练稳定性、长上下文"},
            {"name": "后训练组", "duty": "SFT、偏好对齐、工具调用、评测"},
            {"name": "推理优化组", "duty": "量化、算子、显存、吞吐与延迟"},
            {"name": "数据工程组", "duty": "语料治理、清洗流水线、标注管理"},
            {"name": "多模态组", "duty": "图生文、文生图、视频理解"},
        ],
        "headcount": 720, "onboard": 668, "band": "1.2~8.0", "budget": 4200,
        "kpi": "千卡线性加速比 ≥0.86，推理成本每季降 15%",
        "output": "「知源」系列大模型（7B/32B/236B-MoE），授权与 API 收入",
        "revenue": 5200.0, "gross": 0.51,
        "staff": [
            {"name": "周慕之", "post": "院长", "level": "M5", "since": "2019-04", "salary": 8.0, "perf": "A", "fire_note": "不能动：整个技术盘子是她撑着的"},
            {"name": "韩度", "post": "预训练组负责人", "level": "M3", "since": "2020-05", "salary": 6.5, "perf": "B", "fire_note": "可以动：上一轮 236B 训练崩了两次，损失 900 万卡时"},
            {"name": "叶轻舟", "post": "后训练组负责人", "level": "M2", "since": "2021-07", "salary": 4.8, "perf": "A", "fire_note": "留着：对齐和工具调用是她最拿得出手的活"},
            {"name": "屠鸣", "post": "推理优化负责人", "level": "M2", "since": "2021-02", "salary": 5.2, "perf": "C", "fire_note": "可以开：量化方案拖了两个季度，竞品早就上了"},
        ],
        "recruit": [
            {"post": "MoE 训练工程师", "level": "P7", "salary": "4.5~6.5", "need": 4, "cycle": "70 天", "why": "下一代基座走稀疏路线，没人真跑过万卡 MoE"},
            {"post": "多模态算法工程师", "level": "P6", "salary": "3.0~4.5", "need": 3, "cycle": "60 天", "why": "视频理解这块被客户追着要"},
        ],
    },
    {
        "id": "silicon", "name": "芯片部", "short": "芯片",
        "duty": "自研推理卡「知源一号」、加速整机、板卡与散热设计、流片与量产导入",
        "head": "程一苇", "head_note": "硬件出身，认死理，为了一颗电容能跟供应商吵三天",
        "teams": [
            {"name": "架构组", "duty": "指令集、互联、HBM 选型"},
            {"name": "后端与验证组", "duty": "综合、时序、DFT、验证"},
            {"name": "整机组", "duty": "板卡、散热、电源、结构"},
            {"name": "量产组", "duty": "封测、良率、供应链导入"},
        ],
        "headcount": 540, "onboard": 505, "band": "1.2~7.0", "budget": 3400,
        "kpi": "流片一次成功，整机交付良率 ≥97%",
        "output": "知源一号（28nm，单卡 96T INT8）、训推一体整机",
        "revenue": 3000.0, "gross": 0.29,
        "staff": [
            {"name": "程一苇", "post": "硬件部总经理", "level": "M5", "since": "2020-01", "salary": 7.0, "perf": "A", "fire_note": "不能动：知源一号是他从纸面做到量产的"},
            {"name": "常骁", "post": "后端负责人", "level": "M3", "since": "2021-03", "salary": 5.0, "perf": "B", "fire_note": "可以用：时序收敛靠外包救过一次"},
            {"name": "苏离", "post": "量产经理", "level": "M2", "since": "2022-01", "salary": 3.2, "perf": "C", "fire_note": "可以开：封测厂排产被他压错，交期延后两周"},
        ],
        "recruit": [
            {"post": "SoC 验证工程师", "level": "P7", "salary": "3.5~5.5", "need": 3, "cycle": "75 天", "why": "二代卡验证人手不够，靠外部团队一天烧 3 万"},
        ],
    },
    {
        "id": "cloud", "name": "云平台", "short": "云运营",
        "duty": "推理云平台、SRE、计费与结算、客户工单、可用性保障",
        "head": "路遥", "head_note": "运营出身，脾气好，情绪稳定到不像人",
        "teams": [
            {"name": "平台组", "duty": "控制台、计量、配额、账单"},
            {"name": "SRE 组", "duty": "监控、容量、故障复盘"},
            {"name": "客户支持组", "duty": "工单、值班、SLA 赔付"},
        ],
        "headcount": 330, "onboard": 310, "band": "0.8~3.6", "budget": 1300,
        "kpi": "推理 API 月度可用性 ≥99.9%，工单首响 ≤15 分钟",
        "output": "推理 API 与私有云订阅",
        "revenue": 2400.0, "gross": 0.46,
        "staff": [
            {"name": "路遥", "post": "运营部总经理", "level": "M4", "since": "2020-06", "salary": 3.6, "perf": "A", "fire_note": "不能动：计量计费这条线换人就出账"},
            {"name": "文竹", "post": "SRE 负责人", "level": "M2", "since": "2021-11", "salary": 2.6, "perf": "B", "fire_note": "可以用：上个月两次 P2 故障复盘写得敷衍"},
            {"name": "石见", "post": "客户支持主管", "level": "P6", "since": "2022-02", "salary": 1.3, "perf": "C", "fire_note": "可以开：大客户投诉三次超时未回"},
        ],
        "recruit": [
            {"post": "SRE 工程师", "level": "P6", "salary": "1.8~2.8", "need": 4, "cycle": "45 天", "why": "推理流量翻了三倍，值班表排不开"},
        ],
    },
    {
        "id": "solution", "name": "方案部", "short": "解决方案",
        "duty": "政企/金融/制造/能源行业方案、售前、交付与验收、招投标",
        "head": "尤四海", "head_note": "做了十五年政企单，酒桌上能把事谈成",
        "teams": [
            {"name": "政企组", "duty": "省市平台、国资、政务云"},
            {"name": "金融组", "duty": "银行、保险、券商的风控与客服模型"},
            {"name": "制造与能源组", "duty": "质检、排产、巡检、电网负荷预测"},
            {"name": "交付组", "duty": "实施、验收、回款推进"},
        ],
        "headcount": 580, "onboard": 540, "band": "1.0~4.5", "budget": 1900,
        "kpi": "中标率 ≥32%，验收后 90 天回款率 ≥80%",
        "output": "行业项目合同（含三年运维）",
        "revenue": 4000.0, "gross": 0.38,
        "staff": [
            {"name": "尤四海", "post": "事业部总经理", "level": "M5", "since": "2019-09", "salary": 4.5, "perf": "A", "fire_note": "不能动：省里的几个大单都是他的人脉"},
            {"name": "苗青禾", "post": "金融组负责人", "level": "M2", "since": "2021-04", "salary": 3.0, "perf": "B", "fire_note": "可以用：一家城商行的验收拖了半年，回款没跟上"},
            {"name": "齐国安", "post": "交付经理", "level": "P6", "since": "2020-10", "salary": 1.8, "perf": "C", "fire_note": "可以开：两个项目验收资料不全，被扣了 40 万尾款"},
        ],
        "recruit": [
            {"post": "能源行业解决方案专家", "level": "M2", "salary": "2.8~3.8", "need": 2, "cycle": "60 天", "why": "电网这块是新盘子，现在靠借人"},
        ],
    },
    {
        "id": "marketing", "name": "市场部", "short": "市场",
        "duty": "品牌、发布会、内容与社区、渠道与生态、活动",
        "head": "俞听澜", "head_note": "市场总监，做传播出身，场面话一套一套",
        "teams": [
            {"name": "品牌组", "duty": "定位、视觉、对外口径"},
            {"name": "内容与社区组", "duty": "公众号、开发者社区、技术博客、开源运营"},
            {"name": "渠道与生态组", "duty": "集成商、ISV、云市场"},
        ],
        "headcount": 150, "onboard": 140, "band": "0.9~3.5", "budget": 900,
        "kpi": "线索量季度增长 ≥20%，活动 ROI ≥1.8",
        "output": "线索与品牌，间接支撑签单",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "俞听澜", "post": "市场总监", "level": "M3", "since": "2021-05", "salary": 3.5, "perf": "B", "fire_note": "可以用：发布会花了 380 万，线索没接住"},
            {"name": "季小满", "post": "社区负责人", "level": "P6", "since": "2022-08", "salary": 1.6, "perf": "A", "fire_note": "留着：开发者社区是她做起来的，动了她就散"},
            {"name": "费无名", "post": "渠道经理", "level": "P5", "since": "2023-02", "salary": 1.2, "perf": "C", "fire_note": "可以开：渠道返点算错，被集成商投诉"},
        ],
        "recruit": [],
    },
    {
        "id": "success", "name": "客成部", "short": "客户成功",
        "duty": "大客户续约、增购、赋能培训、NPS 与流失预警",
        "head": "于归", "head_note": "带过客服团队，客户骂人她还能笑着谈",
        "teams": [
            {"name": "大客户组", "duty": "Top20 客户的经营与续约"},
            {"name": "赋能组", "duty": "培训、最佳实践、方案复用"},
        ],
        "headcount": 130, "onboard": 122, "band": "0.8~2.8", "budget": 460,
        "kpi": "续约率 ≥88%，NPS ≥45",
        "output": "续约与增购，直接落在存量收入上",
        "revenue": 1600.0, "gross": 0.62,
        "staff": [
            {"name": "于归", "post": "客户成功总监", "level": "M3", "since": "2021-07", "salary": 2.8, "perf": "A", "fire_note": "不能动：前二十个客户她一个个谈下来的"},
            {"name": "李知白", "post": "大客户经理", "level": "P6", "since": "2022-05", "salary": 1.8, "perf": "C", "fire_note": "可以开：两个客户流失，事前一次预警都没报"},
        ],
        "recruit": [
            {"post": "客户成功经理", "level": "P5", "salary": "1.2~1.8", "need": 3, "cycle": "30 天", "why": "续约季快到了，人均带 18 家太多"},
        ],
    },
    {
        "id": "supply", "name": "供应链", "short": "供应链",
        "duty": "服务器与网络设备采购、封测与代工、物流仓储、供应商管理",
        "head": "万元朗", "head_note": "采购老手，压价狠，供应商见他都头疼",
        "teams": [
            {"name": "设备采购组", "duty": "GPU/CPU/交换机/线缆"},
            {"name": "代工与封测组", "duty": "流片、封测、整机代工"},
            {"name": "仓储物流组", "duty": "备件库、调拨、清关"},
        ],
        "headcount": 190, "onboard": 178, "band": "0.8~3.2", "budget": 720,
        "kpi": "采购降本 ≥5%/年，到货准时率 ≥95%",
        "output": "成本与供应保障",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "万元朗", "post": "采购总监", "level": "M3", "since": "2020-04", "salary": 3.2, "perf": "A", "fire_note": "不能动：H200 那批货是他抢回来的"},
            {"name": "屈小乙", "post": "设备采购经理", "level": "P6", "since": "2021-12", "salary": 1.7, "perf": "C", "fire_note": "可以开：一家供应商没走比价，价差 12%"},
        ],
        "recruit": [
            {"post": "关务专员", "level": "P4", "salary": "0.9~1.3", "need": 1, "cycle": "25 天", "why": "进口设备清关老压箱，罚款吃了两次"},
        ],
    },
    {
        "id": "security", "name": "安全部", "short": "安全",
        "duty": "网络安全、数据安全、模型安全与内容合规、应急响应、等保",
        "head": "聂行舟", "head_note": "安全负责人，话少，红队出身",
        "teams": [
            {"name": "攻防组", "duty": "渗透、红蓝对抗、漏洞管理"},
            {"name": "数据安全组", "duty": "分级分类、脱敏、审计"},
            {"name": "模型安全组", "duty": "越狱防护、内容风控、评测"},
        ],
        "headcount": 105, "onboard": 98, "band": "1.0~4.0", "budget": 380,
        "kpi": "重大安全事件零发生，等保测评一次过",
        "output": "合规与兜底",
        "revenue": 0.0, "gross": 0.0,
        "staff": [
            {"name": "聂行舟", "post": "安全总监", "level": "M3", "since": "2021-02", "salary": 4.0, "perf": "A", "fire_note": "不能动：等保和政企安全审查都认他"},
            {"name": "凌可", "post": "模型安全负责人", "level": "P7", "since": "2022-09", "salary": 2.4, "perf": "B", "fire_note": "可以用：越狱样本库更新慢，被客户抓到一次"},
        ],
        "recruit": [
            {"post": "数据安全工程师", "level": "P6", "salary": "2.0~3.0", "need": 2, "cycle": "45 天", "why": "分类分级今年要落地，人手不够"},
        ],
    },
]

# ── 集团经营（月度，万元）────────────────────────────────────────────────
FINANCE = {
    "revenue_total": 26000.0,
    "gross_total": 0.312,
    "cost": {
        "人力": 5200.0,
        "算力与电力": 6200.0,
        "机房与折旧": 2400.0,
        "供应链与硬件": 5800.0,
        "市场与差旅": 900.0,
        "研发外采与标注": 700.0,
        "其他管理": 400.0,
    },
    "op_profit": 3000.0,
    "net_profit": 2400.0,
    "cash": 26000.0,
    "receivable": 9800.0,
    "payable": 4600.0,
    "credit_line": 50000.0,
    "credit_used": 12000.0,
    "note": "算力租赁与模型授权是现金牛；行业项目回款慢、账期长，别把现金全压在上面。",
}



# ── 在册名册（抽样）────────────────────────────────────────────────
_NAMES_A = ("周吴郑冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜")
_NAMES_B = ("嘉言亦舟致远书宁知行清和问渠长风若谷时雨南星景明令仪予怀怀瑾明夷见山临川"
            "文竹叶舟子墨沐白雨桐照雪思远立行慎言守拙")

POSTS = {
    "office": ["战略专员", "秘书", "督办专员", "政府事务专员"],
    "finance": ["会计", "资金专员", "税务专员", "经营分析"],
    "hr": ["招聘专员", "薪酬专员", "培训专员", "员工关系"],
    "legal": ["合同律师", "知产律师", "合规专员"],
    "audit": ["内控专员", "审计员"],
    "idc": ["运维工程师", "电力工程师", "液冷工程师", "调度员", "值班班长"],
    "research": ["算法工程师", "训练工程师", "数据工程师", "评测工程师", "推理优化"],
    "silicon": ["验证工程师", "后端工程师", "整机工程师", "量产工程师"],
    "cloud": ["SRE", "平台开发", "客服专员", "计费专员"],
    "solution": ["售前顾问", "交付经理", "行业专家", "投标专员"],
    "marketing": ["品牌专员", "内容运营", "渠道经理"],
    "success": ["客户成功经理", "赋能顾问"],
    "supply": ["采购专员", "关务专员", "仓储主管"],
    "security": ["安全工程师", "渗透测试", "数据安全"],
}
LEVELS = ("P4", "P5", "P6", "P7", "M1")


def roster(dept_id: str, limit: int = 0) -> List[Dict[str, Any]]:
    """按部门生成在册名单（确定性：同一部门每次一样）。

    只生成抽样，不是全部：面板上要的是「像真的名册」，不是三千行表格。
    """
    import hashlib as _hl
    d = None
    for x in DEPARTMENTS:
        if x["id"] == dept_id:
            d = x
            break
    if not d:
        return []
    hc = int(d["onboard"] or 0)
    n = limit or max(4, min(14, hc // 50 + 3))
    posts = POSTS.get(dept_id) or ["工程师"]
    rows = []
    for i in range(n):
        seed = _hl.md5(("%s-%d" % (dept_id, i)).encode()).hexdigest()
        name = _NAMES_A[int(seed[0:2], 16) % len(_NAMES_A)] + _NAMES_B[int(seed[2:4], 16) % len(_NAMES_B)]
        rows.append({
            "name": name,
            "post": posts[int(seed[4:6], 16) % len(posts)],
            "level": LEVELS[int(seed[6:8], 16) % len(LEVELS)],
            "perf": ("A", "B", "B", "C")[int(seed[8:10], 16) % 4],
            "dept": d["name"], "dept_id": d["id"],
            "since": "20%02d" % (17 + int(seed[10:12], 16) % 9),
        })
    return rows



def _merge_bank(row: Dict[str, Any]) -> Dict[str, Any]:
    """把银行侧的授信数据挂到集团报表上（由调用方传入最新值再返回）。"""
    row["credit_available"] = round(
        max(0.0, float(row.get("credit_line", 0)) - float(row.get("credit_used", 0))), 2
    )
    return row


def group() -> Dict[str, Any]:
    return dict(GROUP)


def departments() -> List[Dict[str, Any]]:
    return [dict(d) for d in DEPARTMENTS]


def dept(key: str) -> Optional[Dict[str, Any]]:
    if not key:
        return None
    key = str(key).strip()
    for d in DEPARTMENTS:
        if key in (d["id"], d["name"], d["short"]) or key in d["name"]:
            return dict(d)
    return None


def org_tree() -> Dict[str, Any]:
    """给面板/上下文用的整体架构树。"""
    tree = {
        "group": dict(GROUP),
        "seats": {
            "董事长": GROUP["chair"],
            "常务副总裁": GROUP["vice"][0],
            "高级副总裁": GROUP["vice"][1],
            "CFO": dept("finance")["head"],
            "CHO": dept("hr")["head"],
        },
        "departments": [
            {
                "id": d["id"], "name": d["name"], "head": d["head"],
                "teams": [t["name"] for t in d["teams"]],
                "headcount": d["headcount"], "onboard": d["onboard"],
                "kpi": d["kpi"], "revenue": d["revenue"], "gross": d["gross"],
                "recruit": len(d["recruit"]),
            }
            for d in DEPARTMENTS
        ],
        "total_headcount": sum(d["headcount"] for d in DEPARTMENTS),
        "total_onboard": sum(d["onboard"] for d in DEPARTMENTS),
    }
    return tree


def staff(key: str) -> List[Dict[str, Any]]:
    d = dept(key)
    if not d:
        return []
    out = []
    for s in d["staff"]:
        row = dict(s)
        row["dept"] = d["name"]
        # 能不能动，一眼能看出来
        row["fireable"] = row["fire_note"].startswith(("可以", "能用", "可以用", "可以动", "可以开"))
        out.append(row)
    return out


def fireable(key: str = "") -> List[Dict[str, Any]]:
    """列出可以开除的人（不传部门就全集团）。"""
    rows: List[Dict[str, Any]] = []
    targets = [dept(key)] if key else DEPARTMENTS
    for d in targets:
        if not d:
            continue
        for s in d["staff"]:
            note = s["fire_note"]
            if note.startswith(("可以", "能用")):
                rows.append({
                    "dept": d["name"], "name": s["name"], "post": s["post"],
                    "level": s["level"], "salary": s["salary"],
                    "perf": s["perf"], "why": note,
                    "severance": round(float(s["salary"]) * _severance_months(s), 2),
                })
    return rows


def _severance_months(s: Dict[str, Any]) -> int:
    """N+1：按入职年份粗算工龄。"""
    try:
        since = int(str(s.get("since", "2020"))[:4])
    except Exception:
        since = 2020
    years = max(1, 2026 - since)
    return years + 1


def recruit_plan(key: str = "") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    targets = [dept(key)] if key else DEPARTMENTS
    for d in targets:
        if not d:
            continue
        for r in d["recruit"]:
            row = dict(r)
            row["dept"] = d["name"]
            rows.append(row)
    return rows


def hire(key: str, post: str = "") -> Dict[str, Any]:
    """招聘一人：返回成本与影响（真正的扣款由调用方做）。"""
    d = dept(key)
    if not d:
        return {"ok": False, "msg": "没有这个部门"}
    plan = d["recruit"]
    if not plan:
        return {"ok": False, "msg": "%s 目前没有在招岗位" % d["name"]}
    pick = plan[0]
    if post:
        for p in plan:
            if post in p["post"]:
                pick = p
                break
    salary = str(pick["salary"])
    low = salary.split("~")[0] if "~" in salary else salary
    try:
        monthly = float(low)
    except Exception:
        monthly = 1.5
    return {
        "ok": True, "dept": d["name"], "post": pick["post"], "level": pick["level"],
        "salary": salary, "cycle": pick["cycle"], "why": pick["why"],
        "cost_first_month": round(monthly * 1.6, 2),   # 工资 + 社保公积金 + 猎头/安置
        "onboard_after": pick["cycle"],
    }


def fire(key: str, name: str) -> Dict[str, Any]:
    """开除一个人：返回赔偿与连带影响（扣款由调用方做）。"""
    d = dept(key) if key else None
    pool = [d] if d else DEPARTMENTS
    for dd in pool:
        if not dd:
            continue
        for s in dd["staff"]:
            if name and name in s["name"]:
                if not s["fire_note"].startswith(("可以", "能用")):
                    return {"ok": False, "msg": "%s 不是能随便动的人：%s" % (s["name"], s["fire_note"])}
                months = _severance_months(s)
                return {
                    "ok": True, "dept": dd["name"], "name": s["name"], "post": s["post"],
                    "monthly": s["salary"], "months": months,
                    "severance": round(float(s["salary"]) * months, 2),
                    "risk": _fire_risk(s),
                    "why": s["fire_note"],
                }
    return {"ok": False, "msg": "名册里没有这个人"}


def _fire_risk(s: Dict[str, Any]) -> str:
    if s["perf"] == "A":
        return "有留人风险：绩效 A，外面接得住"
    if s["perf"] == "B":
        return "低：绩效中等，交接两周能完"
    return "很低：绩效 C，早该动"


def report() -> Dict[str, Any]:
    """集团月度经营报表。"""
    row = dict(FINANCE)
    row["cost_total"] = round(sum(row["cost"].values()), 2)
    row["headcount"] = sum(d["headcount"] for d in DEPARTMENTS)
    row["onboard"] = sum(d["onboard"] for d in DEPARTMENTS)
    row["vacancy"] = row["headcount"] - row["onboard"]
    row["revenue_by_dept"] = [
        {"dept": d["name"], "revenue": d["revenue"], "gross": d["gross"]}
        for d in DEPARTMENTS if d["revenue"] > 0
    ]
    row["margin"] = round(100.0 * row["net_profit"] / row["revenue_total"], 1)
    return _merge_bank(row)


if __name__ == "__main__":  # 自检：python3 company.py
    import json
    r = report()
    print(json.dumps({k: r[k] for k in ("revenue_total", "cost_total", "net_profit", "margin", "headcount", "vacancy", "credit_available")},
                     ensure_ascii=False, indent=1))
    print("部门数:", len(departments()), "可开除:", len(fireable()), "在招:", len(recruit_plan()))
