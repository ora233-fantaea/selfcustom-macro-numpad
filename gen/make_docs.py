"""从 design.py 生成归档用文档：docs/元件表.md 与 docs/网表.md。

单一真值源是 design.py，这两份文档是它的渲染结果，改设计后重跑即可：

    python gen/make_docs.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as d

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, 'docs')


def ref_key(ref):
    """SW1 < SW2 < … ；R1 < R10；先按字母前缀再按数字。"""
    head = ref.rstrip('0123456789')
    num = ref[len(head):]
    return (head, int(num) if num else 0)


def comp_rows():
    rows = []
    for c in sorted(d.COMPS, key=lambda c: ref_key(c['ref'])):
        nets = c.get('nets') or {}
        net_txt = ' '.join('%s→%s' % (p, n) for p, n in sorted(nets.items()))
        x, y = c['at']
        rows.append((c['ref'], c['value'], c.get('fp', ''), c.get('side', 'F'),
                     '%.2f, %.2f' % (x, y), c.get('rot', 0), net_txt))
    return rows


def write_components():
    out = io.StringIO()
    out.write('# 元件表\n\n')
    out.write('> 本文件由 `gen/make_docs.py` 从 [`gen/design.py`](../gen/design.py) 自动生成，**不要手改**。\n')
    out.write('> 改设计请改 design.py 后重跑：`python gen/make_docs.py`。\n\n')
    out.write('共 **%d** 个元件、**%d** 个网络。坐标单位为 mm，原点在板子左上角，'
              'X 向右、Y 向下；`F` = 正面（轴体侧），`B` = 背面（焊接侧）。\n\n' % (len(d.COMPS), len(d.net_table())))
    out.write('| 位号 | 值 | 封装 | 面 | 位置 (x, y) | 旋转 | 网络 |\n')
    out.write('|---|---|---|---|---|---|---|\n')
    for r in comp_rows():
        out.write('| %s | %s | %s | %s | %s | %s° | %s |\n' % r)
    body = out.getvalue()
    with open(os.path.join(DOCS, '元件表.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(body)
    return len(d.COMPS)


def write_netlist():
    net = d.net_table()
    out = io.StringIO()
    out.write('# 网表\n\n')
    out.write('> 本文件由 `gen/make_docs.py` 从 [`gen/design.py`](../gen/design.py) 自动生成，**不要手改**。\n\n')
    out.write('共 **%d** 个网络。原理图（`kicad/numpad.kicad_sch`）用网络标签连接，'
              '导出的 `kicad/numpad.net` 与本表逐网络一致（见 `gen/check_sch.py` 的回归）。\n\n' % len(net))
    out.write('| 网络 | 引脚数 | 连接 |\n|---|---|---|\n')
    for name in sorted(net, key=lambda n: (n.upper() != 'GND', n.upper())):
        pins = sorted(('%s.%s' % (r, p) for r, p in net[name]), key=lambda s: ref_key(s.split('.')[0]))
        out.write('| `%s` | %d | %s |\n' % (name, len(pins), ', '.join(pins)))
    body = out.getvalue()
    with open(os.path.join(DOCS, '网表.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(body)
    return len(net)


def write_matrix():
    """键盘矩阵表：把每个开关的行/列网络翻成 MCU 引脚。"""
    gpio_of = {}
    for n, gp in enumerate(d._ROW_GPIO):
        gpio_of['ROW%d' % n] = gp
    for n, gp in enumerate(d._COL_GPIO):
        gpio_of['COL%d' % n] = gp

    def pin_name(gp):
        return 'GP%d' % gp

    by_sw = {}
    for c in d.COMPS:
        if c['ref'].startswith('SW') and c.get('key'):
            by_sw[c['ref']] = c
    dio = {}
    for c in d.COMPS:
        if c['ref'].startswith('D'):
            nets = list(c.get('nets', {}).values())
            a = [n for n in nets if n.startswith('K_')]
            r = [n for n in nets if n.startswith('ROW')]
            if a:
                dio[a[0]] = (c['ref'], r[0] if r else '?')

    out = io.StringIO()
    out.write('# 矩阵与引脚分配\n\n')
    out.write('> 生成自 `gen/design.py`。\n\n')
    out.write('## 行 / 列 → MCU 引脚\n\n')
    out.write('| 网络 | RP2040 引脚 |\n|---|---|\n')
    for n in ['ROW0', 'ROW1', 'ROW2', 'ROW3', 'ROW4', 'ROW5']:
        out.write('| `%s` | %s |\n' % (n, pin_name(gpio_of[n])))
    for n in ['COL0', 'COL1', 'COL2', 'COL3', 'COL4']:
        out.write('| `%s` | %s |\n' % (n, pin_name(gpio_of[n])))
    out.write('\n## 键位表\n\n')
    out.write('| 键 | 开关 | 二极管 | 列 | 行 | MCU |\n|---|---|---|---|---|---|\n')
    order = ['F1', 'F2', 'F3', 'F4', 'M1', 'M2', 'M3', 'M4', 'M5',
             'NUM', '/', '*', '-', '+', '7', '8', '9', '4', '5', '6',
             '1', '2', '3', 'ENTER', '0', '.']
    rows = []
    for ref, c in by_sw.items():
        nets = c['nets']
        col = [v for v in nets.values() if v.startswith('COL')]
        k = c['nets']['1']
        dre, row = dio.get(k, ('?', '?'))
        label = d.KEY_LABEL.get(c['key'], c['key'])
        rows.append((label, ref, dre, col[0] if col else '?', row))
    rows.sort(key=lambda r: (order.index(r[0]) if r[0] in order else 99))
    for label, ref, dre, col, row in rows:
        out.write('| %s | %s | %s | %s (%s) | %s (%s) | — |\n' % (
            label, ref, dre, col, pin_name(gpio_of.get(col, -1)), row, pin_name(gpio_of.get(row, -1))))
    # 旋钮按压：ENC1 的 S1 经 D27 进 ROW0、S2 接 COL0 → 矩阵位置 R0C0
    for c in d.COMPS:
        if c['ref'] == 'ENC1':
            s2 = c['nets'].get('S2', '?')
            out.write('| 旋钮按压 | ENC1.S1/S2 | D27 | %s (%s) | ROW0 (GP2) | R0C0 |\n' % (
                s2, pin_name(gpio_of.get(s2, -1))))
            out.write('\n旋钮本体（EC11 编码器 A/B 相，直接进 GPIO，不占矩阵）：\n\n')
            out.write('| 信号 | ENC1 引脚 | 网络 | RP2040 |\n|---|---|---|---|\n')
            ab = {'A': 'GP0', 'B': 'GP1'}
            for pin in ('A', 'B'):
                out.write('| %s 相 | %s | `%s` | %s |\n' % (pin, pin, c['nets'].get(pin, '?'), ab[pin]))
            out.write('| 公共端 | C | `GND` | GND |\n')
    body = out.getvalue()
    with open(os.path.join(DOCS, '矩阵与引脚.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(body)


if __name__ == '__main__':
    os.makedirs(DOCS, exist_ok=True)
    n = write_components()
    m = write_netlist()
    write_matrix()
    print('docs/元件表.md     %d 个元件' % n)
    print('docs/网表.md       %d 个网络' % m)
    print('docs/矩阵与引脚.md  26 键 + 旋钮')
