import pcbnew, os
def t(path, name):
    fp = pcbnew.FootprintLoad(path, name)
    print(name, '->', len(list(fp.Pads())) if fp else 'None')
t(r'numpad/lib/numpad.pretty', 'MountingHole_3.4mm')
t(r'numpad/lib/numpad.pretty', 'SW_Stab_Cherry_MX_2.00u')
ki = r'tools/kicad-portable/share/kicad/footprints/MountingHole.pretty'
print('kicad lib exists', os.path.isdir(ki))
if os.path.isdir(ki):
    t(ki, 'MountingHole_3.2mm_M3')
