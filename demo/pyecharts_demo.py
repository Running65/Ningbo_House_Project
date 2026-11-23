# 成员 C 第一周 Pyecharts 最小演示
# 运行：.venv/Scripts/python.exe demo/pyecharts_demo.py
# 注意：以下数据是虚构的，仅用于测试图表功能，不得当作宁波真实房价结论。

from pyecharts.globals import CurrentConfig

CurrentConfig.ONLINE_HOST = "./"   # 从本地目录加载 echarts.min.js，离线可用

from pyecharts.charts import Bar
from pyecharts import options as opts

bar = (
    Bar()
    .add_xaxis(["海曙", "鄞州", "江北"])
    .add_yaxis("示例均价", [20000, 26000, 18000])
    .set_global_opts(
        title_opts=opts.TitleOpts(title="Pyecharts 测试图"),
        tooltip_opts=opts.TooltipOpts(),          # 动态提示框
        toolbox_opts=opts.ToolboxOpts(),          # 工具箱（保存图片等）
    )
)

bar.render("demo.html")
print("已生成 demo.html，用浏览器打开即可查看图表。")
