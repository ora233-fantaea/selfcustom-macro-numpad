# -*- coding: utf-8 -*-
"""v4 极简拓扑图：键盘是唯一 USB 设备，M5Dial 降级成"串口屏 + 旋钮"。

输出 img/wiring_v4.png。框图纯示意，不含真实坐标。
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]

W, H = 1480, 1120
BG = "#ffffff"
INK = "#2c3e50"
MUTED = "#7f8c8d"
BLUE = "#2980b9"
RED = "#c0392b"
GREEN = "#1e8449"
ORANGE = "#d35400"


def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=0)
            except Exception:
                continue
    return ImageFont.load_default()


def f(size):
    return load_font(size)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def box(cx, cy, w, h, title, sub=None, fill="#f4f6f9", line="#95a5a6",
        tcol=INK, scol=MUTED, r=10, lw=3, tsize=25, ssize=17):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
                        radius=r, fill=fill, outline=line, width=lw)
    if sub:
        d.text((cx, cy - 14), title, font=f(tsize), fill=tcol, anchor="mm")
        d.text((cx, cy + 20), sub, font=f(ssize), fill=scol, anchor="mm")
    else:
        d.text((cx, cy), title, font=f(tsize), fill=tcol, anchor="mm")


def arrow(pts, col=INK, w=4, size=13):
    d.line(pts, fill=col, width=w, joint="curve")
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    d.polygon([
        (x1, y1),
        (x1 - size * math.cos(a - 0.45), y1 - size * math.sin(a - 0.45)),
        (x1 - size * math.cos(a + 0.45), y1 - size * math.sin(a + 0.45)),
    ], fill=col)


def tag(x, y, text, col=BLUE, size=16, anchor="lm"):
    d.text((x, y), text, font=f(size), fill=col, anchor=anchor)


# ---------------------------------------------------------------- 标题
d.text((60, 40), "v4 极简：键盘是唯一的 USB 设备", font=f(40), fill=INK)
d.text((60, 94), "拨盘不再伪装成一台电脑设备 —— 它只是键盘的一块屏加一个旋钮，走两根线",
       font=f(20), fill=MUTED)

# ---------------------------------------------------------------- 主干
CX = 400
box(CX, 180, 460, 84, "电脑", "USB 主机接口", fill="#ecf0f1", line="#bdc3c7")
arrow([(CX, 222), (CX, 286)], INK, 5)
tag(CX + 18, 254, "一根 USB-C 线（全机对外唯一）", BLUE, 17)

box(CX, 330, 470, 76, "J1  USB-C 母座", "卡在壳壁开孔上", fill="#eaf2f8", line=BLUE)
arrow([(CX, 368), (CX, 424)], INK, 5)
tag(CX + 18, 396, "D+ / D- / 5V", BLUE, 17)

box(CX, 480, 480, 92, "U1  RP2040", "键盘主控 · QMK / Vial（原有，不动）", fill="#eaf2f8", line=BLUE, lw=4)
# 唯一设备徽标（贴在框内右上角）
d.rounded_rectangle([CX + 92, 442, CX + 230, 468], radius=7,
                    fill="#eafaf1", outline=GREEN, width=2)
d.text((CX + 161, 455), "唯一 USB 设备", font=f(14), fill=GREEN, anchor="mm")

arrow([(CX, 526), (CX, 584)], INK, 5)
box(CX, 640, 480, 92, "35 键矩阵 + Flash + LDO", "键盘功能全在这边", fill="#f4f6f9",
    line="#95a5a6", tsize=23)

# ---------------------------------------------------------------- 拨盘
RX, RY = 1040, 480
arrow([(CX + 240, RY), (RX - 190, RY)], INK, 5)
tag(RX - 196, RY - 52, "UART + 5V / GND", BLUE, 16, anchor="rm")
tag(RX - 196, RY - 26, "G13/G15 · Grove 4P 线", GREEN, 16, anchor="rm")

box(RX, RY, 380, 104, "M5Dial", "1.28″ 圆屏 + 旋钮（自带 ESP32-S3）",
    fill="#fdecea", line=RED, lw=4, tsize=24)
tag(RX, RY + 76, "不再是 USB 设备：只是键盘的一块屏 + 一个旋钮", RED, 16, anchor="mm")

# ---------------------------------------------------------------- 左面板：砍掉的
PX, PY = 60, 760
d.rounded_rectangle([PX - 24, PY - 44, PX + 620, H - 40], radius=12,
                    fill="#fbfcfd", outline="#d5dbdb", width=2)
d.text((PX, PY - 16), "v3 有、v4 没有了", font=f(21), fill=ORANGE)
gone = [
    "U5 USB Hub 芯片（CH334P ¥2.88）",
    "12 MHz 晶振 + 2 颗负载电容",
    "J3 第二个 USB-C 母座",
    "下游 CC 上拉 56 kΩ × 2",
    "限流开关 + 10 µF × 2 + 100 µF",
    "下游 D± 的第二套 ESD",
    "嘉立创扩展库换料费 ¥20",
]
for i, t in enumerate(gone):
    y = PY + 26 + i * 34
    d.ellipse([PX + 4, y - 5, PX + 14, y + 5], fill=GREEN)
    d.text((PX + 26, y), t, font=f(18), fill="#34495e", anchor="lm")

d.text((PX, PY + 26 + 7 * 34 + 16), "净省约 ¥50 / 5 片（已扣掉 Grove 座与线），少约 20 个元件，少一整类翻车点",
       font=f(18), fill=GREEN)

# ---------------------------------------------------------------- 右面板：代价
QX = 720
d.rounded_rectangle([QX - 24, PY - 44, W - 40, H - 40], radius=12,
                    fill="#fbfcfd", outline="#d5dbdb", width=2)
d.text((QX, PY - 16), "代价，以及前提", font=f(21), fill=MUTED)
cost = [
    "RP2040 要多一层转发：PC → raw HID → UART，约 150 行（VIA 就走这条通道）",
    "拨盘单独插电脑只能烧固件，不能当屏幕用 —— 桌面场景无所谓",
    "PC 侧仍要一个状态推送程序；Hub 方案同样要，屏幕不会自己知道系统音量",
    "键盘固件挂了，屏幕跟着黑",
]
for i, t in enumerate(cost):
    y = PY + 26 + i * 36
    d.ellipse([QX + 4, y - 5, QX + 14, y + 5], fill=ORANGE)
    d.text((QX + 26, y), t, font=f(18), fill="#34495e", anchor="lm")

d.text((QX, PY + 26 + 4 * 36 + 20), "待验证：", font=f(18), fill=RED)
d.text((QX + 96, PY + 26 + 4 * 36 + 20),
       "Grove 口的 5V 能否反向给拨盘供电。能的话连 USB-C 都省了。",
       font=f(18), fill="#34495e")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "wiring_v4.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("saved", out, img.size)
