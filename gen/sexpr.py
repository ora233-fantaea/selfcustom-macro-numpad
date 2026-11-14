# -*- coding: utf-8 -*-
"""极简 S 表达式读写器，用于生成/修改 KiCad 的 .kicad_sch / .kicad_pcb / .kicad_sym。

原子一律保存为原始字符串（带引号的字符串保留引号），这样可以无损往返写回。
"""


def parse(text):
    i = 0
    n = len(text)
    stack = [[]]
    while i < n:
        c = text[i]
        if c == '(':
            new = []
            stack[-1].append(new)
            stack.append(new)
            i += 1
        elif c == ')':
            if len(stack) < 2:
                raise ValueError("unbalanced ')' at %d" % i)
            stack.pop()
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if text[j] == '\\':
                    buf.append(text[j:j + 2])
                    j += 2
                    continue
                if text[j] == '"':
                    break
                buf.append(text[j])
                j += 1
            stack[-1].append('"' + ''.join(buf) + '"')
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and (not text[j].isspace()) and text[j] not in '()':
                j += 1
            stack[-1].append(text[i:j])
            i = j
    if len(stack) != 1:
        raise ValueError("unbalanced '(' — %d levels left" % (len(stack) - 1))
    if not stack[0]:
        raise ValueError("empty document")
    return stack[0][0]


def unquote(atom):
    if isinstance(atom, str) and len(atom) >= 2 and atom[0] == '"' and atom[-1] == '"':
        return atom[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    return atom


def quote(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def head(node):
    return node[0] if isinstance(node, list) and node else None


def children(node, name):
    """所有 head == name 的直接子节点"""
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def child(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def atoms(node):
    return [unquote(x) for x in node[1:] if isinstance(x, str)]


def find_symbols(root):
    """在 .kicad_sym / lib_symbols 里找出全部 (symbol "NAME" ...) 定义。"""
    out = {}
    for c in children(root, 'symbol'):
        name = unquote(c[1])
        out.setdefault(name, c)
    return out


def iter_pins(sym):
    """遍历符号定义里所有 (pin ...) 节点（含子单元 symbol "NAME_0_1" 里的）。"""
    stack = [sym]
    while stack:
        node = stack.pop()
        for c in node[1:]:
            if isinstance(c, list) and c:
                if c[0] == 'pin':
                    yield c
                elif c[0] == 'symbol':
                    stack.append(c)


def pin_info(pin_node):
    """返回 dict(number, name, x, y, angle, length, etype, style)"""
    at = child(pin_node, 'at')
    name = child(pin_node, 'name')
    number = child(pin_node, 'number')
    length = child(pin_node, 'length')
    info = {
        'etype': unquote(pin_node[1]),
        'style': unquote(pin_node[2]),
        'x': float(at[1]), 'y': float(at[2]),
        'angle': float(at[3]) if len(at) > 3 else 0.0,
        'length': float(length[1]) if length else 0.0,
        'name': unquote(name[1]) if name else '',
        'number': unquote(number[1]) if number else '',
    }
    return info
