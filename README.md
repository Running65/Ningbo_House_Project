# Ningbo_House_Project

**宁波市二手房市场价格分析与可视化研究**（期末课程小组作业 · 方向 C：城市二手房市场价格洞察）

本项目采集宁波市二手房挂牌房源数据，经清洗与统计分析后，用 Pyecharts 制作可视化大屏，洞察宁波各行政区的房价水平、总价分布、面积-单价关系，并筛选高性价比房源。

## 成员分工

| 成员 | 角色 | 主要职责 |
|---|---|---|
| A | 项目负责人 + 数据采集工程师 | 数据采集、项目统筹、Git 管理、文件整合 |
| B | 数据清洗与分析工程师 | 数据清洗、统计分析、性价比筛选、报告分析 |
| C | 可视化与前端工程师 | Pyecharts 图表、大屏布局、交互、演示录屏 |

## 项目结构

```
Ningbo_House_Project/
├── data/
│   ├── raw/raw_data.csv          # 原始数据（1195 条，12 字段）
│   └── processed/                # 清洗后数据（B 第3周产出）
├── spider/                       # 数据采集爬虫
│   ├── spider_region.py          # 主爬虫：按行政区筛选采集
│   ├── spider_cdp.py             # CDP 接管真实 Chrome 采集
│   ├── spider_beike.py           # 贝壳版（Playwright + 登录）
│   └── spider.py                 # 早期 requests 版（链家，参考）
├── analysis/                     # 分析与清洗
│   ├── beginner_test.py          # 数据质量检查（B）
│   ├── dashboard_stats.py        # 大屏真实统计值计算（C）
│   ├── clean.py / analysis.py    # 清洗与分析（B 第3、4周产出）
│   └── gen_geo_js.py             # 行政区地图数据生成（C）
├── visualization/                # 可视化大屏
│   ├── page_demo.html / tab_demo.html   # 大屏（Page/Tab 布局）
│   ├── real_data.js              # 大屏真实数据（自动生成）
│   └── ningbo_geo.js             # 宁波行政区地图（自动生成）
├── docs/                         # 项目文档
├── demo/                         # 环境测试
├── member_A.md / member_B.md / member_C.md   # 成员任务文档
├── README.md
├── requirements.txt
└── .gitignore
```

## 数据说明

| 项目 | 说明 |
|---|---|
| 数据源 | 贝壳找房 · 宁波站（`nb.ke.com/ershoufang/`）|
| 数据规模 | 1195 条，覆盖宁波 11 个行政区 |
| 字段 | 12 个（标题、小区名、行政区、户型、面积、朝向、楼层、总价、单价、关注数、发布时间、房源链接）|
| 数据质量 | 仅楼层 30 条缺失（来源端），总价≈面积×单价一致性 0 偏差 |

> 详细说明见 `docs/数据来源说明_成员A.md`、`docs/数据字段说明.md`、`docs/数据质量检查记录_成员A.md`。

## 环境准备

```bash
pip install -r requirements.txt
```

## 环境测试

```bash
python demo/test_libraries.py
```

## 数据采集（如需重新采集）

数据采集需要登录贝壳账号，用真实 Chrome 采集：

```bash
# 1. 启动带调试端口的 Chrome（首次）
#    Chrome 地址栏登录贝壳后，运行：
python spider/spider_region.py    # 按行政区采集（11 区 × 4 页 ≈ 1195 条）
```

> 采集过程会触发人机验证，需人工在浏览器中完成。详细方案见 `docs/数据来源说明_成员A.md`。

## 文档索引

| 文档 | 说明 |
|---|---|
| [六周计划](docs/六周计划.md) | 权威 6 周进度计划 |
| [协作规范](docs/协作规范.md) | 小组协作与 Git 规范 |
| [数据来源说明](docs/数据来源说明_成员A.md) | 数据怎么来的 |
| [数据字段说明](docs/数据字段说明.md) | 12 个字段详解 |
| [数据质量检查记录](docs/数据质量检查记录_成员A.md) | A 的质量自检结论 |
| [数据字段设计表](docs/数据字段设计表_成员B.md) | B 的字段设计与清洗约定 |
| [数据质量报告](docs/数据质量报告_成员B.md) | B 的质量检查结论 |
| [图表设计清单](docs/图表设计清单_成员C.md) | C 的 6 类图表设计 |
| AI 协作日志（[A](docs/AI协作日志_成员A.md) / [B](docs/AI协作日志_成员B.md) / [C](docs/AI协作日志_成员C.md)）| 各成员排错记录 |

## 当前进度

- 第 1 周（项目立项）✅ 完成（除立项 PPT）
- 第 2 周（数据采集）✅ 完成（1195 条）
- 第 3 周（数据质量检查）✅ A 完成；B 数据清洗进行中
- 第 4 周（大屏数据支持 / 图表数据分析）进行中（C 已接真实数据 + 行政区地图）
