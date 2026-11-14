# -*- coding: utf-8 -*-
"""原理图回归检查：ERC 必须 0 违规，导出网表必须与 design.py 完全一致。

    python gen/check_sch.py

退出码 0 = 通过；1 = 有问题（会打印差异）。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D                                        # noqa: E402
import sexpr                                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
KICADCLI = os.path.join(ROOT, 'tools', 'kicad-portable', 'bin', 'kicad-cli.exe')
SCH = os.path.join(ROOT, 'numpad', 'kicad', 'numpad.kicad_sch')
ERC = os.path.join(ROOT, 'numpad', 'kicad', 'erc.rpt')
NET = os.path.join(ROOT, 'numpad', 'kicad', 'numpad.net')


def clean(s):
    return s.strip('"').lstrip('/')


def walk(node, name):
    if isinstance(node, list) and node and node[0] == name:
        return node
    if isinstance(node, list):
        for c in node:
            r = walk(c, name)
            if r:
                return r
    return None


def main():
    bad = 0

    # ---- 1. ERC ----
    subprocess.run([KICADCLI, 'sch', 'erc', '-o', ERC, SCH],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
    text = open(ERC, encoding='utf-8').read()
    kinds = re.findall(r'^\[(\w+)\]', text, re.M)
    cnt = {}
    for k in kinds:
        cnt[k] = cnt.get(k, 0) + 1
    print('ERC：%d 条违规 %s' % (len(kinds), cnt if cnt else ''))
    if kinds:
        bad += 1

    # ---- 2. 网表 vs design.py ----
    subprocess.run([KICADCLI, 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
                    '-o', NET, SCH],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
    root = sexpr.parse(open(NET, encoding='utf-8').read())
    nets_node = walk(root, 'nets')
    sch = {}
    for n in nets_node[1:]:
        if n[0] != 'net':
            continue
        name = clean([c for c in n if isinstance(c, list) and c[0] == 'name'][0][1])
        nodes = set()
        for nd in n[1:]:
            if isinstance(nd, list) and nd[0] == 'node':
                ref = clean([c for c in nd if isinstance(c, list) and c[0] == 'ref'][0][1])
                pin = clean([c for c in nd if isinstance(c, list) and c[0] == 'pin'][0][1])
                if not ref.startswith('FLG_'):        # PWR_FLAG 是原理图专用的假元件
                    nodes.add((ref, pin))
        sch[name] = nodes

    # EC11 的 MP 安装脚在封装里直接接 GND，符号没有这个引脚，比对时排除
    pcb = {k: {x for x in v if not (x[0] == 'ENC1' and x[1] == 'MP')}
           for k, v in D.net_table().items()}

    same, diff = 0, []
    for name in sorted(set(sch) | set(pcb)):
        a, b = sch.get(name, set()), pcb.get(name, set())
        if a == b and a:
            same += 1
        elif b:                                       # 原理图独有的 unconnected-* 不算差异
            diff.append((name, sorted(a - b), sorted(b - a)))
    print('网表：一致 %d 个网络，不一致 %d 个（另有 %d 个 unconnected-* 悬空脚）'
          % (same, len(diff), len([k for k in sch if k not in pcb])))
    for d in diff:
        print('   差异 %s  原理图多 %s  设计多 %s' % d)
    if diff:
        bad += 1

    print('结果：%s' % ('通过' if bad == 0 else '不通过'))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
