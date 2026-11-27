# -*- coding: utf-8 -*-
# 成员C：六张核心图表构建模块
# 数据口径与 analysis/dashboard_stats.py 保持一致（单价去千位逗号、面积去「平米」、剔除 0/缺失）
# 单图预览：.venv/Scripts/python.exe visualization/charts.py  → visualization/output/*.html
# 大屏组装：.venv/Scripts/python.exe visualization/dashboard.py → visualization/ningbo_dashboard.html
import json
from pathlib import Path

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Boxplot, HeatMap, Map, Pie, Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.globals import CurrentConfig, ThemeType

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "raw" / "raw_data.csv"
GEOJSON_PATH = BASE_DIR / "docs" / "ningbo_geojson.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# 深色商务风配色（docs/大屏布局草图_成员C.md）
BG_COLOR = "#0f1c3f"
GOLD = "#f6c344"
CYAN = "#37c6ff"
ORANGE = "#ff9c6e"
GREY = "#8ea0c4"


def load_data() -> pd.DataFrame:
    """读取并清洗原始数据，返回含「单价/面积值/总价」数值列的 DataFrame。"""
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["单价"] = pd.to_numeric(
        df["单价(元/平)"].astype(str).str.replace(",", ""), errors="coerce")
    df["面积值"] = pd.to_numeric(
        df["面积"].astype(str).str.replace("平米", ""), errors="coerce")
    df["总价"] = pd.to_numeric(df["总价(万)"], errors="coerce")
    df = df[(df["单价"] > 0) & (df["面积值"] > 0) & df["总价"].notna()]
    return df


def kpi_data(df: pd.DataFrame) -> dict:
    """顶部 KPI 指标卡数据。"""
    return {
        "total": int(len(df)),
        "avg": round(float(df["单价"].mean())),
        "median": round(float(df["单价"].median())),
        "districts": int(df["行政区"].nunique()),
    }


def _init(height: str = "420px") -> opts.InitOpts:
    return opts.InitOpts(
        theme=ThemeType.DARK, bg_color=BG_COLOR, width="1100px", height=height)


def build_bar(df: pd.DataFrame) -> Bar:
    """图1：各行政区平均单价柱状图（降序，Tooltip 附房源数）。"""
    g = (df.groupby("行政区")["单价"].agg(["mean", "count"])
         .sort_values("mean", ascending=False))
    counts = json.dumps({k: int(v) for k, v in g["count"].items()}, ensure_ascii=False)
    return (
        Bar(init_opts=_init())
        .add_xaxis(g.index.tolist())
        .add_yaxis("平均单价(元/平)", [round(v) for v in g["mean"]],
                   itemstyle_opts=opts.ItemStyleOpts(color=GOLD))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各行政区平均单价", subtitle="按均价降序"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    "function(p){var c=%s[p.name]||0;"
                    "return p.name+'<br/>均价：'+p.value+' 元/平<br/>在售：'+c+' 套';}" % counts)),
            datazoom_opts=[opts.DataZoomOpts(type_="inside")],
        )
    )


def build_pie(df: pd.DataFrame) -> Pie:
    """图2：总价区间占比饼图（分箱口径与 B 对齐：≤80 / 80-150 / 150-300 / >300 万）。"""
    bins = [(0, 80, "≤80万"), (80, 150, "80-150万"),
            (150, 300, "150-300万"), (300, 10**9, ">300万")]
    data = [{"name": n, "value": int(((df["总价"] > a) & (df["总价"] <= b)).sum())}
            for a, b, n in bins]
    return (
        Pie(init_opts=_init())
        .add("房源数", data,
             center=["50%", "55%"],
             label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="在售房源总价区间占比"),
            legend_opts=opts.LegendOpts(orient="vertical", pos_left="left", pos_top="middle"),
            tooltip_opts=opts.TooltipOpts(formatter="{b}：{c} 套（{d}%）"),
        )
        .set_series_opts(selected_mode="single")
    )


def build_scatter(df: pd.DataFrame) -> Scatter:
    """图3：面积-单价散点图，visualMap 按单价映射颜色。"""
    points = [[round(r["面积值"], 1), round(r["单价"])] for _, r in df.iterrows()]
    vmax = round(float(df["单价"].max()))
    return (
        Scatter(init_opts=_init())
        .add_xaxis(points)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="面积与单价关系"),
            xaxis_opts=opts.AxisOpts(name="面积(㎡)", type_="value", splitline_opts=opts.SplitLineOpts(is_show=True)),
            yaxis_opts=opts.AxisOpts(name="单价(元/平)", type_="value", splitline_opts=opts.SplitLineOpts(is_show=True)),
            tooltip_opts=opts.TooltipOpts(formatter=JsCode(
                "function(p){return '面积：'+p.value[0]+' ㎡<br/>单价：'+p.value[1]+' 元/平';}")),
            visualmap_opts=opts.VisualMapOpts(
                dimension=1, min_=3000, max_=vmax, is_piecewise=False,
                range_color=[CYAN, GOLD, ORANGE], range_text=["高", "低"],
                pos_right="5%", pos_top="middle"),
        )
    )


def build_box(df: pd.DataFrame) -> Boxplot:
    """图4：各行政区单价箱线图（样本量 ≥30 才纳入）。"""
    rows = df.groupby("行政区")["单价"].agg(["count", "mean"]).sort_values("mean", ascending=False)
    names, data = [], []
    for name, cnt in rows["count"].items():
        if cnt < 30:
            continue
        sub = df[df["行政区"] == name]["单价"]
        q1, med, q3 = sub.quantile(.25), sub.quantile(.5), sub.quantile(.75)
        iqr = q3 - q1
        lo = float(sub[sub >= q1 - 1.5 * iqr].min())
        hi = float(sub[sub <= q3 + 1.5 * iqr].max())
        names.append(name)
        data.append([round(lo), round(q1), round(med), round(q3), round(hi)])
    return (
        Boxplot(init_opts=_init())
        .add_xaxis(names)
        .add_yaxis("单价(元/平)", data,
                   itemstyle_opts=opts.ItemStyleOpts(color=CYAN, border_color=GOLD))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各行政区单价分布（箱线图）", subtitle="样本量 <30 的区县不纳入"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
            yaxis_opts=opts.AxisOpts(name="单价(元/平)"),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )


def build_heatmap(df: pd.DataFrame) -> HeatMap:
    """图5：总价 × 单价 × 面积 Pearson 相关性热力图。"""
    labels = ["总价(万)", "单价(元/平)", "面积"]
    corr = df[["总价", "单价", "面积值"]].corr(method="pearson")
    data = [[i, j, round(float(corr.iloc[i, j]), 3)] for i in range(3) for j in range(3)]
    labels_js = json.dumps(labels, ensure_ascii=False)
    return (
        HeatMap(init_opts=_init(height="380px"))
        .add_xaxis(labels)
        .add_yaxis("相关系数", labels, data,
                   label_opts=opts.LabelOpts(is_show=True, position="inside"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="数值变量相关性热力图"),
            visualmap_opts=opts.VisualMapOpts(
                min_=-1, max_=1, is_piecewise=False, pos_right="2%",
                range_color=[CYAN, "#16264d", GOLD]),
            tooltip_opts=opts.TooltipOpts(formatter=JsCode(
                "function(p){var L=%s;var x=L[p.value[0]],y=L[p.value[1]];"
                "return x+' × '+y+'<br/>r = '+p.value[2];}" % labels_js)),
        )
    )


def build_map(df: pd.DataFrame) -> Map:
    """图6：宁波市行政区房价地图（geoJSON 内嵌，离线渲染）。"""
    g = df.groupby("行政区")["单价"].mean().sort_values(ascending=False)
    m = Map(init_opts=_init(height="620px"))
    m.add("平均单价(元/平)",
          [[k, round(v)] for k, v in g.items()],
          maptype="ningbo",
          is_map_symbol_show=False,
          label_opts=opts.LabelOpts(is_show=True),
          tooltip_opts=opts.TooltipOpts(formatter=JsCode(
              "function(p){return p.name+'<br/>均价：'+(p.value||'-')+' 元/平';}")))
    m.set_global_opts(
        title_opts=opts.TitleOpts(title="宁波市各区县平均单价地图", subtitle="颜色越深均价越高（前湾新区为功能区，无官方边界不涂色）"),
        visualmap_opts=opts.VisualMapOpts(
            min_=int(g.min()), max_=int(g.max()), pos_left="2%", pos_bottom="5%",
            range_color=[CYAN, GOLD, ORANGE]),
    )
    # 内嵌 geoJSON：模板会以 echarts.registerMap('ningbo', {...}) 内联注册，离线可用
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geo = json.load(f)
    m._geo_json_name = "ningbo"
    m._geo_json = geo
    if "ningbo" in m.js_dependencies.items:
        m.js_dependencies.items.remove("ningbo")  # 数据已内嵌，避免渲染出多余的外链地图 js
    return m


if __name__ == "__main__":
    CurrentConfig.ONLINE_HOST = "../"  # output/ 的上级目录即 visualization/echarts.min.js
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = load_data()
    for chart in (build_bar(data), build_pie(data), build_scatter(data),
                  build_box(data), build_heatmap(data), build_map(data)):
        path = OUTPUT_DIR / f"{chart.__class__.__name__.lower()}.html"
        chart.render(str(path))
        print(f"已生成 {path}")
