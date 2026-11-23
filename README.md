# Ningbo_House_Project

期末课程小组作业

宁波房产数据分析项目。

## 项目结构

```
Ningbo_House_Project/
├── data/
│   ├── raw/           # 原始数据
│   └── processed/     # 处理后的数据
├── spider/
│   └── spider.py      # 爬虫脚本
├── analysis/
│   ├── clean.py       # 数据清洗
│   └── analysis.py    # 数据分析
├── visualization/
│   ├── charts.py      # 图表
│   └── dashboard.py   # 数据看板
├── docs/              # 文档
├── demo/
│   └── test_libraries.py  # 环境测试脚本
├── README.md
├── requirements.txt
└── .gitignore
```

## 环境准备

```bash
pip install -r requirements.txt
```

## 环境测试

```bash
python demo/test_libraries.py
```
