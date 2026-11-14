# -*- coding: utf-8 -*-
"""把 .kicad_pcb 画成 PNG（自检用，不依赖 KiCad 的渲染管线）。

用法：
    python.exe render.py                       # 默认 顶/底 两张
    python.exe render.py --side both --zoom 6
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew                                          # noqa: E402
from PIL import Image, ImageDraw, ImageFont            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
PCB = os.path.join(ROOT, 'numpad', 'kicad', 'numpad.kicad_pcb')
OUTDIR = os.path.join(ROOT, 'numpad', 'kicad', 'img')

SS = 3          # 超采样倍数

COL_F_CU = (200, 60, 50)
COL_IN3_CU = (235, 140, 40)
COL_IN4_CU = (170, 90, 200)
COL_B_CU = (50, 90, 200)
COL_SILK = (225, 225, 225)
COL_FAB = (90, 90, 90)
COL_CRT = (240, 200, 60)
COL_EDGE = (255, 240, 120)
COL_PAD = (215, 175, 60)
COL_DRILL = (25, 25, 25)
COL_TEXT = (120, 220, 120)
COL_ZONE = (52, 78, 60)      # GND 铺铜（暗绿，走线/焊盘压在上面）


def track_width(t):
    """取线宽。KiCad 10 里 PCB_VIA 的宽度按层不同，不带层会触发断言弹窗。"""
    if isinstance(t, pcbnew.PCB_VIA):
        return t.GetWidth(pcbnew.F_Cu)
    return t.GetWidth()


def mm(v):
    return pcbnew.ToMM(v)


class Canvas:
    def __init__(self, w_mm, h_mm, zoom, region=None, margin=3.0):
        self.zoom = zoom * SS
        self.region = region or (0.0, 0.0, w_mm, h_mm)
        self.margin = margin
        rw = self.region[2] - self.region[0]
        rh = self.region[3] - self.region[1]
        self.w = int((rw + 2 * margin) * self.zoom)
        self.h = int((rh + 2 * margin) * self.zoom)
        self.wmm = w_mm
        self.img = Image.new('RGB', (self.w, self.h), (18, 18, 22))
        self.d = ImageDraw.Draw(self.img, 'RGBA')

    def p(self, x, y):
        return ((x - self.region[0] + self.margin) * self.zoom,
                (y - self.region[1] + self.margin) * self.zoom)

    def line(self, x1, y1, x2, y2, color, width_mm):
        w = max(1, int(width_mm * self.zoom))
        self.d.line([self.p(x1, y1), self.p(x2, y2)], fill=color, width=w)

    def rect(self, cx, cy, w, h, ang, color, fill=True, width_mm=0.1, r=0.0):
        pts = []
        hw, hh = w / 2.0, h / 2.0
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        for dx, dy in corners:
            # KiCad 角度为逆时针（y 向下时用 -sin）
            rx = dx * ca + dy * sa
            ry = -dx * sa + dy * ca
            pts.append(self.p(cx + rx, cy + ry))
        if fill:
            self.d.polygon(pts, fill=color)
        else:
            w_px = max(1, int(width_mm * self.zoom))
            self.d.line(pts + [pts[0]], fill=color, width=w_px)

    def circle(self, cx, cy, rad, color, fill=True, width_mm=0.1):
        x0, y0 = self.p(cx - rad, cy - rad)
        x1, y1 = self.p(cx + rad, cy + rad)
        if fill:
            self.d.ellipse([x0, y0, x1, y1], fill=color)
        else:
            self.d.ellipse([x0, y0, x1, y1], outline=color,
                           width=max(1, int(width_mm * self.zoom)))

    def poly(self, pts_mm, color, fill=True, width_mm=0.1):
        pts = [self.p(x, y) for x, y in pts_mm]
        if len(pts) < 2:
            return
        if fill and len(pts) >= 3:
            self.d.polygon(pts, fill=color)
        else:
            self.d.line(pts + [pts[0]], fill=color,
                        width=max(1, int(width_mm * self.zoom)))

    def save(self, path):
        self.img.resize((self.w // SS, self.h // SS), Image.LANCZOS).save(path)


def shape_points(shape):
    """把 PCB_SHAPE 转成点列（mm）；文字之类的非图形对象返回 []。"""
    if not hasattr(shape, 'GetShape'):
        return []
    kind = shape.GetShape()
    if kind == pcbnew.SHAPE_T_SEGMENT:
        a, b = shape.GetStart(), shape.GetEnd()
        return [(mm(a.x), mm(a.y)), (mm(b.x), mm(b.y))]
    if kind == pcbnew.SHAPE_T_RECT:
        a, b = shape.GetStart(), shape.GetEnd()
        x1, y1, x2, y2 = mm(a.x), mm(a.y), mm(b.x), mm(b.y)
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    if kind == pcbnew.SHAPE_T_CIRCLE:
        c, e = shape.GetCenter(), shape.GetEnd()
        r = math.hypot(mm(e.x - c.x), mm(e.y - c.y))
        n = 40
        cx, cy = mm(c.x), mm(c.y)
        return [(cx + r * math.cos(2 * math.pi * i / n),
                 cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    if kind == pcbnew.SHAPE_T_ARC:
        c = shape.GetCenter()
        s, e = shape.GetStart(), shape.GetEnd()
        cx, cy = mm(c.x), mm(c.y)
        r = math.hypot(mm(s.x - c.x), mm(s.y - c.y))
        a0 = math.atan2(mm(s.y - c.y), mm(s.x - c.x))
        a1 = math.atan2(mm(e.y - c.y), mm(e.x - c.x))
        while a1 <= a0:
            a1 += 2 * math.pi
        n = max(6, int((a1 - a0) * 20))
        return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
                 cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    if kind == pcbnew.SHAPE_T_POLY:
        poly = shape.GetPolyShape()
        if poly.OutlineCount() == 0:
            return []
        chain = poly.Outline(0)
        return [(mm(chain.CPoint(i).x), mm(chain.CPoint(i).y))
                for i in range(chain.PointCount())]
    return []


def draw_pad(cv, pad, color):
    pos = pad.GetPosition()
    cx, cy = mm(pos.x), mm(pos.y)
    sz = pad.GetSize()
    w, h = mm(sz.x), mm(sz.y)
    ang = pad.GetOrientationDegrees()
    shp = pad.GetShape()
    drill = pad.GetDrillSize()
    dw, dh = mm(drill.x), mm(drill.y)

    if shp == pcbnew.PAD_SHAPE_CIRCLE:
        cv.circle(cx, cy, w / 2.0, color)
    elif shp == pcbnew.PAD_SHAPE_OVAL:
        if abs(w - h) < 1e-6:
            cv.circle(cx, cy, w / 2.0, color)
        else:
            cv.rect(cx, cy, w, h, ang, color, r=min(w, h) / 2)
    else:
        cv.rect(cx, cy, w, h, ang, color)

    if dw > 0.01:
        if abs(dw - dh) < 1e-6:
            cv.circle(cx, cy, dw / 2.0, COL_DRILL)
        else:
            cv.rect(cx, cy, dw, dh, ang, COL_DRILL)


def draw_board(board, side, zoom, out, region=None):
    bbx = board.GetBoardEdgesBoundingBox()
    w_mm, h_mm = mm(bbx.GetWidth()), mm(bbx.GetHeight())
    cv = Canvas(w_mm, h_mm, zoom, region=region)

    def vis(layer_name, want):
        return layer_name in want

    fliplr = (side == 'B')
    cu = 'F.Cu' if side == 'F' else 'B.Cu'
    cu_col = COL_F_CU if side == 'F' else COL_B_CU
    silk = 'F.SilkS' if side == 'F' else 'B.SilkS'
    crt = 'F.CrtYd' if side == 'F' else 'B.CrtYd'

    # --- 覆铜（GND 铺铜，画成半透明深色垫底）---
    cu_id = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
    for z in board.Zones():
        if z.GetLayer() != cu_id:
            continue
        try:
            polys = z.GetFilledPolysList(cu_id)
        except Exception:
            continue
        for i in range(polys.OutlineCount()):
            outline = polys.Outline(i)
            pts = [(mm(outline.CPoint(k).x), mm(outline.CPoint(k).y))
                   for k in range(outline.PointCount())]
            if len(pts) >= 3:
                cv.poly(pts, COL_ZONE, fill=True, width_mm=0.0)

    # --- 铜层填充/走线 ---
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            pos = t.GetPosition()
            cv.circle(mm(pos.x), mm(pos.y), mm(t.GetWidth(pcbnew.F_Cu)) / 2, COL_SILK if side == 'F' else COL_SILK)
            cv.circle(mm(pos.x), mm(pos.y), mm(t.GetDrillValue()) / 2, COL_DRILL)
            continue
        if t.GetLayerName() != cu:
            continue
        a, b = t.GetStart(), t.GetEnd()
        cv.line(mm(a.x), mm(a.y), mm(b.x), mm(b.y), cu_col, mm(track_width(t)))

    # --- 焊盘 ---
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.IsOnLayer(pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu):
                draw_pad(cv, pad, COL_PAD)

    # --- 丝印 / 装配 / courtyard ---
    for fp in board.GetFootprints():
        for item in fp.GraphicalItems():
            name = item.GetLayerName()
            if name == silk:
                pts = shape_points(item)
                if len(pts) == 2:
                    cv.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], COL_SILK, 0.12)
                elif len(pts) >= 3:
                    cv.poly(pts, COL_SILK, fill=False, width_mm=0.12)
            elif name == crt:
                pts = shape_points(item)
                if len(pts) == 2:
                    cv.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], COL_CRT + (110,), 0.05)
                elif len(pts) >= 3:
                    cv.poly(pts, COL_CRT + (110,), fill=False, width_mm=0.05)

    for item in board.GetDrawings():
        name = item.GetLayerName()
        if name == 'Edge.Cuts':
            pts = shape_points(item)
            if len(pts) >= 2:
                cv.poly(pts, COL_EDGE, fill=False, width_mm=0.15)
        elif name == silk and isinstance(item, pcbnew.PCB_TEXT):
            pos = item.GetPosition()
            x, y = mm(pos.x), mm(pos.y)
            txt = item.GetText()
            h = mm(item.GetTextHeight()) or 1.4
            n = max(1, len(txt))
            sp = h * 0.72 * cv.zoom
            x0 = x * cv.zoom + cv.margin * cv.zoom - n * sp / 2
            y0 = y * cv.zoom + cv.margin * cv.zoom - h * cv.zoom / 2
            cv.d.text((x0, y0), txt, fill=COL_TEXT)

    cv.save(out)
    print('wrote', out)



def draw_stack(board, zoom, out, region=None):
    """四层铜一次画出来：F 红、In3 橙、In4 紫、B 蓝，过孔画成小圈。
    用来一眼看整板布线密度，比单面图有用。"""
    from design import BOARD_W as bw, BOARD_H as bh
    cv = Canvas(bw, bh, zoom, region)
    cols = {'F.Cu': COL_F_CU, 'In3.Cu': COL_IN3_CU, 'In4.Cu': COL_IN4_CU, 'B.Cu': COL_B_CU}
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            pos = t.GetPosition()
            cv.circle(mm(pos.x), mm(pos.y), mm(t.GetWidth(pcbnew.F_Cu)) / 2, (200, 200, 200))
            cv.circle(mm(pos.x), mm(pos.y), mm(t.GetDrillValue()) / 2, COL_DRILL)
            continue
        c = cols.get(t.GetLayerName())
        if not c:
            continue
        a, b = t.GetStart(), t.GetEnd()
        cv.line(mm(a.x), mm(a.y), mm(b.x), mm(b.y), c, mm(track_width(t)))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            draw_pad(cv, pad, COL_PAD)
        for item in fp.GraphicalItems():
            if item.GetLayerName() == 'Edge.Cuts':
                pts = shape_points(item)
                if len(pts) >= 2:
                    cv.poly(pts, COL_EDGE, fill=False, width_mm=0.15)
    cv.save(out)
    print('wrote', out)


def main():
    zoom = 6.0
    side = 'both'
    region = None
    tag = ''
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--zoom':
            zoom = float(args[i + 1])
        if a == '--side':
            side = args[i + 1]
        if a == '--region':
            region = tuple(float(v) for v in args[i + 1].split(','))
        if a == '--tag':
            tag = '_' + args[i + 1]
    os.makedirs(OUTDIR, exist_ok=True)
    board = pcbnew.LoadBoard(PCB)
    if side in ('F', 'both'):
        draw_board(board, 'F', zoom, os.path.join(OUTDIR, 'top%s.png' % tag), region)
    if side in ('B', 'both'):
        draw_board(board, 'B', zoom, os.path.join(OUTDIR, 'bottom%s.png' % tag), region)
    if side in ('stack', 'both'):
        draw_stack(board, zoom, os.path.join(OUTDIR, 'stack%s.png' % tag), region)


if __name__ == '__main__':
    main()
