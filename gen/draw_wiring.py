# -*- coding: utf-8 -*-
"""单线出线拓扑图：USB-C → 板载 Hub → {RP2040, M5Dial}。

输出 img/wiring_v3.png。框图纯示意，不含真实坐标。
"""
import os
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]


def load_font(size, bold=False):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=0)
            except Exception:
                continue
    return ImageFont.load_default()


W, H = 1480, 1080
BG = "#ffffff"
INK = "#2c3e50"
MUTED = "#7f8c8d"
BLUE = "#2980b9"
RED = "#c0392b"
GREEN = "#1e8449"
ORANGE = "#d35400"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def f(size, bold=False):
    return load_font(size, bold)


def box(cx, cy, w, h, title, sub=None, fill="#f4f6f9", line="#95a5a6",
        tcol=INK, scol=MUTED, r=10, lw=3, tsize=25, ssize=17):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
                        radius=r, fill=fill, outline=line, width=lw)
    if sub:
        d.text((cx, cy - 14), title, font=f(tsize, True), fill=tcol, anchor="mm")
        d.text((cx, cy + 20), sub, font=f(ssize), fill=scol, anchor="mm")
    else:
        d.text((cx, cy), title, font=f(tsize, True), fill=tcol, anchor="mm")


def line(pts, col=INK, w=4):
    d.line(pts, fill=col, width=w, joint="curve")


def arrow(pts, col=INK, w=4, size=13):
    line(pts, col, w)
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    import math
    a = math.atan2(y1 - y0, x1 - x0)
    d.polygon([
        (x1, y1),
        (x1 - size * math.cos(a - 0.45), y1 - size * math.sin(a - 0.45)),
        (x1 - size * math.cos(a + 0.45), y1 - size * math.sin(a + 0.45)),
    ], fill=col)


def tag(x, y, text, col=BLUE, size=16, anchor="lm"):
    d.text((x, y), text, font=f(size), fill=col, anchor=anchor)


# ---------------------------------------------------------------- 标题
d.text((60, 40), "整机只有一根线：板载 USB Hub 拓扑", font=f(40, True), fill=INK)
d.text((60, 92), "键盘与 M5Dial 挂在同一颗 Hub 下面，各走各的通道，电脑那边看到两个独立设备",
       font=f(20), fill=MUTED)

CX = 640

# ---------------------------------------------------------------- 电脑
box(CX, 190, 460, 84, "电脑", "USB 主机接口", fill="#ecf0f1", line="#bdc3c7")
arrow([(CX, 232), (CX, 292)], INK, 5)
tag(CX + 18, 262, "一根 USB-C 线（对外唯一）", BLUE, 17)

# ---------------------------------------------------------------- 上游插座
box(CX, 330, 470, 78, "J1  USB-C 母座", "上游口 · 卡在壳壁开孔上", fill="#eaf2f8", line=BLUE)
arrow([(CX, 369), (CX, 424)], INK, 5)
tag(CX + 18, 396, "D+ / D- / 5V", BLUE, 17)

# ---------------------------------------------------------------- Hub
box(CX, 468, 470, 92, "U5  USB 2.0 Hub 芯片", "1 上游 + 2 下游 · 放板子背面", fill="#fef5e7", line=ORANGE, lw=4)

# ---------------------------------------------------------------- 分叉
BR = 600
line([(CX, 512), (CX, BR)], INK, 5)
line([(320, BR), (960, BR)], INK, 5)

# ---------------------------------------------------------------- 左：RP2040
LX = 320
arrow([(LX, BR), (LX, 636)], INK, 5)
box(LX, 682, 400, 88, "U1  RP2040", "下游 1 · 键盘主控（原有，固件不变）", fill="#eaf2f8", line=BLUE)
LX2 = LX
arrow([(LX2, 726), (LX2, 774)], INK, 5)
box(LX2, 826, 400, 92, "35 键矩阵 + Flash + LDO", "键盘功能全在这边", fill="#f4f6f9", line="#95a5a6", tsize=22)

# ---------------------------------------------------------------- 右：M5Dial
RX = 960
arrow([(RX, BR), (RX, 636)], INK, 5)
box(RX, 682, 400, 88, "J3  USB-C 母座", "下游 2 · 内部口，接 M5Dial", fill="#fdecea", line=RED)
arrow([(RX, 726), (RX, 774)], RED, 5)
tag(RX + 18, 750, "机内短 USB-C 线（数据 + 5V 供电）", RED, 16)
box(RX, 826, 400, 92, "M5Dial", "1.28″ 圆屏 + 旋钮（自带 ESP32-S3）", fill="#fdecea", line=RED, tsize=22)

# ---------------------------------------------------------------- 右侧说明
NX, NY = 60, 912
d.text((NX, NY), "为什么需要这颗 Hub：", font=f(22, True), fill=INK)
notes = [
    "M5Dial 不是「键盘上的旋钮」，它是一台独立的 USB 设备（自带 USB 口和固件）",
    "两个 USB 设备想共用一根线，中间必须有一个 Hub 分配通道 —— 这是 USB 协议的要求",
    "Hub 只是分流，两边各自枚举成独立设备：键盘是一个 HID，M5Dial 是另一个",
]
for i, t in enumerate(notes):
    y = NY + 36 + i * 34
    d.ellipse([NX + 4, y - 5, NX + 14, y + 5], fill=ORANGE)
    d.text((NX + 26, y), t, font=f(19), fill="#34495e", anchor="lm")

# ---------------------------------------------------------------- 左下：不做的几种
BX, BY = 60, 240
d.rounded_rectangle([BX - 24, BY - 40, BX + 300, BY + 372], radius=10,
                    fill="#fbfcfd", outline="#d5dbdb", width=2)
d.text((BX, BY - 12), "另外三条路（不做）", font=f(21, True), fill=MUTED)
rej = [
    ("两根线", "不要 Hub，各插一个口", "你否掉了"),
    ("M5Dial 走 UART", "键盘取电 + 转发", "屏幕拿不到 PC 数据"),
    ("去掉 RP2040", "让 ESP32-S3 直接扫描矩阵", "放弃 QMK/Vial，固件全重写"),
]
for i, (t, s1, s2) in enumerate(rej):
    y = BY + 22 + i * 118
    d.text((BX, y), t, font=f(21, True), fill="#566573")
    d.text((BX, y + 30), s1, font=f(17), fill=MUTED)
    d.text((BX, y + 58), "→ " + s2, font=f(17), fill=RED)

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "wiring_v3.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("saved", out, img.size)
