# -*- coding: utf-8 -*-
# 把阿里云 DataV 的宁波市 geoJSON 转成大屏可直接 <script> 引入的 JS 文件
# 来源：https://geo.datav.aliyun.com/areas_v3/bound/330200_full.json（公开免费数据）
import json

with open('docs/ningbo_geojson.json', encoding='utf-8') as f:
    geo = json.load(f)

js = ('// 由 analysis/gen_geo_js.py 从 docs/ningbo_geojson.json 生成，勿手改\n'
      'const NINGBO_GEO = ' + json.dumps(geo, ensure_ascii=False, separators=(',', ':')) + ';\n')

with open('visualization/ningbo_geo.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('ningbo_geo.js written,', len(js), 'bytes')
