"""FreeRouting 流水线：干净板 -> 覆铜 -> 导出 DSN -> 外部自动布线 -> 回灌 SES。

用法：
  python gen/freeroute.py --export     # 只导出 DSN（板子须已 build_pcb.py --place）
  python gen/freeroute.py --import     # 回灌 SES 并重新灌铜存盘
  python gen/freeroute.py --route      # export + 跑 freerouting + import（一步到底）

freerouting 自己的日志进 logs/freerouting.log，SES 里只有它布出来的线。
"""
import argparse
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # numpad/
KICAD = os.path.join(ROOT, 'kicad')
PCB = os.path.join(KICAD, 'numpad.kicad_pcb')
DSN = os.path.join(KICAD, 'numpad.dsn')
SES = os.path.join(KICAD, 'numpad.ses')
JAR = os.path.join(os.path.dirname(ROOT), 'tools', 'freerouting', 'freerouting-1.9.0.jar')
JAVA = r'C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot\bin\java.exe'

MM = pcbnew.FromMM


def load():
    if not os.path.exists(PCB):
        sys.exit('没有板子：%s' % PCB)
    return pcbnew.LoadBoard(PCB)


def set_rules(board):
    """按嘉立创普通工艺的极限值配网类规则：0.15 线宽/间距、0.45 过孔。
    FreeRouting 从 DSN 里读的就是这套数，所以必须在导出前设好。
    KiCad 10 里网类要从 GetAllNetClasses() 取，GetDefaultNetclass() 已经没有了。"""
    ncs = board.GetAllNetClasses()
    nc = ncs.get('Default') or next(iter(ncs.values()))
    nc.SetClearance(MM(0.15))
    nc.SetTrackWidth(MM(0.15))
    nc.SetViaDiameter(MM(0.45))
    nc.SetViaDrill(MM(0.25))
    nc.SetDiffPairWidth(MM(0.20))
    nc.SetDiffPairGap(MM(0.20))
    print('规则：间距 %.2f / 线宽 %.2f / 过孔 %.2f:%.2f' % (
        pcbnew.ToMM(nc.GetClearance()), pcbnew.ToMM(nc.GetTrackWidth()),
        pcbnew.ToMM(nc.GetViaDiameter()), pcbnew.ToMM(nc.GetViaDrill())))


def add_zones(board):
    """In1 = GND 平面、In2 = 3V3 平面。板子上已经有就不重复加。"""
    have = set()
    for z in board.Zones():
        have.add((z.GetNetname(), z.GetLayer()))
    w = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetWidth())
    h = pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetHeight())
    for layer, netname in ((pcbnew.In1_Cu, 'GND'), (pcbnew.In2_Cu, '3V3')):
        if (netname, layer) in have:
            continue
        z = pcbnew.ZONE(board)
        ls = pcbnew.LSET()
        ls.AddLayer(layer)
        z.SetLayerSet(ls)
        z.SetNet(board.FindNet(netname))
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
        print('加覆铜 %s @ %s' % (netname, board.GetLayerName(layer)))


def fill(board):
    zs = list(board.Zones())
    if zs:
        pcbnew.ZONE_FILLER(board).Fill(zs)


def do_export():
    board = load()
    set_rules(board)
    add_zones(board)
    fill(board)
    ok = pcbnew.ExportSpecctraDSN(board, DSN)
    pcbnew.SaveBoard(PCB, board)
    if not ok:
        sys.exit('DSN 导出失败')
    print('DSN -> %s (%.1f KB)' % (DSN, os.path.getsize(DSN) / 1024))


def finish(board):
    """叠构收口：2 层 + 双面 GND 覆铜。

    freerouting 在这块板上把 613 段全走在 F.Cu/B.Cu（内层四层一段没用），
    所以原来 6 层的叠构纯属浪费——内层是空的，GND/3V3 平面反而孤立。
    改成 2 层、两面都铺 GND（间距 0.20，孤岛自动移除）：
    制板便宜一大截，GND 靠铺铜 + 走线，键盘这种低速板完全够用。
    """
    if board.GetCopperLayerCount() != 2:
        board.SetCopperLayerCount(2)
        print('叠构 -> 2 层（freerouting 只用了 F/B）')

    have = {(z.GetNetname(), z.GetLayer()) for z in board.Zones()}
    bb = board.GetBoardEdgesBoundingBox()
    inset = MM(0.40)                          # 离板边 0.4，满足 edge_clr_0.2
    x0, y0 = bb.GetLeft() + inset, bb.GetTop() + inset
    x1, y1 = bb.GetRight() - inset, bb.GetBottom() - inset
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        if ('GND', layer) in have:
            continue
        z = pcbnew.ZONE(board)
        ls = pcbnew.LSET()
        ls.AddLayer(layer)
        z.SetLayerSet(ls)
        z.SetNet(board.FindNet('GND'))
        z.SetLocalClearance(MM(0.20))
        z.SetMinThickness(MM(0.20))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.40))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.Outline().NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            z.Outline().Append(x, y)
        board.Add(z)
        print('GND 覆铜 @ %s' % board.GetLayerName(layer))

    # USB-C 的两个外壳地焊盘（A12/B1）被信号脚夹在中间，热焊盘只能拉出 1 根引线，
    # DRC 报 starved_thermal；改成整片直连。
    conn = getattr(pcbnew, 'ZONE_CONNECTION_FULL', None)
    j1 = board.FindFootprintByReference('J1')
    if j1 is not None and conn is not None:
        for p in j1.Pads():
            if p.GetNumber() in ('A12', 'B1'):
                p.SetLocalZoneConnection(conn)


def do_import():
    board = load()
    n_fp = len(list(board.GetFootprints()))
    if n_fp < 50:
        # 曾经发生过：build_pcb 崩在丝印清理阶段，board 被写成空板，
        # 回灌后得到 613 条无网络走线 + 178 条 track_dangling 的假结果。
        sys.exit('板子只有 %d 个封装，是半成品（build_pcb 崩溃过），'
                 '先重跑 build_pcb.py --place' % n_fp)
    if not os.path.exists(SES):
        sys.exit('没有 SES：%s' % SES)
    n_before = len(list(board.GetTracks()))
    ok = pcbnew.ImportSpecctraSES(board, SES)
    n_after = len(list(board.GetTracks()))
    if not ok:
        sys.exit('SES 回灌失败')
    board.BuildConnectivity()
    finish(board)                 # 2 层 + 双面 GND 覆铜
    fill(board)
    pcbnew.SaveBoard(PCB, board)
    tr = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    vi = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    print('SES -> 走线 %d 段，过孔 %d 个（回灌前 %d 个对象）' % (len(tr), len(vi), n_before))


def do_route(passes=30, threads=8):
    do_export()
    if os.path.exists(SES):
        os.remove(SES)
    cmd = [JAVA, '-jar', JAR, '-de', DSN, '-do', SES,
           '-mp', str(passes), '-mt', str(threads)]
    print('跑 freerouting：%s' % ' '.join(cmd[-8:]))
    r = subprocess.run(cmd, cwd=os.path.dirname(ROOT), capture_output=True, text=True,
                       timeout=3600)
    tail = (r.stdout or '')[-1500:]
    print(tail)
    if not os.path.exists(SES):
        sys.exit('freerouting 没产出 SES（exit %s）\n%s' % (r.returncode, (r.stderr or '')[-1500:]))
    print('SES -> %s (%.1f KB)' % (SES, os.path.getsize(SES) / 1024))
    do_import()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--export', action='store_true')
    ap.add_argument('--import', dest='imp', action='store_true')
    ap.add_argument('--route', action='store_true')
    ap.add_argument('--passes', type=int, default=30)
    ap.add_argument('--threads', type=int, default=8)
    a = ap.parse_args()
    if a.route:
        do_route(a.passes, a.threads)
    elif a.export:
        do_export()
    elif a.imp:
        do_import()
    else:
        ap.print_help()
