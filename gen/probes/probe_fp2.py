import pcbnew, os
p = r'numpad/lib/numpad.pretty'
fp = pcbnew.FootprintLoad(p, 'SW_Hotswap_Kailh_MX_1.00u')
print('pads', len(list(fp.Pads())), 'graphics', fp.GraphicalItems().__len__() if hasattr(fp.GraphicalItems(),"__len__") else "?")
print('graphic count', len(list(fp.GraphicalItems())))
# 程序化建一个 pad 看能不能存
fp2 = pcbnew.FOOTPRINT(None)
fp2.SetFPID(pcbnew.LIB_ID('numpad','TESTPAD'))
pad = pcbnew.PAD(fp2)
pad.SetNumber('1'); pad.SetShape(pcbnew.PAD_SHAPE_RECT)
pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1), pcbnew.FromMM(1)))
pad.SetPosition(pcbnew.VECTOR2I(0,0))
pad.SetLayerSet(pcbnew.LSET(pcbnew.F_Cu))
fp2.Add(pad)
print('fp2 pads', len(list(fp2.Pads())))
out = os.path.join(p, 'TESTPAD.kicad_mod')
try:
    pcbnew.FootprintSave(p, fp2)
    print('saved ok')
    fp3 = pcbnew.FootprintLoad(p, 'TESTPAD')
    print('reload pads', len(list(fp3.Pads())))
except Exception as e:
    print('save err', e)
print(open(out, encoding='utf-8').read()[:1200])
