# -*- coding: utf-8 -*-
"""把 DRC 违规点画到板子截图上，用来直接看"挤在哪儿"。

    python gen/drc_map.py [x0 y0 x1 y1]

默认画电子舱（40,0)-(92,20)。红色圈 = 违规点，圈的颜色深度按类别区分；
底层走线按层着色：F 红 / In3 橙 / In4 紫 / B 蓝。
"""
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
PCB = os.path.join(ROOT, 'numpad', 'kicad', 'numpad.kicad_pcb')
RPT = os.path.join(ROOT, 'numpad', 'kicad', 'drc.rpt')
OUT = os.path.join(ROOT, 'numpad', 'kicad', 'img', 'bay_drc.png')

LAYER_COL = {
    'F.Cu': (255, 90, 90, 235),
    'In3.Cu': (255, 165, 60, 235),
    'In4.Cu': (190, 110, 240, 235),
    'B.Cu': (90, 150, 255, 235),
}
# 电气类问题用亮红，几何/外观类用粉色，未连接用黄色
SEV_COL = {
    'shorting_items': (255, 40, 40),
    'clearance': (255, 120, 0),
    'tracks_crossing': (255, 0, 200),
    'solder_mask_bridge': (255, 200, 0),
    'hole_clearance': (0, 230, 230),
    'hole_to_hole': (0, 230, 230),
    'holes_co_located': (0, 230, 230),
    'unconnected_items': (255, 255, 0),
    'track_dangling': (160, 160, 160),
    'via_dangling': (160, 160, 160),
}


def track_width(t):
    """取线宽。KiCad 10 里 PCB_VIA 的宽度按层不同，不带层会触发断言弹窗。"""
    if isinstance(t, pcbnew.PCB_VIA):
        return t.GetWidth(pcbnew.F_Cu)
    return t.GetWidth()


def parse_rpt():
    """返回 [(类型, x, y, 说明)]"""
    out = []
    kind = None
    for line in open(RPT, encoding='utf-8', errors='replace'):
        m = re.match(r'^\[(\w+)\]:\s*(.*)$', line)
        if m:
            kind = m.group(1)
            desc = m.group(2)
            continue
        m = re.search(r'@\(\s*([-\d.]+) mm,\s*([-\d.]+) mm\)', line)
        if m and kind:
            out.append((kind, float(m.group(1)), float(m.group(2))))
    return out


def main():
    reg = (40.0, 0.0, 92.0, 20.0)
    if len(sys.argv) >= 5:
        reg = tuple(float(v) for v in sys.argv[1:5])

    board = pcbnew.LoadBoard(PCB)
    mm = R.mm
    cv = R.Canvas(107.25, 134.3, zoom=14, region=reg, margin=1.5)

    # 板框
    for d in board.GetDrawings():
        if d.GetLayerName() == 'Edge.Cuts':
            pts = R.shape_points(d)
            if len(pts) >= 2:
                cv.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], (200, 200, 120, 255), 0.2)

    # 走线（只看区域内的）
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            x, y = mm(p.x), mm(p.y)
            if reg[0] - 1 < x < reg[2] + 1 and reg[1] - 1 < y < reg[3] + 1:
                cv.circle(x, y, mm(t.GetWidth(pcbnew.F_Cu)) / 2, (240, 240, 240, 230))
                cv.circle(x, y, mm(t.GetDrillValue()) / 2, (20, 20, 20, 255))
            continue
        col = LAYER_COL.get(t.GetLayerName())
        if not col:
            continue
        a, b = t.GetStart(), t.GetEnd()
        cv.line(mm(a.x), mm(a.y), mm(b.x), mm(b.y), col, mm(track_width(t)))

    # 焊盘
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.IsOnLayer(pcbnew.F_Cu):
                R.draw_pad(cv, pad, (215, 180, 70, 255))
            elif pad.IsOnLayer(pcbnew.B_Cu):
                R.draw_pad(cv, pad, (150, 120, 60, 255))

    # 违规点
    items = parse_rpt()
    shown = 0
    for kind, x, y in items:
        if not (reg[0] - 1 < x < reg[2] + 1 and reg[1] - 1 < y < reg[3] + 1):
            continue
        col = SEV_COL.get(kind, (255, 255, 255))
        cv.circle(x, y, 0.55, col, fill=False, width_mm=0.12)
        shown += 1

    cv.save(OUT)
    print('wrote %s  区域内违规点 %d / 全板 %d' % (OUT, shown, len(items)))
    # 区域内的类别统计
    cnt = {}
    for kind, x, y in items:
        if reg[0] - 1 < x < reg[2] + 1 and reg[1] - 1 < y < reg[3] + 1:
            cnt[kind] = cnt.get(kind, 0) + 1
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
        print('   %-22s %d' % (k, v))


if __name__ == '__main__':
    main()
