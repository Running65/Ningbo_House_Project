# -*- coding: utf-8 -*-
# 成员C：组装宁波二手房数据大屏（深色商务风，离线 HTML）
# 运行：.venv/Scripts/python.exe visualization/dashboard.py → visualization/ningbo_dashboard.html
import json
import re
import sys
from pathlib import Path

from pyecharts.charts import Page
from pyecharts.globals import CurrentConfig

sys_dir = Path(__file__).resolve().parent
sys_path = str(sys_dir)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

import charts  # noqa: E402  同目录下的图表构建模块

CurrentConfig.ONLINE_HOST = "./"  # echarts.min.js 与大屏同目录，离线可用

KPI_HTML = """
<style>
  body { background:#0f1c3f; font-family:"Microsoft YaHei","PingFang SC",sans-serif; }
  .kpi-row { display:flex; gap:16px; padding:14px 24px; max-width:1140px; margin:0 auto; }
  .kpi { flex:1; background:#16264d; border-radius:8px; padding:12px 18px;
         border:1px solid rgba(55,198,255,.25); text-align:center; }
  .kpi .label { color:#8ea0c4; font-size:13px; }
  .kpi .value { font-size:28px; font-weight:bold; margin-top:4px; }
  .kpi.gold .value { color:#f6c344; } .kpi.cyan .value { color:#37c6ff; }
</style>
<div class="kpi-row">
  <div class="kpi cyan"><div class="label">在售房源总数</div><div class="value">{total} 套</div></div>
  <div class="kpi gold"><div class="label">全市平均单价</div><div class="value">{avg} 元/平</div></div>
  <div class="kpi gold"><div class="label">单价中位数</div><div class="value">{median} 元/平</div></div>
  <div class="kpi cyan"><div class="label">覆盖行政区</div><div class="value">{districts} 个</div></div>
</div>
"""


def inject_kpi(html_path: Path, kpi: dict) -> None:
    """把 KPI 指标卡与深色背景注入渲染后的 HTML（pyecharts Page 只承载图表）。"""
    html = html_path.read_text(encoding="utf-8")
    block = KPI_HTML
    for key, value in kpi.items():
        block = block.replace("{%s}" % key, str(value))
    html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + block, html, count=1)
    html_path.write_text(html, encoding="utf-8")


def main() -> None:
    df = charts.load_data()
    kpi = charts.kpi_data(df)
    page = Page(page_title="宁波市二手房市场价格洞察大屏", layout=Page.SimplePageLayout)
    page.add(
        charts.build_map(df),      # 主视觉：区域地图
        charts.build_bar(df),      # 左：各区均价
        charts.build_box(df),      # 右：分布
        charts.build_pie(df),      # 价格结构
        charts.build_scatter(df),  # 面积-单价
        charts.build_heatmap(df),  # 相关性
    )
    out = sys_dir / "ningbo_dashboard.html"
    page.render(str(out))
    inject_kpi(out, kpi)
    print(f"大屏已生成：{out}")
    print(json.dumps(kpi, ensure_ascii=False))


if __name__ == "__main__":
    main()
