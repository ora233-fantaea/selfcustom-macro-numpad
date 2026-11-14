# -*- coding: utf-8 -*-
"""把 drc.rpt 按坐标聚成热点，便于一次修一片。"""
import re
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else 'numpad/kicad/drc.rpt'
txt = open(path, encoding='utf-8').read()
blocks = re.split(r'\n(?=\[)', txt)
hot = defaultdict(list)
kinds = defaultdict(int)
for b in blocks:
    m = re.match(r'\[(\w+)\]', b)
    if not m:
        continue
    kind = m.group(1)
    kinds[kind] += 1
    pts = re.findall(r'@\(([\d.]+) mm, ([\d.]+) mm\)', b)
    if not pts:
        continue
    x = sum(float(p[0]) for p in pts) / len(pts)
    y = sum(float(p[1]) for p in pts) / len(pts)
    hot[(round(x / 4) * 4, round(y / 4) * 4)].append((kind, b.strip().splitlines()[0][:60]))

print('总计：', sum(kinds.values()))
for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
    print('  %-22s %d' % (k, v))
print('\n热点（4mm 网格）：')
for (x, y), items in sorted(hot.items(), key=lambda kv: -len(kv[1]))[:18]:
    print('  ~(%5.1f, %5.1f)  %d 条: %s' % (x, y, len(items),
                                           ', '.join(sorted({i[0] for i in items}))))
