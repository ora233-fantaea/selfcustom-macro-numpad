# -*- coding: utf-8 -*-
"""列出某个 .kicad_sym 文件里的符号与引脚表，便于核对。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexpr

def main(path, only=None):
    root = sexpr.parse(open(path, encoding='utf-8').read())
    syms = sexpr.find_symbols(root)
    for name, sym in syms.items():
        if only and only.lower() not in name.lower():
            continue
        body = [c for c in sexpr.children(sym, 'symbol')]
        if not body:
            continue
        print("=== %s ===" % name)
        rows = []
        for p in sexpr.iter_pins(sym):
            rows.append(sexpr.pin_info(p))
        rows.sort(key=lambda r: (int(r['number']) if r['number'].isdigit() else 9999))
        for r in rows:
            print("%-4s %-14s x=%7.2f y=%7.2f a=%5.0f len=%4.1f  %s/%s" % (
                r['number'], r['name'], r['x'], r['y'], r['angle'], r['length'],
                r['etype'], r['style']))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
