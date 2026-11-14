import pcbnew
b = pcbnew.LoadBoard(r'numpad/kicad/numpad.kicad_pcb')
holes = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        d = p.GetDrillSize()
        if d.x > 0 and p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            pos = p.GetPosition()
            holes.append((pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), pcbnew.ToMM(d.x)/2, fp.GetReference()))
print('NPTH 总数', len(holes))
# 键区 y=14..131 里，找一条横向完全无孔的空走廊（按 x 采样）
H = [h for h in holes if 14.0 < h[1] < 131.5]
print('键区内的孔', len(H))
x = 0.0
free = []
step = 0.1
import math
while x < 107.25:
    ok = True
    for hx, hy, r, ref in H:
        if abs(x - hx) < r + 0.55:
            ok = False
            break
    free.append((x, ok))
    x += step
runs = []
cur = None
for xx, ok in free:
    if ok and cur is None:
        cur = xx
    elif not ok and cur is not None:
        runs.append((cur, xx - step)); cur = None
if cur is not None:
    runs.append((cur, free[-1][0]))
runs = [(a, b) for a, b in runs if b - a > 1.2]
print('可用垂直走廊（宽>1.2mm）：')
for a, b in sorted(runs, key=lambda t: -(t[1]-t[0]))[:12]:
    print('  %.2f .. %.2f  宽 %.2f' % (a, b, b - a))
