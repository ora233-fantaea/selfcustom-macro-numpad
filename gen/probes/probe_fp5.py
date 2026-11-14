import pcbnew
for n in ['SW_Hotswap_Kailh_MX_1.00u','SW_Stab_Cherry_MX_2.00u','MountingHole_3.4mm']:
    fp = pcbnew.FootprintLoad(r'numpad/lib/numpad.pretty', n)
    print(n, len(list(fp.Pads())))
