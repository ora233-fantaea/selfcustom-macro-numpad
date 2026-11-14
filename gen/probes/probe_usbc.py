import pcbnew
b = pcbnew.LoadBoard(r'numpad/kicad/numpad.kicad_pcb')
fp = b.FindFootprintByReference('J1')
for p in fp.Pads():
    s = p.GetSize()
    pos = p.GetPosition()
    print('%-4s (%.2f,%.2f) size %.2f x %.2f drill %.2f' % (p.GetNumber() or 'SH',
        pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), pcbnew.ToMM(s.x), pcbnew.ToMM(s.y),
        pcbnew.ToMM(p.GetDrillSize().x)))
