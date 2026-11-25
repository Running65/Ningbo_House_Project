# -*- coding: utf-8 -*-
"""成员B 第一周交付物： beginner_test.py

按《第一周任务》6.2/6.3 的要求，完成对原始数据的最基本质量检查：
读取 data/raw/raw_data.csv，显示前5行、字段信息，
统计每个字段的缺失值数量和重复行数量。

运行方式（在项目根目录下）：
    python analysis/beginner_test.py
"""

import pandas as pd

# 原始数据路径（相对项目根目录）
RAW_DATA_PATH = "data/raw/raw_data.csv"


def main():
    # 1. 读取 CSV（文件带 BOM，用 utf-8-sig 读取，避免表头出现乱码前缀）
    df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig")
    print(f"成功读取：{RAW_DATA_PATH}")

    # 2. 显示前 5 行
    print("\n===== 前 5 行数据 =====")
    print(df.head())

    # 3. 显示字段信息（字段类型、非空数量）
    print("\n===== 字段信息 df.info() =====")
    df.info()

    # 4. 数值字段的描述统计
    print("\n===== 数值字段描述统计 df.describe() =====")
    print(df.describe())

    # 5. 统计每个字段的缺失值数量
    print("\n===== 各字段缺失值数量 =====")
    print(df.isnull().sum())

    # 6. 统计重复行数量
    print("\n===== 重复行数量 =====")
    print(df.duplicated().sum())

    print("\n检查完成。详细结论见 docs/数据质量报告_成员B.md")


if __name__ == "__main__":
    main()
