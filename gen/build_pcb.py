# -*- coding: utf-8 -*-
"""从 design.py 生成 numpad 的 .kicad_pcb（叠放 + 板框 + 网络），布线在 route.py。

用法：
    python.exe numpad/gen/build_pcb.py            # 完整（叠放 + 布线）
    python.exe numpad/gen/build_pcb.py --place    # 只叠放不布线
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D                                    # noqa: E402
import pcbnew                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))          # E:\ESP-USB-HUB
FP_LIB = os.path.join(ROOT, 'tools', 'kicad-libs', 'kicad-footprints-master')
LOCAL_FP = os.path.join(ROOT, 'numpad', 'lib', 'numpad.pretty')
OUT_DIR = os.path.join(ROOT, 'numpad', 'kicad')
PCB_PATH = os.path.join(OUT_DIR, 'numpad.kicad_pcb')

MM = pcbnew.FromMM
TOMM = pcbnew.ToMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# ----------------------------------------------------------------- 板框
def rounded_rect(board, w, h, r, layer=pcbnew.Edge_Cuts, width=0.1):
    """圆角矩形板框（真圆弧）。"""
    r = min(r, w / 2, h / 2)
    segs = [
        ((r, 0), (w - r, 0)),
        ((w, r), (w, h - r)),
        ((w - r, h), (r, h)),
        ((0, h - r), (0, r)),
    ]
    for (x1, y1), (x2, y2) in segs:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x1, y1))
        s.SetEnd(V(x2, y2))
        s.SetLayer(layer)
        s.SetWidth(MM(width))
        board.Add(s)

    arcs = [
        ((r, r), (r, 0), (0, r)),                 # 左上
        ((w - r, r), (w, r), (w - r, 0)),         # 右上
        ((w - r, h - r), (w - r, h), (w, h - r)),  # 右下
        ((r, h - r), (0, h - r), (r, h)),         # 左下
    ]
    for center, start, end in arcs:
        cx, cy = center
        vx = (start[0] - cx) + (end[0] - cx)
        vy = (start[1] - cy) + (end[1] - cy)
        n = math.hypot(vx, vy)
        mid = (cx + vx / n * r, cy + vy / n * r)   # 圆弧中点（SetArcGeometry 第二参数是 arc mid）
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(V(*start), V(*mid), V(*end))
        s.SetLayer(layer)
        s.SetWidth(MM(width))
        board.Add(s)


# ----------------------------------------------------------------- 封装装载
def lib_path(key):
    cat, name = D.FP[key]
    if cat == 'numpad':
        return LOCAL_FP, name
    return os.path.join(FP_LIB, cat), name


def load_fp(board, key):
    path, name = lib_path(key)
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError('footprint not found: %s / %s' % (path, name))
    board.Add(fp)
    return fp


# ----------------------------------------------------------------- 主流程
def build(route=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    board = pcbnew.NewBoard(PCB_PATH)
    board.SetFileName(PCB_PATH)

    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    try:
        ds.SetCopperLayerCount(2)
    except Exception:
        pass

    rounded_rect(board, D.BOARD_W, D.BOARD_H, D.CORNER_R)

    # ---- 挂载孔 ----
    for i, (x, y) in enumerate(D.MOUNT_HOLES):
        fp = load_fp(board, 'mh_m3')
        fp.SetPosition(V(x, y))
        fp.SetReference('MH%d' % (i + 1))

    # ---- 网络 ----
    nets = {}
    for name in sorted(D.net_table().keys()):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    placed = {}
    small_parts = []
    # ---- 元件 ----
    for c in D.COMPS:
        fp = load_fp(board, c['fp'])
        fp.SetReference(c['ref'])
        fp.SetValue(c['value'])
        fp.SetPosition(V(*c['at']))
        if c['flip']:
            fp.Flip(fp.GetPosition(), False)
        if c['rot']:
            fp.SetOrientationDegrees(c['rot'])
        placed[c['ref']] = fp
        pads = list(fp.Pads())
        # 2 脚以内的小件（二极管/电阻/电容）丝印会压在轴体丝印上，稍后整组删掉。
        # 这里就记下来：KiCad 的 SWIG 封装上，GraphicalItems() 必须是第一个被调用的
        # 取值器，先调 GetReference()/GetPadCount() 会让它返回不可迭代的裸 SwigPyObject。
        small_parts.append((fp, len(pads) <= 2))

        for pad, net in c.get('nets', {}).items():
            if not net or net == 'NC':
                continue
            for p in pads:
                if p.GetNumber() == pad:
                    p.SetNet(nets[net])

    # ---- 键位丝印 ----
    # 原来的 26 个键名字贴在 B 面轴体下方，和轴/二极管的丝印线互相压（DRC 报 50 条
    # silk_overlap）。装上键帽后本来就看不见，所以不再画。

    # ---- 丝印清理 ----
    # 位号/值全部隐藏：正面被轴体和热插拔座占满，没有放位号的地方，
    # 摆在外面会压焊盘（DRC 报 silk_over_copper）。自制封装（热插拔座/稳定器/
    # 安装孔）自带的丝印线会跨过自己的焊盘和 NPTH，一并删掉——这些件装配靠定位板。
    skipped = []
    for fp, is_small in small_parts:
        try:
            graphics = list(fp.GraphicalItems())
        except TypeError:                    # 极少数封装上 SWIG 会返回裸对象，跳过即可
            skipped.append(fp.GetReference())
            continue
        for g in graphics:
            if type(g).__name__ in ('PCB_TEXT', 'PCB_FIELD'):
                g.SetVisible(False)          # 位号/值全部隐藏（正面没地方放）
                continue
            if g.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                continue
            # 挪到 Fab 层而不是删除：fp.Remove() 之后这个封装的 SWIG 取值器会失效
            if is_small:                     # 二极管/电阻/电容的丝印，压在轴丝印上
                g.SetLayer(pcbnew.B_Fab)
                continue
            gb = g.GetBoundingBox()          # 丝印线压到自己焊盘上的也挪走
            for p in fp.Pads():
                if gb.Intersects(p.GetBoundingBox()):
                    g.SetLayer(pcbnew.B_Fab)
                    break
        if skipped:
            print('  丝印清理跳过 %d 个封装: %s' % (len(skipped), ', '.join(skipped[:6])))
            skipped = []
        for fld in (fp.Reference(), fp.Value()):
            try:
                fld.SetVisible(False)
            except AttributeError:
                pass

    if route:
        import route as R
        R.route_all(board, placed, nets)

    pcbnew.SaveBoard(PCB_PATH, board)
    return board, placed, nets


# ----------------------------------------------------------------- 自检
def check(placed):
    """叠放自检：courtyard 两两重叠 + 焊盘出界 + 轴心定位。"""
    bad = 0

    def crt(fp):
        for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            try:
                poly = fp.GetCourtyard(layer)
                if poly.OutlineCount() > 0:
                    bb = poly.BBox()
                    return (TOMM(bb.GetLeft()), TOMM(bb.GetTop()),
                            TOMM(bb.GetRight()), TOMM(bb.GetBottom()))
            except Exception:
                pass
        for getter in (lambda: fp.GetBoundingBox(False, False), fp.GetBoundingBox):
            try:
                bb = getter()                # KiCad 10 的 SWIG 有时返回裸指针，逐个试
                left, top, right, bottom = (TOMM(bb.GetLeft()), TOMM(bb.GetTop()),
                                            TOMM(bb.GetRight()), TOMM(bb.GetBottom()))
                if right > left and bottom > top:
                    return (left, top, right, bottom)
            except Exception:
                pass
        p = fp.GetPosition()                 # 拿不到包围盒就退化成零尺寸，交给 DRC 判重叠
        return (TOMM(p.x), TOMM(p.y), TOMM(p.x), TOMM(p.y))

    boxes = [(ref, fp.GetPosition(), crt(fp), fp.GetLayer() == pcbnew.B_Cu)
             for ref, fp in placed.items()]
    pos = {ref: (TOMM(p.x), TOMM(p.y)) for ref, p, _, _ in boxes}
    side = {ref: b for ref, _, _, b in boxes}

    def same_cell(a, b):
        """同一个键格里的轴 / 稳定器 / 二极管不算冲突。"""
        if not (a[0] in 'SD' or a.startswith('SW')):
            return False
        if not (b[0] in 'SD' or b.startswith('SW')):
            return False
        ax, ay = pos[a]
        bx, by = pos[b]
        return abs(ax - bx) < 14 and abs(ay - by) < 14

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if side[a[0]] != side[b[0]]:        # 正反面各占各的 courtyard
                continue
            if same_cell(a[0], b[0]):
                continue
            ox = min(a[2][2], b[2][2]) - max(a[2][0], b[2][0])
            oy = min(a[2][3], b[2][3]) - max(a[2][1], b[2][1])
            if ox > 0.03 and oy > 0.03:
                print('  [重叠] %-6s x %-6s  %.2f x %.2f mm' % (a[0], b[0], ox, oy))
                bad += 1

    for ref, _p, (l, t, r, b), _s in boxes:
        if ref == 'J1':                          # 沉板 USB-C 本就压在板边
            continue
        if l < -0.01 or t < -0.01 or r > D.BOARD_W + 0.01 or b > D.BOARD_H + 0.01:
            print('  [出界] %-6s bbox=(%.2f,%.2f)-(%.2f,%.2f)' % (ref, l, t, r, b))
            bad += 1

    # 轴心 = (0,0) 定位柱
    for c in D.COMPS:
        if c['fp'] == 'mx_hotswap':
            fp = placed[c['ref']]
            for p in fp.Pads():
                if abs(TOMM(p.GetSize().x) - 4.0) < 0.01:
                    q = p.GetPosition()
                    dx = TOMM(q.x) - c['at'][0]
                    dy = TOMM(q.y) - c['at'][1]
                    if abs(dx) > 0.01 or abs(dy) > 0.01:
                        print('  [轴心] %s 定位柱偏离 (%.3f, %.3f)' % (c['ref'], dx, dy))
                        bad += 1
    return bad


if __name__ == '__main__':
    do_route = '--place' not in sys.argv
    board, placed, nets = build(route=do_route)
    print('已生成 %s' % PCB_PATH)
    print('封装 %d 个，网络 %d 个' % (len(placed) + len(D.MOUNT_HOLES), len(nets)))
    n = check(placed)
    print('叠放自检：%s' % ('通过' if n == 0 else '%d 处问题' % n))
