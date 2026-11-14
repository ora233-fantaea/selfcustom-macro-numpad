# -*- coding: utf-8 -*-
"""从 design.py 的元件表/网络表生成 KiCad 原理图。

思路：**连线全部用网络标签**。设计里的网表已经是单一真值源，这里只做两件事——
把每个元件摆上图纸，把每个有网络的引脚拉一小段线再接一个同名标签。
这样「图」和「板」用的是同一份 net_table()，不可能各说各话。

生成的是 A1 图幅、四象限分区的平铺原理图：
  左上 USB-C / ESD / 保险丝    左下 电源链
  右上 RP2040 / 晶振 / QSPI    右下 矩阵（26 轴 + 27 二极管 + 旋钮）
"""
import math
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SYMBOLDIR = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                         'tools', 'kicad-portable', 'share', 'kicad', 'symbols')
OUT = os.path.join(ROOT, 'numpad', 'kicad', 'numpad.kicad_sch')

# value / footprint -> (库名:符号名)
# 按封装的 key 映射到 KiCad 符号（比值名稳）
FP_SYM = {
    'mx_hotswap': 'Switch:SW_Push',
    'd_sod123': 'Device:D',
    'ec11': 'Device:RotaryEncoder_Switch',
    'qfn56': 'MCU_RaspberryPi:RP2040',
    'usbc16': 'Connector:USB_C_Receptacle_USB2.0_16P',
    'sot23_6': 'numpad:USBLC6-2SC6',
    'sot23_5': 'Regulator_Linear:ME6211C33M5',
    'soic8': 'Memory_Flash:W25Q32JVSS',
    'crystal': 'Device:Crystal_GND24',
    'fuse1206': 'Device:Polyfuse',
    'tp': 'Connector:TestPoint',
    'c_0402': 'Device:C',
    'c_0603': 'Device:C',
    'r_0402': 'Device:R',
    'r_0603': 'Device:R',
}


def sym_for(comp):
    fp = comp['fp']
    if fp in FP_SYM:
        return FP_SYM[fp]
    if fp == 'stab_2u':
        return None                       # 纯机械件，原理图上不画
    raise KeyError('没有给 %s（封装 %s）配符号' % (comp['ref'], fp))


_LIBCACHE = {}



# 自制符号：库里的 USBLC6-2SC6 是 (extends "USBLC6-2P6") 的派生符号，
# 嵌进 lib_symbols 后 KiCad 会报 lib_symbol_mismatch、引脚位置也对不上，
# 所以这里画一个 6 脚黑盒（脚序与 SOT-23-6 封装一一对应）。
_CUSTOM = {}
_pin = lambda x, y, a, n, name: (
    '    (pin passive line (at %g %g %d) (length 2.54)\n'
    '      (name "%s" (effects (font (size 1.016 1.016))))\n'
    '      (number "%s" (effects (font (size 1.016 1.016)))))' % (x, y, a, name, n))
_CUSTOM['numpad:USBLC6-2SC6'] = '\n'.join([
    '(symbol "numpad:USBLC6-2SC6"',
    '  (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
    '  (property "Reference" "U" (at 0 5.842 0) (effects (font (size 1.27 1.27))))',
    '  (property "Value" "USBLC6-2SC6" (at 0 -5.842 0) (effects (font (size 1.27 1.27))))',
    '  (symbol "USBLC6-2SC6_0_1"',
    '    (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default))',
    '      (fill (type background))))',
    '  (symbol "USBLC6-2SC6_1_1"',
    _pin(-7.62, 2.54, 0, '1', 'I/O1'), _pin(-7.62, 0, 0, '2', 'GND'),
    _pin(-7.62, -2.54, 0, '3', 'I/O2'), _pin(7.62, 2.54, 180, '6', 'I/O1'),
    _pin(7.62, 0, 180, '5', 'VBUS'), _pin(7.62, -2.54, 180, '4', 'I/O2'),
    '  )', ')'])


def _raw_symbol(lib, name):
    if lib not in _LIBCACHE:
        path = os.path.join(SYMBOLDIR, lib + '.kicad_sym')
        _LIBCACHE[lib] = open(path, encoding='utf-8').read()
    text = _LIBCACHE[lib]
    key = '(symbol "%s"' % name
    i = text.find(key)
    if i < 0:
        raise KeyError('%s:%s' % (lib, name))
    depth = 0
    for j in range(i, len(text)):
        if text[j] == '(':
            depth += 1
        elif text[j] == ')':
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    raise ValueError(name)


def base_of(lib_id):
    """派生符号（(extends "基类")）返回基类的完整 lib_id"""
    if lib_id in _CUSTOM:
        return None
    lib, name = lib_id.split(':', 1)
    seg = _raw_symbol(lib, name)
    m = re.search(r'\(extends\s+"([^"]+)"', seg)
    return '%s:%s' % (lib, m.group(1)) if m else None


def lib_def(lib_id):
    """原始定义文本；派生符号保持 (extends ...)，由 KiCad 自己展开，避免 lib_symbol_mismatch"""
    if lib_id in _CUSTOM:
        return _CUSTOM[lib_id]
    lib, name = lib_id.split(':', 1)
    return _raw_symbol(lib, name)


def flat_def(lib_id):
    """展开 extends 后的定义——只用来算引脚和包围盒"""
    dep = base_of(lib_id)
    if not dep:
        return lib_def(lib_id)
    lib, name = lib_id.split(':', 1)
    body = lib_def(dep)
    body = body[body.index('"', body.index('"') + 1) + 1:-1]
    base_name = dep.split(':', 1)[1]
    body = body.replace('(symbol "%s_' % base_name, '(symbol "%s_' % name)
    return '(symbol "%s"%s)' % (name, body)


def pins_of(symdef):
    """{编号: (x, y, angle)}；坐标是符号系（y 向上）"""
    out = {}
    for m in re.finditer(
            r'\(pin\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)'
            r'\s*\(length\s+([-\d.]+)\)', symdef):
        x, y, ang, ln = map(float, m.groups())
        tail = symdef[m.end():m.end() + 500]
        num = re.search(r'\(number\s+"([^"]+)"', tail)
        if num:
            out[num.group(1)] = (x, y, ang)
    return out


def bbox_of(symdef):
    ps = pins_of(symdef)
    xs = [p[0] for p in ps.values()]
    ys = [p[1] for p in ps.values()]
    return min(xs) - 5.08, min(ys) - 5.08, max(xs) + 5.08, max(ys) + 5.08


def uid():
    return str(uuid.uuid4())


def snap(v, grid=1.27):
    return round(v / grid) * grid


class Sheet:
    def __init__(self):
        self.body = []
        self.libs = {}

    def wire(self, x1, y1, x2, y2):
        self.body.append(
            '(wire (pts (xy %g %g) (xy %g %g)) (stroke (width 0) (type default)) '
            '(uuid %s))' % (x1, y1, x2, y2, uid()))

    def label(self, name, x, y):
        self.body.append(
            '(label "%s" (at %g %g 0) (effects (font (size 1.27 1.27)) '
            '(justify left bottom)) (uuid %s))' % (name, x, y, uid()))

    def no_connect(self, x, y):
        self.body.append('(no_connect (at %g %g) (uuid %s))' % (x, y, uid()))

    def text(self, s, x, y, size=2.0):
        self.body.append(
            '(text "%s" (at %g %g 0) (effects (font (size %g %g)) '
            '(justify left bottom)) (uuid %s))' % (s, x, y, size, size, uid()))

    def symbol(self, lib_id, ref, value, fp, x, y):
        symdef = flat_def(lib_id)
        self.libs[lib_id] = lib_def(lib_id)
        dep = base_of(lib_id)
        while dep:
            if dep not in self.libs:
                self.libs[dep] = lib_def(dep)
            dep = base_of(dep)
        p = pins_of(symdef)
        self.body.append(
            '(symbol (lib_id "%s") (at %g %g 0) (unit 1) (in_bom yes) (on_board yes) '
            '(dnp no) (uuid %s)' % (lib_id, x, y, uid()))
        self.body.append(
            '  (property "Reference" "%s" (at %g %g 0) (effects (font (size 1.27 1.27))))'
            % (ref, x + 2.54, y - 1.27))
        self.body.append(
            '  (property "Value" "%s" (at %g %g 0) (effects (font (size 1.27 1.27))))'
            % (str(value).replace('"', "'"), x + 2.54, y + 1.27))
        self.body.append(
            '  (property "Footprint" "%s" (at %g %g 0) (effects (font (size 1.27 1.27)) hide))'
            % (fp or '', x, y))
        for num in sorted(p):
            self.body.append('  (pin "%s" (uuid %s))' % (num, uid()))
        self.body.append(
            '  (instances (project "numpad" (path "/" (reference "%s") (unit 1))))' % ref)
        self.body.append(')')
        # 引脚在图纸上的位置（符号 y 向上，图纸 y 向下）
        return {n: (x + px, y - py) for n, (px, py, _a) in p.items()}, p

    def render(self, project='numpad', paper='A0'):
        out = ['(kicad_sch (version 20250114) (generator "numpad_sch")']
        out.append('  (uuid "%s")' % uid())
        out.append('  (paper "%s")' % paper)
        out.append('  (lib_symbols')
        for lib_id, symdef in self.libs.items():
            i = symdef.index('"', symdef.index('"') + 1) + 1
            body = symdef[i:-1]
            out.append('    (symbol "%s"%s)' % (lib_id, body))
        out.append('  )')
        out.extend('  ' + b for b in self.body)
        out.append('  (sheet_instances (path "/" (page "1")))')
        out.append(')')
        return '\n'.join(out) + '\n'


def main():
    nt = D.net_table()
    placed_nets = {}
    for n, members in nt.items():
        for ref, pad in members:
            placed_nets.setdefault(ref, {})[str(pad)] = n

    # ---- 布局：按功能分区，每个元件一个格子 ----
    blocks = [
        ('USB / ESD / 保险丝', lambda c: c['ref'] in ('J1', 'U4', 'F2', 'R3', 'R4', 'R5', 'R6', 'TP4', 'TP5'),
         (20, 25, 285, 6)),
        ('电源', lambda c: c['ref'] in ('U3', 'C1', 'C8', 'C2', 'C5'),
         (20, 125, 285, 6)),
        ('主控 / 晶振 / QSPI', lambda c: c['ref'] in ('U1', 'Y1', 'R1', 'C9', 'C10', 'U2', 'R2')
         or (c['ref'].startswith('C') and c['ref'] not in ('C1', 'C8', 'C2', 'C5', 'C9', 'C10')),
         (20, 195, 285, 6)),
        ('矩阵 26 键 + 二极管 + 旋钮', lambda c: True, (300, 25, 580, 17)),
    ]

    sh = Sheet()
    order = []
    for title, pred, (x0, y0, x1, pad) in blocks:
        sel = [c for c in D.COMPS if pred(c) and c not in order]
        order.extend(sel)
        sh.text(title, x0, y0 - 6, size=3.0)
        x, y, rowh = snap(x0, 1.27), snap(y0, 1.27), 0
        for c in sel:
            lib_id = sym_for(c)
            if lib_id is None:
                continue
            bx0, by0, bx1, by1 = bbox_of(flat_def(lib_id))
            w = math.ceil((bx1 - bx0 + pad) / 1.27) * 1.27
            h = math.ceil((by1 - by0 + pad) / 1.27) * 1.27
            if x + w > x1:
                x = x0
                y += rowh + 6
                rowh = 0
            # 原点落在 0.635 栅格上，引脚连接点才落在连接栅格上（ERC 的 endpoint_off_grid）
            ox = snap(x + w / 2, 1.27)
            oy = snap(y + h / 2, 1.27)
            pos, pinmeta = sh.symbol(lib_id, c['ref'], c['value'], c.get('fpname') or '', ox, oy)
            rowh = max(rowh, h)
            x += w
            # 每个引脚：短引线 + 网络标签；单端网络当作悬空脚处理
            for num, (px, py) in pos.items():
                net = placed_nets.get(c['ref'], {}).get(num)
                ang = pinmeta[num][2]
                dx = -math.cos(math.radians(ang))
                dy = math.sin(math.radians(ang))
                ex, ey = px + 2.54 * dx, py + 2.54 * dy
                if not net or len(nt[net]) < 2:
                    sh.no_connect(px, py)
                    continue
                sh.wire(px, py, ex, ey)
                sh.label(net, ex, ey)

    # 电源网络要有驱动源，否则 ERC 报 power_pin_not_driven
    fl = lib_def('power:PWR_FLAG')
    sh.libs['power:PWR_FLAG'] = fl
    px = 20.32
    for net in ('GND', 'VBUS', '5V'):
        y = 400.05
        pos, _m = sh.symbol('power:PWR_FLAG', 'FLG_' + net, 'PWR_FLAG', '', px, y)
        for num, (x1, y1) in pos.items():
            sh.wire(x1, y1, x1, y1 + 2.54)
            sh.label(net, x1, y1 + 2.54)
        px += 20.32

    sh.text('EC11 的 MP 安装脚在封装里直接接 GND，符号库没有对应引脚', 20, 410, size=2.0)

    open(OUT, 'w', encoding='utf-8', newline='\n').write(sh.render())
    print('生成', OUT)
    print('元件 %d 个，网络 %d 个' % (len(D.COMPS), len(nt)))


if __name__ == '__main__':
    main()
