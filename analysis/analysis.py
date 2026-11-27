# -*- coding: utf-8 -*-
"""成员B 第四周交付物：analysis.py

按《member_B.md》第4周任务，基于第3周清洗后的 clean_data.csv 做图表数据分析：
    1. 统计各行政区平均单价（均值 + 中位数）；
    2. 统计不同总价区间的房源数量；
    3. 计算面积与单价、面积与总价的相关性；
    4. 分析不同区域房价分布（四分位数，供箱线图使用）；
    5. 建立高性价比房源筛选规则并输出筛选结果；
    6. 向成员C输出图表统计数据（data/processed/chart_stats/）。

运行方式（在项目根目录下）：
    python analysis/analysis.py
"""

import os

import pandas as pd

CLEAN_DATA_PATH = "data/processed/clean_data.csv"
OUT_DIR = "data/processed/chart_stats"
VFM_PATH = "data/processed/value_for_money.csv"


def region_price(df):
    """1. 各行政区平均单价（均值降序），输出给柱状图/地图。"""
    stats = (
        df.groupby("行政区")["单价(元/平)"]
        .agg(["count", "mean", "median"])
        .round(0)
        .sort_values("mean", ascending=False)
    )
    stats.to_csv(f"{OUT_DIR}/region_price.csv", encoding="utf-8-sig")
    print("===== 1. 各行政区平均单价 =====")
    print(stats.to_string())
    return stats


def price_bins(df):
    """2. 总价区间分布，输出给饼图/柱状图。"""
    bins = [0, 50, 100, 150, 200, 300, float("inf")]
    labels = ["50万以下", "50-100万", "100-150万", "150-200万", "200-300万", "300万以上"]
    cut = pd.cut(df["总价(万)"], bins=bins, labels=labels, right=False)
    stats = cut.value_counts().reindex(labels)
    stats.rename("房源数量").to_csv(f"{OUT_DIR}/price_bins.csv", encoding="utf-8-sig")
    print("\n===== 2. 总价区间分布 =====")
    print(stats.to_string())
    return stats


def correlations(df):
    """3. 相关性，输出给散点图说明。"""
    r_area_unit = df["面积(平米)"].corr(df["单价(元/平)"])
    r_area_total = df["面积(平米)"].corr(df["总价(万)"])
    print("\n===== 3. 相关性 =====")
    print(f"面积-单价 Pearson r = {r_area_unit:.3f}")
    print(f"面积-总价 Pearson r = {r_area_total:.3f}")
    return r_area_unit, r_area_total


def region_distribution(df):
    """4. 各区域单价四分位数，输出给箱线图。"""
    stats = (
        df.groupby("行政区")["单价(元/平)"]
        .describe()[["count", "min", "25%", "50%", "75%", "max"]]
        .round(0)
    )
    stats.to_csv(f"{OUT_DIR}/region_distribution.csv", encoding="utf-8-sig")
    print("\n===== 4. 各区域单价分布（箱线图数据） =====")
    print(stats.to_string())
    return stats


def value_for_money(df):
    """5. 高性价比房源筛选。

    规则（在报告中说明理由）：
    a. 单价 ≤ 所在行政区单价的 85%（低于区域均价至少一成五，保证「比区域便宜」）；
    b. 面积在 80~140 平米之间（主力改善户型，避免面积太小拉低单价的假便宜）；
    c. 关注数 ≥ 全体房源关注数的中位数（市场关注度作交叉验证）。
    满足全部三条记为高性价比房源。
    """
    df = df.copy()
    df["区域单价中位数"] = df.groupby("行政区")["单价(元/平)"].transform("median").round(0)
    med_focus = df["关注数(人)"].median()
    rule_a = df["单价(元/平)"] <= df["区域单价中位数"] * 0.85
    rule_b = df["面积(平米)"].between(80, 140)
    rule_c = df["关注数(人)"] >= med_focus
    df["高性价比"] = rule_a & rule_b & rule_c

    result = (
        df.loc[df["高性价比"],
               ["小区名", "行政区", "户型", "面积(平米)", "总价(万)", "单价(元/平)",
                "区域单价中位数", "关注数(人)", "房源链接"]]
        .sort_values(["行政区", "单价(元/平)"])
    )
    result.to_csv(VFM_PATH, index=False, encoding="utf-8-sig")
    print("\n===== 5. 高性价比房源筛选 =====")
    print(f"筛选规则：a) 单价≤区域中位数的85%  b) 面积80~140平米  c) 关注数≥中位数({med_focus:.0f}人)")
    print(f"满足条件的房源：{len(result)} 条，已输出 {VFM_PATH}")
    print(result.head(10).drop(columns=["房源链接"]).to_string(index=False))
    return result


def main():
    df = pd.read_csv(CLEAN_DATA_PATH, encoding="utf-8-sig")
    print(f"读取清洗后数据：{CLEAN_DATA_PATH}，{len(df)} 行")
    os.makedirs(OUT_DIR, exist_ok=True)

    region_price(df)
    price_bins(df)
    correlations(df)
    region_distribution(df)
    value_for_money(df)

    print("\n图表统计数据已输出至 data/processed/chart_stats/（region_price.csv、"
          "price_bins.csv、region_distribution.csv），性价比结果 value_for_money.csv")


if __name__ == "__main__":
    main()
