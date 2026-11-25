# -*- coding: utf-8 -*-
# 成员C：从 raw_data.csv 计算大屏真实统计值（图表数据口径与B的字段设计表一致）
import json, re
import pandas as pd

df = pd.read_csv('data/raw/raw_data.csv', encoding='utf-8-sig')
df['单价'] = df['单价(元/平)'].astype(str).str.replace(',', '').astype(float)
df['面积值'] = df['面积'].str.replace('平米', '').astype(float)
df = df[(df['单价'] > 0) & (df['面积值'] > 0)]

stats = {}
stats['total'] = int(len(df))
stats['avgPrice'] = round(float(df['单价'].mean()))
stats['medianPrice'] = round(float(df['单价'].median()))
stats['districts'] = int(df['行政区'].nunique())

# 图1/图6：各区平均单价，降序
g = df.groupby('行政区')['单价'].agg(['mean', 'count']).sort_values('mean', ascending=False)
stats['districtAvg'] = [[idx, round(r['mean']), int(r['count'])] for idx, r in g.iterrows()]

# 图2：总价分箱（B建议口径 ≤80 / 80-150 / 150-300 / >300 万）
bins = [(0, 80, '≤80万'), (80, 150, '80-150万'), (150, 300, '150-300万'), (300, 10**9, '>300万')]
stats['priceRanges'] = [{'name': n, 'value': int(((df['总价(万)'] > a) & (df['总价(万)'] <= b)).sum())} for a, b, n in bins]

# 图3：面积-单价散点（全量）
stats['scatter'] = [[round(r['面积值'], 1), round(r['单价'])] for _, r in df.iterrows()]

# 图4：各区单价箱线图 [min,q1,med,q3,max]
def box5(s):
    q1, med, q3 = s.quantile(.25), s.quantile(.5), s.quantile(.75)
    iqr = q3 - q1
    lo = float(s[s >= q1 - 1.5 * iqr].min()); hi = float(s[s <= q3 + 1.5 * iqr].max())
    return [round(lo), round(q1), round(med), round(q3), round(hi)]
stats['box'] = {d: box5(sub['单价']) for d, sub in df.groupby('行政区')}

# 图5：Pearson 相关矩阵
cols = ['总价(万)', '单价', '面积值']
corr = df[cols].corr(method='pearson')
stats['corrLabels'] = ['总价(万)', '单价(元/平)', '面积']
stats['corr'] = [[float(corr.iloc[i, j]) for j in range(3)] for i in range(3)]

with open('/tmp/stats.json', 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=1)

# 同步生成大屏引用的数据文件（analysis.py → 图表统计数据 的交付形式）
js = "// 由 analysis/dashboard_stats.py 自动生成，勿手改；数据源 data/raw/raw_data.csv\n"
js += "const KPI = {total:%d, avgPrice:%d, medianPrice:%d, districts:%d};\n" % (
    stats['total'], stats['avgPrice'], stats['medianPrice'], stats['districts'])
js += "const DISTRICT_AVG = %s;\n" % json.dumps(stats['districtAvg'], ensure_ascii=False)
js += "const PRICE_RANGES = %s;\n" % json.dumps(stats['priceRanges'], ensure_ascii=False)
js += "const SCATTER = %s;\n" % json.dumps(stats['scatter'])
js += "const BOX = %s;\n" % json.dumps(stats['box'], ensure_ascii=False)
js += "const CORR_LABELS = %s;\n" % json.dumps(stats['corrLabels'], ensure_ascii=False)
js += "const CORR = %s;\n" % json.dumps(stats['corr'])
with open('visualization/real_data.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('real_data.js written,', len(js), 'bytes')
print(json.dumps(stats, ensure_ascii=False)[:600])
