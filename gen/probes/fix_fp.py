import re, os, glob
d = r'numpad/lib/numpad.pretty'
fixed = 0
for f in glob.glob(os.path.join(d, '*.kicad_mod')):
    t = open(f, encoding='utf-8').read()
    t2 = re.sub(r'\(fill\s*\n\s*\(none\)\s*\n\s*\)', '(fill no)', t)
    t2 = re.sub(r'\(fill\s*\n\s*\(solid\)\s*\n\s*\)', '(fill yes)', t2)
    t2 = t2.replace('(fill (none))', '(fill no)').replace('(fill (solid))', '(fill yes)')
    if t2 != t:
        open(f, 'w', encoding='utf-8', newline='\n').write(t2)
        fixed += 1
    print(os.path.basename(f), 'none-ish:', t.count('(none)'), '->', t2.count('(none)'))
print('fixed', fixed)
