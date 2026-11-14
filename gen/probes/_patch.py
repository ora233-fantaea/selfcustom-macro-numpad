import re, io
p = 'numpad/gen/route.py'
s = open(p, encoding='utf-8').read()

NEW = {}

NEW['route_usb'] = '''def route_usb():
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
    for pn, ref in (('A5', 'R3'), ('B5', 'R4')):
        a, b = pad('J1', pn), pad(ref, 1)
        route('CC1' if pn == 'A5' else 'CC2', [a, b], SIG)
    # VBUS：4 个电源脚并到 y=1.90 的干线，往东喂 ESD 的 5 脚、往西喂保险丝
    vb = [pad('J1', pn) for pn in ('A4', 'A9', 'B4', 'B9')]
    lo, hi = min(q[0] for q in vb), max(q[0] for q in vb)
    for a in vb:
        route('VBUS', [a, (a[0], 1.90)], SIG, PWR_W)
    route('VBUS', [(lo, 1.90), (hi, 1.90)], SIG, PWR_W)
    u5 = pad('U4', 5)
    route('VBUS', [(hi, 1.90), (u5[0] + 0.9, 1.90), (u5[0] + 0.9, u5[1]), u5], SIG, PWR_W)
    f1 = pad('J2', 1)
    route('VBUS', [(lo, 1.90), (f1[0] + 1.4, 1.90), (f1[0] + 1.4, f1[1]), f1], SIG, PWR_W)
'''

NEW['route_power'] = '''def route_power():
    u3v, u3c, u3o = pad('U3', 1), pad('U3', 3), pad('U3', 5)
    f2, c1, c2 = pad('J2', 2), pad('C1', 1), pad('C2', 1)
    route('5V', [f2, (f2[0] + 0.9, f2[1]), (f2[0] + 0.9, u3v[1]), u3v], SIG, PWR_W)
    route('5V', [(u3c[0], u3c[1]), (u3c[0] + 1.5, u3c[1]), (u3c[0] + 1.5, u3v[1]), u3v], SIG, PWR_W)
    route('5V', [(c1[0], c1[1]), (c1[0], c1[1] + 1.2), (f2[0], c1[1] + 1.2)], SIG, PWR_W)
    t = escape('45', 'E', 45 - 43, 'VREG_1V1')
    route('VREG_1V1', [(t[0], t[1]), (c2[0], t[1])], AUX2)
'''

NEW['route_decoupling'] = '''def route_decoupling():
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
        escape(pin, side, {1:0,10:1,22:2,33:3,42:4,43:5,44:6,48:7,49:8,50:9}[pin], '3V3')
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
'''

NEW['route_ctrl'] = '''def route_ctrl():
    """没有 SWD 排针和复位键：USB 引导即可烧录，这里留空。
    需要调试时在 TP4/TP5 旁边飞线，或者下一版再加回 3 个测试点。"""
    return
'''

NEW['route_boot_pull'] = '''def route_boot_pull():
    """QSPI_SS 上拉 R2 + BOOTSEL 短接焊盘 TP4"""
    r2a, r2b = pad('R2', 1), pad('R2', 2)
    tp4 = pad('TP4', 1)
    via('QSPI_SS', r2b[0], r2b[1] - 0.85)
    route('QSPI_SS', [(r2b[0], r2b[1]), (r2b[0], r2b[1] - 0.85)], STUB)
    via('3V3', r2a[0], r2a[1] - 0.85)
    route('3V3', [(r2a[0], r2a[1]), (r2a[0], r2a[1] - 0.85)], STUB)
    route('BOOT_N', [tp4, (tp4[0], tp4[1] - 1.0)], STUB)
    via('BOOT_N', tp4[0], tp4[1] - 1.0)
'''

for name, body in NEW.items():
    pat = re.compile(r'def %s\(\):.*?(?=\ndef |\nif __name__)' % name, re.S)
    assert pat.search(s), name
    s = pat.sub(body + '\n', s, count=1)

# 3V3 平面 + GND 平面
s = s.replace('''    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(net('GND'))''', '''    for layer, netname in ((pcbnew.In1_Cu, 'GND'), (pcbnew.In2_Cu, '3V3')):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(net(netname))''')
s = s.replace('''    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.20))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25))
    z.SetThermalReliefSpokeWidth(MM(0.40))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.Outline().NewOutline()
    for x, y in [(0, 0), (w, 0), (w, h), (0, h)]:
        z.Outline().Append(MM(x), MM(y))
    board.Add(z)''', '''        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.20))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.40))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.Outline().NewOutline()
        for x, y in [(0, 0), (w, 0), (w, h), (0, h)]:
            z.Outline().Append(MM(x), MM(y))
        board.Add(z)''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('route functions rewritten')
