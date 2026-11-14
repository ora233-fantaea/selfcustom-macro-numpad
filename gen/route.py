# -*- coding: utf-8 -*-
"""QFN 扇出 + 电子舱布线（3 排交错打孔；西侧按"先北后西"的车道表走）。

坐标约定
--------
* QFN U1 在 (67, 9) 转 90°：南排 1-14 (y=12.44)、西排 15-28 (x=63.56)、
  北排 29-42 (y=5.56)、东排 43-56 (x=70.44)，间距 0.4 mm。
* 扇出：焊盘 -> B 面短线 -> 过孔，第 i 个脚用第 i%3 排（1.0/2.0/3.0 mm）。
  同一排相邻过孔间隔 1.2 mm，中间能过 0.2 mm 线。
* 行引出：6 根各自在 In2 下到不同深度再西折（先折的最靠西），互不相交。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew                                          # noqa: E402
import design as D                                     # noqa: E402
import geom                                            # noqa: E402

PCB = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                   'numpad', 'kicad', 'numpad.kicad_pcb')
TRACK_W, PWR_W = 0.20, 0.40
VIA_D, VIA_DRILL = 0.45, 0.25
SIG, STUB, AUX, AUX2 = 'F.Cu', 'B.Cu', 'In3.Cu', 'In4.Cu'
ROW_BUS_DY, COL_BUS_DX = 3.00, 8.90

board = pcbnew.LoadBoard(PCB)
LAY = geom.Layout(D.BOARD_W, D.BOARD_H)
CONFLICTS = []


def _load_pads():
    """把板上所有焊盘/孔灌进几何检查器"""
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pos = p.GetPosition()
            sz = p.GetSize()
            dr = p.GetDrillSize()
            x, y = mm(pos.x), mm(pos.y)
            w, h = mm(sz.x), mm(sz.y)
            rot = p.GetOrientationDegrees()
            net = p.GetNetname()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                LAY.add_pad(x, y, w, h, rot, '', '', is_hole=True, drill=mm(dr.x))
                continue
            pth = (p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
            if pth:
                for lay in ('F.Cu', 'In1.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'):
                    LAY.add_pad(x, y, w, h, rot, net, lay)
            else:
                lay = 'B.Cu' if p.IsOnLayer(pcbnew.B_Cu) else 'F.Cu'
                LAY.add_pad(x, y, w, h, rot, net, lay)


def MM(v):
    return pcbnew.FromMM(v)


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def mm(v):
    return pcbnew.ToMM(v)


def net(name):
    n = board.FindNet(name)
    if n is None:
        raise KeyError('network %r not in board' % name)
    return n


def pad(ref, num):
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise KeyError('footprint %r not found' % ref)
    hits = [p for p in fp.Pads() if p.GetNumber() == str(num)]
    if not hits:
        raise KeyError('pad %s.%s not found' % (ref, num))
    pos = hits[0].GetPosition()
    return (mm(pos.x), mm(pos.y))


def _emit(name, pts, layer, width):
    n = net(name)
    lay = board.GetLayerID(layer)
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a))
        t.SetEnd(V(*b))
        t.SetWidth(MM(width))
        t.SetLayer(lay)
        t.SetNet(n)
        board.Add(t)
        LAY.commit_track(a, b, width, name, layer)


def _score(name, pts, layer, width):
    bad = 0
    worst = 0.0
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
            continue
        for c in LAY.check_track(a, b, width, name, layer):
            bad += 1
            worst = max(worst, c[3] - c[2])
    return bad, worst


def route(name, pts, layer, width=TRACK_W, auto=False):
    """放一段折线；auto=True 时整体做 ±0.6 mm 的平移试错，取最先不撞的"""
    pts = [tuple(p) for p in pts]
    bad, worst = _score(name, pts, layer, width)
    if bad and auto:
        best = (bad, worst, pts)
        for step in (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8):
            for sgn in (1, -1):
                for axis in (1, 0):
                    cand = [(p[0] + (sgn * step if axis == 0 else 0),
                             p[1] + (sgn * step if axis == 1 else 0)) for p in pts]
                    b2, w2 = _score(name, cand, layer, width)
                    if b2 == 0:
                        _emit(name, cand, layer, width)
                        return cand
                    if (b2, w2) < (best[0], best[1]):
                        best = (b2, w2, cand)
        pts = best[2]
        bad, worst = best[0], best[1]
    if bad:
        detail = []
        for a, b in zip(pts, pts[1:]):
            for c in LAY.check_track(a, b, width, name, layer):
                detail.append('%s@(%.2f,%.2f) 差%.3f' % (c[0], c[4][0], c[4][1], c[3] - c[2]))
        CONFLICTS.append((name, layer, len(detail), round(worst, 3), pts[0], detail[:3]))
    _emit(name, pts, layer, width)
    return pts


def via(name, x, y, dia=VIA_D, drill=VIA_DRILL):
    bad = LAY.check_via(x, y, dia, name)
    if bad:
        CONFLICTS.append((name, 'via', len(bad),
                          round(max(c[3] - c[2] for c in bad), 3), (x, y),
                          ['%s@(%.2f,%.2f) 差%.3f' % (c[0], c[4][0], c[4][1], c[3] - c[2])
                           for c in bad[:3]]))
    LAY.commit_via(x, y, dia, name)
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetWidth(MM(dia))
    v.SetDrill(MM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net(name))
    board.Add(v)


ROWS = ['ROW%d' % i for i in range(6)]
COLS = ['COL%d' % i for i in range(5)]


def row_center_y(r):
    return D.MY + (r + 0.5) * D.PITCH


def col_bus_x(c):
    return D.MX + (c + 0.5) * D.PITCH + COL_BUS_DX


def escape(pin, side, idx, name, pitch=0.40):
    """焊盘 -> B 面短线 -> 过孔（3 排交错），返回过孔坐标。

    idx 由 pin 与所在边推出（pitch=0.4 mm），保证同一排里相邻过孔间距 1.2 mm。
    """
    p = pad('U1', pin)
    base = {'S': 1, 'W': 15, 'N': 29, 'E': 43}[side]
    idx = int(pin) - base
    d = 1.30 + 1.10 * (idx % 3) + 0.80 * (idx // 3)
    if side == 'E':
        t = (p[0] + d, p[1])
    elif side == 'W':
        t = (p[0] - d, p[1])
    elif side == 'N':
        t = (p[0], p[1] - d)
    else:
        t = (p[0], p[1] + d)
    route(name, [p, t], STUB)
    via(name, t[0], t[1])
    return t


# ------------------------------------------------------------------ 矩阵
def route_matrix():
    col_vias = {c: [] for c in range(5)}
    for name, col, row, w, h, r, cc in D.KEYS:
        cx, cy = D.key_center(col, row, w, h)
        p2 = pad(D.SW_REF[name], 2)
        bx = col_bus_x(cc)
        sy = p2[1] + 1.50
        route(COLS[cc], [p2, (p2[0], sy), (bx, sy)], STUB)
        via(COLS[cc], bx, sy)
        col_vias[cc].append((bx, sy))
    for cc in range(5):
        ys = sorted(p[1] for p in col_vias[cc])
        x = col_bus_x(cc)
        route(COLS[cc], [(x, 15.60), (x, ys[-1])], AUX)

    row_pts = {r: [] for r in range(6)}
    for name, col, row, w, h, r, cc in D.KEYS:
        cx, cy = D.key_center(col, row, w, h)
        p1 = pad(D.DIODE_REF[name], 1)
        by = row_center_y(r) + ROW_BUS_DY
        route(ROWS[r], [p1, (p1[0], by)], STUB)
        row_pts[r].append((p1[0], by))
    for r in range(6):
        xs = sorted(p[0] for p in row_pts[r])
        by = row_center_y(r) + ROW_BUS_DY
        route(ROWS[r], [(xs[0], by), (max(xs[-1], 69.5), by)], STUB)


def route_rows_to_mcu():
    """行：3 排交错打孔 -> In2 下到不同深度 -> 各自向西 -> 下到行总线"""
    for r in range(6):
        t = escape(str(D.GPIO_PIN[D._ROW_GPIO[r]]), 'S', r, ROWS[r])
        k = 5 - r                      # 行 5 最浅、最靠西，逐行往东错开
        yt = 17.20 + 0.55 * k
        xd = 24.00 + 0.60 * k          # x=22.1..28.0 是键区唯一横向无孔的走廊
        by = row_center_y(r) + ROW_BUS_DY
        route(ROWS[r], [(t[0], t[1]), (t[0], yt), (xd, yt), (xd, by)], SIG)
        via(ROWS[r], xd, by)


def route_cols_to_mcu():
    """列 0-2：南侧出线，向西错层拐弯；列 3/4：西侧脚北绕再东行"""
    for i, cc in enumerate([0, 1, 2]):
        p = pad('U1', str(D.GPIO_PIN[D._COL_GPIO[cc]]))
        vx = p[0] + (-0.30, 0.10, 0.50)[i]
        ly = 14.20 + 0.60 * (2 - i)
        route(COLS[cc], [p, (p[0], p[1] + 0.55), (vx, ly)], STUB)
        via(COLS[cc], vx, ly)
        bx = col_bus_x(cc)
        route(COLS[cc], [(vx, ly), (bx, ly), (bx, 15.60)], AUX)
    for i, cc in enumerate([3, 4]):
        g = D._COL_GPIO[cc]
        p = pad('U1', str(D.GPIO_PIN[g]))
        y = 2.60 + 0.55 * i
        t = (p[0] - 1.00 - 0.90 * i, p[1])
        route(COLS[cc], [p, t], STUB)
        via(COLS[cc], t[0], t[1])
        bx = col_bus_x(cc)
        route(COLS[cc], [(t[0], t[1]), (t[0], y), (bx, y), (bx, 15.60)], AUX)
        via(COLS[cc], bx, 15.60)


def route_encoder():
    for pin, name, ly, tgt in (('15', 'ENC_A', 12.60, pad('ENC1', 'A')),
                               ('16', 'ENC_B', 12.20, pad('ENC1', 'B'))):
        t = escape(pin, 'W', {'15': 0, '16': 1}[pin], name)
        ex, ey = tgt[0] - 1.6, tgt[1]
        via(name, ex, ey)
        route(name, [(t[0], t[1]), (t[0], ly), (ex, ly), (ex, ey)], SIG)
        route(name, [(ex, ey), (tgt[0], tgt[1])], STUB)
    s2 = pad('ENC1', 'S2')
    route('COL0', [s2, (col_bus_x(0), s2[1])], STUB)
    s1 = pad('ENC1', 'S1')
    d27 = pad('D27', 2)
    route('K_ENC1_A', [s1, (s1[0] + 1.2, s1[1]), (s1[0] + 1.2, 12.00),
                       (d27[0], 12.00), d27], AUX)


def route_qspi():
    order = ['56', '55', '54', '53', '52', '51']   # 先按引脚，稍后按 x 重排
    names = {'56': 'QSPI_SS', '53': 'QSPI_SD0', '55': 'QSPI_SD1',
             '54': 'QSPI_SD2', '52': 'QSPI_SCLK', '51': 'QSPI_SD3'}
    fpad = {'56': '1', '53': '2', '55': '3', '54': '5', '52': '6', '51': '7'}
    esc = {pin: escape(pin, 'E', 0, names[pin]) for pin in order}
    order = sorted(order, key=lambda p: esc[p][0])
    for k, pin in enumerate(order):
        n = names[pin]
        t = esc[pin]
        q = pad('U2', fpad[pin])
        north = fpad[pin] in ('5', '6', '7')
        qy = q[1] - 0.85 if north else q[1] + 0.85
        route(n, [(q[0], q[1]), (q[0], qy)], STUB)
        via(n, q[0], qy)
        lvl = 6.40 + 0.55 * k
        route(n, [(t[0], t[1]), (t[0], lvl), (q[0], lvl), (q[0], qy)], AUX)


def route_usb():
    """USB 前端：连接器 4 个信号脚用交错过孔下 In3 换位，ESD 在连接器东侧，
    27R 紧跟 ESD，CC 下拉直接吊在对应焊盘正下方（一路直下，不拐弯）。"""
    # 4 个信号脚：竖直下探到错开的过孔（互不重叠），再在 In3 上换位
    drops = {'A6': 2.20, 'B6': 2.60, 'A7': 3.40, 'B7': 4.00}
    dp_pts, dm_pts = [], []
    for pn, vy in drops.items():
        a = pad('J1', pn)
        route('USB_DP_CON' if pn in ('A6', 'B6') else 'USB_DM_CON',
              [(a[0], a[1]), (a[0], vy)], SIG)
        via('USB_DP_CON' if pn in ('A6', 'B6') else 'USB_DM_CON', a[0], vy)
        (dp_pts if pn in ('A6', 'B6') else dm_pts).append((a[0], vy))
    # In3 上并到 U4 的 1 脚（DP）与 3 脚（DM）西侧
    u1, u3 = pad('U4', 1), pad('U4', 3)
    for pts, n, tgt in ((dp_pts, 'USB_DP_CON', u1), (dm_pts, 'USB_DM_CON', u3)):
        ys = sorted(set(round(q[1], 2) for q in pts))
        x0 = max(q[0] for q in pts)
        route(n, [(x0, ys[0]), (x0, ys[-1])], AUX)          # 同网络竖段并线
        for q in pts:
            if abs(q[1] - ys[0]) > 1e-6:
                route(n, [q, (q[0], ys[0])], AUX)
        route(n, [(x0, ys[0]), (tgt[0] - 0.8, ys[0]),
                  (tgt[0] - 0.8, tgt[1]), tgt], AUX)
    # 27R 两端：ESD 输出 -> R5/R6 -> QFN 的 46/47
    for pout, rref, n in (('6', 'R5', 'USB_DP'), ('4', 'R6', 'USB_DM')):
        a, b = pad('U4', pout), pad(rref, 1)
        route(n.replace('USB_', 'USB_') + '_CON', [a, (a[0] + 0.6, a[1]), (a[0] + 0.6, b[1]), b], SIG)
    for rref, pin, n in (('R5', '47', 'USB_DP'), ('R6', '46', 'USB_DM')):
        b = pad(rref, 2)
        via(n, b[0], b[1])
        route(n, [(b[0], b[1]), (b[0], b[1])], AUX)
        t = escape(pin, 'E', int(pin) - 43, n)
        route(n, [(b[0], b[1]), (68.90, b[1]), (68.90, t[1]), t], AUX)
    # CC 下拉：连接器 CC 焊盘正下方就是电阻，直下
    for pn, ref, ly in (('A5', 'R3', 3.35), ('B5', 'R4', 3.70)):
        a, b = pad('J1', pn), pad(ref, 1)
        route('CC1' if pn == 'A5' else 'CC2',
              [a, (a[0], ly), (b[0] + 0.9, ly), (b[0] + 0.9, b[1]), b], SIG)
    # VBUS：4 个电源脚并到 y=2.90 的干线，往东喂 ESD 的 5 脚、往西喂保险丝
    vb = [pad('J1', pn) for pn in ('A4', 'A9', 'B4', 'B9')]
    lo, hi = min(q[0] for q in vb), max(q[0] for q in vb)
    for a in vb:
        route('VBUS', [a, (a[0], 2.90)], SIG, PWR_W)
    route('VBUS', [(lo, 2.90), (hi, 2.90)], SIG, PWR_W)
    u5 = pad('U4', 5)
    route('VBUS', [(hi, 2.90), (u5[0] + 0.9, 2.90), (u5[0] + 0.9, u5[1]), u5], SIG, PWR_W)
    f1 = pad('J2', 1)
    route('VBUS', [(lo, 2.90), (f1[0] + 1.4, 2.90), (f1[0] + 1.4, f1[1]), f1], SIG, PWR_W)


def route_power():
    u3v, u3c, u3o = pad('U3', 1), pad('U3', 3), pad('U3', 5)
    f2, c1, c2 = pad('J2', 2), pad('C1', 1), pad('C2', 1)
    route('5V', [f2, (f2[0] + 0.9, f2[1]), (f2[0] + 0.9, u3v[1]), u3v], SIG, PWR_W)
    route('5V', [(u3c[0], u3c[1]), (u3c[0] + 1.5, u3c[1]), (u3c[0] + 1.5, u3v[1]), u3v], SIG, PWR_W)
    route('5V', [(c1[0], c1[1]), (c1[0], c1[1] + 1.2), (f2[0], c1[1] + 1.2)], SIG, PWR_W)
    t = escape('45', 'E', 45 - 43, 'VREG_1V1')
    route('VREG_1V1', [(t[0], t[1]), (c2[0], t[1])], AUX2)


def route_decoupling():
    """3V3 全部就近打孔进 In2 平面，不再拉总线；1V1 只有 3 个脚 + 3 颗电容，
    单独在 In4 上走一条短总线。"""
    for pin in ['1', '10', '22', '33', '42', '43', '44', '48', '49', '50']:
        pp = pad('U1', pin)
        if abs(pp[1] - 12.44) < 0.1:
            side = 'S'
        elif abs(pp[1] - 5.56) < 0.1:
            side = 'N'
        elif pp[0] > 67.0:
            side = 'E'
        else:
            side = 'W'
        escape(pin, side, {'1':0,'10':1,'22':2,'33':3,'42':4,'43':5,'44':6,'48':7,'49':8,'50':9}[pin], '3V3')
    pts = []
    for idx, pin in enumerate(['23', '45', '50']):
        if pin == '50':
            continue
        pp = pad('U1', pin)
        side = 'E' if pp[0] > 67.0 else ('S' if abs(pp[1] - 12.44) < 0.1 else 'W')
        pts.append(escape(pin, side, idx + 20, 'VREG_1V1'))
    for ref in ('C2', 'C7', 'C13', 'C14', 'C11', 'C12', 'C3', 'C5', 'C4', 'C6', 'C8'):
        pass
    for ref in ('C2',):
        p = pad(ref, 1)
        via('3V3', p[0], p[1])
    for ref in ('C7', 'C14'):
        p = pad(ref, 1)
        via('VREG_1V1', p[0], p[1])
    if len(pts) >= 2:
        route('VREG_1V1', [pts[0], pts[1]], AUX2)


def route_clock():
    """XIN 走 10.2 车道，XOUT 走 10.8 车道，R1 在晶振西侧，C9/C10 就近"""
    xin = escape('20', 'W', 20 - 15, 'XIN')
    xout = escape('21', 'W', 21 - 15, 'XOUT_C')
    y1, y3 = pad('Y1', 1), pad('Y1', 3)
    r1a, r1b = pad('R1', 1), pad('R1', 2)
    c9 = pad('C9', 1)
    c10 = pad('C10', 1)
    # XIN：QFN -> 10.2 车道 -> 晶振 pin1，顺带下拉 C9
    route('XIN', [(xin[0], xin[1]), (xin[0], 10.20), (y1[0], 10.20)], AUX)
    route('XIN', [(y1[0], 10.20), (y1[0], y1[1])], AUX)
    route('XIN', [(c9[0], 10.20), c9], AUX)
    via('XIN', c9[0], c9[1])
    # XOUT：QFN -> 10.8 车道 -> R1.pad1
    route('XOUT_C', [(xout[0], xout[1]), (r1a[0], 10.80), (r1a[0], r1a[1])], AUX)
    route('XOUT_C', [(r1a[0], r1a[1]), r1a], AUX)
    # R1.pad2 -> 晶振 pin3；C10 挂在 XOUT 侧
    route('XOUT_C', [r1b, (y3[0], r1b[1]), (y3[0], y3[1])], AUX)
    via('XOUT_C', y3[0], y3[1])
    route('XOUT', [(r1a[0], r1a[1]), (r1a[0], 13.00), (c10[0], 13.00), c10], AUX)
    via('XOUT', c10[0], c10[1])


def route_ctrl():
    """没有 SWD 排针和复位键：USB 引导即可烧录，这里留空。
    需要调试时在 TP4/TP5 旁边飞线，或者下一版再加回 3 个测试点。"""
    return


def route_boot_pull():
    """QSPI_SS 上拉 R2 + BOOTSEL 短接焊盘 TP4"""
    r2a, r2b = pad('R2', 1), pad('R2', 2)
    tp4 = pad('TP4', 1)
    via('QSPI_SS', r2b[0], r2b[1] - 0.85)
    route('QSPI_SS', [(r2b[0], r2b[1]), (r2b[0], r2b[1] - 0.85)], STUB)
    via('3V3', r2a[0], r2a[1] - 0.85)
    route('3V3', [(r2a[0], r2a[1]), (r2a[0], r2a[1] - 0.85)], STUB)
    route('BOOT_N', [tp4, (tp4[0], tp4[1] - 1.0)], STUB)
    via('BOOT_N', tp4[0], tp4[1] - 1.0)


def route_gnd():
    """所有 GND 焊盘就近打孔落 In1 平面；QFN 散热焊盘打 3x3 过孔阵列"""
    # 散热焊盘
    for dx in (-1.2, 0.0, 1.2):
        for dy in (-1.2, 0.0, 1.2):
            via('GND', 67.0 + dx, 9.0 + dy)
    plane_pads = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith('D') or ref.startswith('SW'):
            continue
        for p in fp.Pads():
            if p.GetNetname() != 'GND':
                continue
            s = p.GetSize()
            w, h = mm(s.x), mm(s.y)
            pos = p.GetPosition()
            x, y = mm(pos.x), mm(pos.y)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                continue
            plane_pads.append((ref, x, y, w, h, fp.GetOrientationDegrees()))
    for ref, x, y, w, h, rot in plane_pads:
        if w >= h:          # 水平焊盘：往 ±x 方向出线
            dx, dy = (0.75, 0.0)
        else:
            dx, dy = (0.0, 0.75)
        # 朝远离元件中心的方向出
        fp = board.FindFootprintByReference(ref)
        c = fp.GetPosition()
        cx, cy = mm(c.x), mm(c.y)
        if dx and x < cx:
            dx = -dx
        if dy and y < cy:
            dy = -dy
        vx, vy = x + dx, y + dy
        if vy < 0.80:                       # 后缘 USB-C 附近，往板内推
            vy = y - dy
        if vx < 0.80:
            vx = x - dx
        if not LAY.check_via(vx, vy, VIA_D, 'GND'):
            route('GND', [(x, y), (vx, vy)], STUB)
            via('GND', vx, vy)
        else:
            placed = False
            for ox, oy in ((0, 0.7), (0, -0.7), (0.7, 0), (-0.7, 0), (0.5, 0.5), (-0.5, 0.5),
                           (0.5, -0.5), (-0.5, -0.5)):
                tx, ty = vx + ox, vy + oy
                if not LAY.check_via(tx, ty, VIA_D, 'GND'):
                    route('GND', [(x, y), (tx, ty)], STUB)
                    via('GND', tx, ty)
                    placed = True
                    break


def add_zones():
    w, h = D.BOARD_W, D.BOARD_H
    for layer, netname in ((pcbnew.In1_Cu, 'GND'), (pcbnew.In2_Cu, '3V3')):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        _ls = pcbnew.LSET()
        _ls.AddLayer(layer)
        z.SetLayerSet(_ls)
        z.SetNet(net(netname))
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.20))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.40))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.Outline().NewOutline()
        for x, y in [(0, 0), (w, 0), (w, h), (0, h)]:
            z.Outline().Append(MM(x), MM(y))
        board.Add(z)


def main():
    _load_pads()
    board.SetCopperLayerCount(6)
    route_matrix()
    route_rows_to_mcu()
    route_cols_to_mcu()
    route_encoder()
    route_qspi()
    route_usb()
    route_power()
    route_decoupling()
    route_clock()
    route_ctrl()
    route_boot_pull()
    route_gnd()
    board.BuildConnectivity()
    add_zones()
    zs = list(board.Zones())
    print('覆铜区：' + ', '.join('%s@%s' % (z.GetNetname(), z.GetLayerName()) for z in zs))
    pcbnew.ZONE_FILLER(board).Fill(zs)
    pcbnew.SaveBoard(PCB, board)
    tr = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    vi = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    print('走线 %d 段，过孔 %d 个' % (len(tr), len(vi)))
    if CONFLICTS:
        print('几何预检发现 %d 处冲突：' % len(CONFLICTS))
        seen = {}
        for c in CONFLICTS:
            k = (c[0], c[1])
            seen[k] = max(seen.get(k, 0), c[2])
        shown = set()
        for c in CONFLICTS:
            k = (c[0], c[1])
            if k in shown:
                continue
            shown.add(k)
            print('   %-11s %-7s @(%.1f,%.1f) %d 处: %s' % (c[0], c[1], c[4][0], c[4][1], c[2], '; '.join(c[5])))
    else:
        print('几何预检：全部通过')


if __name__ == '__main__':
    main()
