import pcbnew, os
p = os.path.join(r'numpad/lib/numpad.pretty')
fp = pcbnew.FootprintLoad(p, 'SW_Hotswap_Kailh_MX_1.00u')
print('type', type(fp))
print('pads', len(list(fp.Pads())))
for pad in fp.Pads():
    s = pad.GetSize()
    print(' pad', repr(pad.GetNumber()), pad.GetAttribute(), round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2), pad.GetLayerName())
