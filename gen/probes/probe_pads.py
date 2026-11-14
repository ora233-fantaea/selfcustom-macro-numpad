import pcbnew
b = pcbnew.LoadBoard(r'numpad/kicad/numpad.kicad_pcb')
for fp in b.GetFootprints()[:8]:
    print(fp.GetReference(), fp.GetFPID().GetLibItemName(), len(list(fp.Pads())), [p.GetNumber() for p in fp.Pads()])
print('---- total pads', sum(len(list(f.Pads())) for f in b.GetFootprints()))
