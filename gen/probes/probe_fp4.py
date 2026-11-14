import pcbnew, os, re, shutil
src = r'numpad/lib/numpad.pretty/SW_Hotswap_Kailh_MX_1.00u.kicad_mod'
txt = open(src, encoding='utf-8').read()
d = r'numpad/lib/numpad.pretty'

def test(name, body):
    open(os.path.join(d, name + '.kicad_mod'), 'w', encoding='utf-8', newline='\n').write(body)
    fp = pcbnew.FootprintLoad(d, name)
    print(name, 'pads', len(list(fp.Pads())) if fp else 'None')

# 1) 只保留两个 SMD pad（去掉 NPTH）
body = re.sub(r'\t\(pad "" np_thru_hole[\s\S]*?\n\t\)\n', '', txt)
test('T1_smdonly', body.replace('SW_Hotswap_Kailh_MX_1.00u', 'T1_smdonly'))

# 2) 去掉 fp_circle
body2 = re.sub(r'\t\(fp_circle[\s\S]*?\n\t\)\n', '', txt)
test('T2_nocircle', body2.replace('SW_Hotswap_Kailh_MX_1.00u', 'T2_nocircle'))

# 3) 原始（改名重存）
test('T3_raw', txt.replace('SW_Hotswap_Kailh_MX_1.00u', 'T3_raw'))
