# -*- coding: utf-8 -*-
"""成员B 第三周交付物：clean.py

按《member_B.md》第3周任务和《六周计划》数据清洗要求，对原始数据做清洗：
    1. Pandas 读取 CSV，info()/describe() 探查；
    2. 正则/字符串方式提取数值，统一字段类型；
    3. 删除重复记录（整行重复 + 主键「房源链接」重复）；
    4. 处理缺失值（仅「楼层」有 2.5% 缺失，保留缺失不填补——楼层层级
       无法从其他字段可靠推断，随意填补会引入错误信息）；
    5. 异常值：对「总价(万)」用 IQR（四分位距）法识别并剔除，
       规则为 < Q1-1.5*IQR 或 > Q3+1.5*IQR，理由是高价长尾会显著
       拉偏均值，影响后续区域均价统计的稳健性。
输出 data/processed/clean_data.csv，并打印 EDA 初步统计。

运行方式（在项目根目录下）：
    python analysis/clean.py
"""

import pandas as pd

RAW_DATA_PATH = "data/raw/raw_data.csv"
CLEAN_DATA_PATH = "data/processed/clean_data.csv"


def load_and_explore(path):
    """读取并探查原始数据。"""
    df = pd.read_csv(path, encoding="utf-8-sig")
    print("===== 原始数据探查 =====")
    print(f"原始行数：{len(df)}，字段数：{df.shape[1]}")
    df.info()
    print(df.describe().round(2).to_string())
    return df


def extract_numeric(df):
    """正则/字符串提取数值，统一字段类型。"""
    df = df.copy()
    # 面积：去掉「平米」转 float
    df["面积(平米)"] = (
        df["面积"].str.replace(r"平米", "", regex=True).str.strip().astype(float)
    )
    # 单价：去掉千位逗号转 int
    df["单价(元/平)"] = (
        df["单价(元/平)"].str.replace(r"[,，]", "", regex=True).str.strip().astype(int)
    )
    # 关注数：提取数字
    df["关注数(人)"] = (
        df["关注数"].str.replace(r"人关注", "", regex=True).str.strip().astype(int)
    )
    # 户型：正则提取「X室Y厅」的室、厅数量
    rooms = df["户型"].str.extract(r"(\d+)室(\d+)厅")
    df["室"] = rooms[0].astype(int)
    df["厅"] = rooms[1].astype(int)
    return df


def clean(df):
    """去重、缺失值、异常值处理，返回清洗后的 DataFrame 和处理统计。"""
    stats = {}
    # 1. 去重：主键「房源链接」重复（含整行重复）
    before = len(df)
    df = df.drop_duplicates(subset=["房源链接"])
    stats["去重删除行数"] = before - len(df)

    # 2. 缺失值：核心分析字段（小区名/行政区/总价/面积/单价）必须无缺失
    core = ["小区名", "行政区", "户型", "面积(平米)", "总价(万)", "单价(元/平)"]
    before = len(df)
    df = df.dropna(subset=core)
    stats["核心字段缺失删除行数"] = before - len(df)
    # 楼层缺失保留（不填补，理由见文件头注释）
    stats["楼层缺失保留行数"] = int(df["楼层"].isnull().sum())

    # 3. 异常值：总价 IQR 法
    q1, q3 = df["总价(万)"].quantile(0.25), df["总价(万)"].quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    stats["IQR下界/上界(万)"] = (round(low, 2), round(high, 2))
    mask = df["总价(万)"].between(low, high)
    stats["异常值剔除行数"] = int((~mask).sum())
    df = df[mask]
    return df, stats


def eda(df):
    """EDA 初步统计：行政区均价、面积/楼层与房价关系。"""
    print("\n===== EDA：各行政区平均单价 =====")
    by_region = df.groupby("行政区")["单价(元/平)"].agg(["count", "mean", "median"]).round(0)
    print(by_region.sort_values("mean", ascending=False).to_string())

    print("\n===== EDA：面积与单价相关性 =====")
    print(f"面积-单价 Pearson 相关系数：{df['面积(平米)'].corr(df['单价(元/平)']):.3f}")
    print(f"面积-总价 Pearson 相关系数：{df['面积(平米)'].corr(df['总价(万)']):.3f}")

    print("\n===== EDA：不同楼层的平均单价 =====")
    print(df.groupby("楼层")["单价(元/平)"].mean().round(0).to_string())

    print("\n===== EDA：不同户型的平均单价（房源数前6的户型） =====")
    top_layouts = df["户型"].value_counts().head(6).index
    print(
        df[df["户型"].isin(top_layouts)]
        .groupby("户型")["单价(元/平)"]
        .mean()
        .round(0)
        .sort_values(ascending=False)
        .to_string()
    )


def main():
    df = load_and_explore(RAW_DATA_PATH)

    df = extract_numeric(df)
    print("\n===== 数值提取后字段类型 =====")
    print(df[["面积(平米)", "单价(元/平)", "关注数(人)", "室", "厅"]].dtypes.to_string())

    df, stats = clean(df)
    print("\n===== 清洗处理统计 =====")
    for k, v in stats.items():
        print(f"{k}：{v}")

    # 输出清洗后数据（保留分析需要的字段，统一中文表头）
    out_cols = [
        "小区名", "行政区", "户型", "室", "厅", "面积(平米)", "朝向",
        "楼层", "总价(万)", "单价(元/平)", "关注数(人)", "发布时间", "房源链接",
    ]
    df[out_cols].to_csv(CLEAN_DATA_PATH, index=False, encoding="utf-8-sig")
    print(f"\n清洗后行数：{len(df)}，已输出：{CLEAN_DATA_PATH}")

    eda(df)
    print("\n清洗完成。详细说明见 docs/EDA分析摘要_成员B.md")


if __name__ == "__main__":
    main()
