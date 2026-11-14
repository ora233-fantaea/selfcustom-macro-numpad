# -*- coding: utf-8 -*-
"""布线器的几何检查器（轻量 DRC）。

只回答一个问题：这条走线/这个过孔放下去会不会跟已有的铜皮撞。
检查对象：焊盘（带旋转的矩形/圆）、走线（线段）、过孔（圆）、NPTH 孔、板边。

比 kicad-cli 快两个数量级，用来在布线过程中实时拦截，而不是事后翻报告。
"""
import math

CLR = 0.20          # 线到线/线到焊盘的最小间距
HOLE_CLR = 0.25     # 铜到 NPTH 孔壁
EDGE_CLR = 0.50     # 铜到板边


def _pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / L2
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _seg_seg(a, b):
    """两条线段的最近距离（相交返回 0）"""
    (x1, y1), (x2, y2) = a
    (x3, y3), (x4, y4) = b

    def cross(ox, oy, ax, ay, bx, by):
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    d1 = cross(x3, y3, x4, y4, x1, y1)
    d2 = cross(x3, y3, x4, y4, x2, y2)
    d3 = cross(x1, y1, x2, y2, x3, y3)
    d4 = cross(x1, y1, x2, y2, x4, y4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(_pt_seg(x1, y1, x3, y3, x4, y4),
               _pt_seg(x2, y2, x3, y3, x4, y4),
               _pt_seg(x3, y3, x1, y1, x2, y2),
               _pt_seg(x4, y4, x1, y1, x2, y2))


def _seg_rect(a, b, cx, cy, w, h, rot):
    """线段到带旋转矩形的最近距离"""
    th = math.radians(-rot)
    c, s = math.cos(th), math.sin(th)

    def tf(x, y):
        dx, dy = x - cx, y - cy
        return (dx * c - dy * s, dx * s + dy * c)

    (x1, y1), (x2, y2) = tf(*a), tf(*b)
    hw, hh = w / 2.0, h / 2.0
    # 端点在矩形内 -> 相交
    for x, y in ((x1, y1), (x2, y2)):
        if -hw <= x <= hw and -hh <= y <= hh:
            return 0.0
    # 线段穿过矩形 -> 相交
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    ok = True
    for p, q in ((-dx, x1 + hw), (dx, hw - x1), (-dy, y1 + hh), (dy, hh - y1)):
        if abs(p) < 1e-12:
            if q < 0:
                ok = False
                break
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if ok and t0 <= t1:
        return 0.0
    best = min(_pt_seg(-hw, -hh, x1, y1, x2, y2),
               _pt_seg(hw, -hh, x1, y1, x2, y2),
               _pt_seg(-hw, hh, x1, y1, x2, y2),
               _pt_seg(hw, hh, x1, y1, x2, y2))
    for x, y in ((x1, y1), (x2, y2)):
        px = min(max(x, -hw), hw)
        py = min(max(y, -hh), hh)
        best = min(best, math.hypot(x - px, y - py))
    return best


class Layout:
    """收集板上的铜皮几何，边加边查"""

    def __init__(self, board_w, board_h):
        self.w, self.h = board_w, board_h
        self.pads = []       # (x, y, w, h, rot, net, layer, is_hole, drill)
        self.tracks = []     # (a, b, width, net, layer)
        self.vias = []       # (x, y, d, net)
        self.conflicts = []

    def add_pad(self, x, y, w, h, rot, net, layer, is_hole=False, drill=0.0):
        self.pads.append((x, y, w, h, rot, net or '', layer, is_hole, drill))

    # --- 查询 ---
    def check_track(self, a, b, width, net, layer):
        out = []
        r = width / 2.0
        for (px, py, pw, ph, prot, pnet, player, is_hole, drill) in self.pads:
            if is_hole:
                need = r + drill / 2.0 + HOLE_CLR
                d = _pt_seg(px, py, a[0], a[1], b[0], b[1])
                if d < need:
                    out.append(('hole', 'NPTH', d, need, (px, py)))
                continue
            if player != layer or pnet == net:
                continue
            d = _seg_rect(a, b, px, py, pw, ph, prot)
            if d < r + CLR:
                out.append(('pad', pnet, d, r + CLR, (px, py)))
        for (ta, tb, tw, tnet, tlayer) in self.tracks:
            if tlayer != layer or tnet == net:
                continue
            d = _seg_seg((a, b), (ta, tb))
            if d < r + tw / 2.0 + CLR:
                out.append(('track', tnet, d, r + tw / 2.0 + CLR, ta))
        for (vx, vy, vd, vnet) in self.vias:
            if vnet == net:
                continue
            d = _pt_seg(vx, vy, a[0], a[1], b[0], b[1])
            if d < r + vd / 2.0 + CLR:
                out.append(('via', vnet, d, r + vd / 2.0 + CLR, (vx, vy)))
        # 板边
        for x, y in (a, b):
            e = min(x, y, self.w - x, self.h - y)
            if e < r + EDGE_CLR:
                out.append(('edge', '', e, r + EDGE_CLR, (x, y)))
        return out

    def check_via(self, x, y, d, net):
        out = []
        r = d / 2.0
        for (px, py, pw, ph, prot, pnet, player, is_hole, drill) in self.pads:
            if is_hole:
                need = r + drill / 2.0 + HOLE_CLR
                dist = math.hypot(x - px, y - py)
                if dist < need:
                    out.append(('hole', 'NPTH', dist, need, (px, py)))
                continue
            if pnet == net:
                continue
            dist = math.hypot(x - px, y - py)
            half = math.hypot(pw, ph) / 2.0
            if dist < r + CLR:
                out.append(('pad', pnet, dist, r + CLR, (px, py)))
        for (ta, tb, tw, tnet, tlayer) in self.tracks:
            if tnet == net:
                continue
            dist = _pt_seg(x, y, ta[0], ta[1], tb[0], tb[1])
            if dist < r + tw / 2.0 + CLR:
                out.append(('track', tnet, dist, r + tw / 2.0 + CLR, ta))
        for (vx, vy, vd, vnet) in self.vias:
            if vnet == net:
                continue
            dist = math.hypot(x - vx, y - vy)
            if dist < r + vd / 2.0 + CLR:
                out.append(('via', vnet, dist, r + vd / 2.0 + CLR, (vx, vy)))
        for xx, yy in ((x, y),):
            e = min(xx, yy, self.w - xx, self.h - yy)
            if e < r + EDGE_CLR:
                out.append(('edge', '', e, r + EDGE_CLR, (x, y)))
        return out

    def commit_track(self, a, b, width, net, layer):
        self.tracks.append((a, b, width, net, layer))

    def commit_via(self, x, y, d, net):
        self.vias.append((x, y, d, net))

    def report(self):
        return self.conflicts
