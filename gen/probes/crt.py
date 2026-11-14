# -*- coding: utf-8 -*-
"""打印各封装 courtyard 的实际范围（用于精确摆位）。"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import build_pcb as B
import pcbnew


def show(key):
    path, name = B.lib_path(key)
    fp = pcbnew.FootprintLoad(path, name)
    for layer, tag in ((pcbnew.F_CrtYd, 'F'), (pcbnew.B_CrtYd, 'B')):
        poly = fp.GetCourtyard(layer)
        if poly.OutlineCount() == 0:
            continue
        bb = poly.BBox()
        print('%-12s %s-crt  x %7.2f..%7.2f  y %7.2f..%7.2f   (w %.2f h %.2f)' % (
            key, tag,
            pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight()),
            pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom()),
            pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))


for k in ('mx_hotswap', 'stab_2u', 'd_sod123', 'r_0402', 'c_0402', 'c_0603',
          'fuse1206', 'qfn56', 'soic8', 'sot23_5', 'sot23_6', 'crystal',
          'usbc16', 'ec11', 'sw_push', 'tp', 'mh_m3'):
    try:
        show(k)
    except Exception as e:
        print(k, 'ERR', e)
