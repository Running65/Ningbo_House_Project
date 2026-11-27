# -*- coding: utf-8 -*-
"""成员B 第二周交付物：field_stats.py

按《member_B.md》第2周任务的要求，对成员A采集的原始数据做字段级统计核查：
统计每个字段的缺失值、重复值、取值分布，并对面积、总价、单价等
核心字段做数值抽取与一致性校验，为「原始数据质量检查表」提供数据。

运行方式（在项目根目录下）：
    python analysis/field_stats.py
"""

import pandas as pd

RAW_DATA_PATH = "data/raw/raw_data.csv"


def main():
    df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig")
    total = len(df)
    print(f"总行数：{total}，字段数：{df.shape[1]}")

    # 1. 各字段基础统计：缺失、重复、唯一值个数
    print("\n===== 各字段缺失 / 重复 / 唯一值统计 =====")
    for col in df.columns:
        miss = df[col].isnull().sum()
        uniq = df[col].nunique(dropna=True)
        # 该字段重复指：同一字段取值相同的行数（不含缺失）
        dup = df[col].dropna().duplicated().sum()
        print(f"{col}\t缺失={miss}({miss/total:.1%})\t唯一值={uniq}\t取值重复行={dup}")

    # 2. 整行重复与主键重复
    print("\n===== 重复检查 =====")
    print(f"整行完全重复：{df.duplicated().sum()} 条")
    print(f"房源链接重复：{df['房源链接'].duplicated().sum()} 条")
    key = ["小区名", "行政区", "户型", "面积", "楼层", "总价(万)"]
    print(f"小区+行政区+户型+面积+楼层+总价 组合重复：{df.duplicated(subset=key).sum()} 条")

    # 3. 分类字段的取值分布
    for col in ["行政区", "户型", "朝向", "楼层", "发布时间"]:
        print(f"\n===== {col} 取值分布 =====")
        print(df[col].value_counts(dropna=False).head(12))

    # 4. 数值字段抽取与校验
    area = df["面积"].str.replace("平米", "", regex=False).str.strip().astype(float)
    total_w = df["总价(万)"].astype(float)
    unit = df["单价(元/平)"].str.replace(",", "", regex=False).str.strip().astype(float)
    focus = df["关注数"].str.replace("人关注", "", regex=False).str.strip().astype(float)

    print("\n===== 核心数值字段描述统计（清洗后） =====")
    stats = pd.DataFrame({"面积(平米)": area, "总价(万)": total_w, "单价(元/平)": unit, "关注数": focus}).describe()
    print(stats.round(2).to_string())

    print("\n===== 合法性校验 =====")
    print(f"面积 <=0 的行：{(area <= 0).sum()}")
    print(f"总价 <=0 的行：{(total_w <= 0).sum()}")
    print(f"单价 <=0 的行：{(unit <= 0).sum()}")
    print(f"关注数 <0 的行：{(focus < 0).sum()}")

    # 5. 单价一致性：总价*10000/面积 与 采集单价 的相对偏差
    calc_unit = total_w * 10000 / area
    diff = ((calc_unit - unit).abs() / unit).round(4)
    print("\n===== 单价一致性（总价×10000÷面积 vs 采集单价） =====")
    print(f"偏差>1%的行：{(diff > 0.01).sum()} 条；>5% 的行：{(diff > 0.05).sum()} 条")
    print(f"偏差中位数：{diff.median():.2%}")

    print("\n统计完成。详细结论见 docs/ 原始数据质量检查表_成员B.md 与 字段统计结果_成员B.md")


if __name__ == "__main__":
    main()
