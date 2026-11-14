import pcbnew
b = pcbnew.LoadBoard(r'numpad/kicad/numpad.kicad_pcb')
print('total pads', sum(len(list(f.Pads())) for f in b.GetFootprints()))
fp = b.FindFootprintByReference('SW1')
print('SW1 pads', [(p.GetNumber(), round(pcbnew.ToMM(p.GetPosition().x),2), round(pcbnew.ToMM(p.GetPosition().y),2)) for p in fp.Pads()])
u1 = b.FindFootprintByReference('U1')
d = {}
for p in u1.Pads():
    n = p.GetNumber()
    if n: d[n] = (round(pcbnew.ToMM(p.GetPosition().x),2), round(pcbnew.ToMM(p.GetPosition().y),2))
for n in ['1','2','3','4','9','10','11','12','13','14','15','19','20','21','22','23','27','28','43','44','45','46','47','48','49','50','51','56','57']:
    print(' U1.%s' % n, d.get(n))
