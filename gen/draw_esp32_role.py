# -*- coding: utf-8 -*-
"""ESP32-S3 在整机里干什么：把"显示"变成"呈现"。

输出 img/esp32_role.png：
  ① 主视图升级版：帧数不再是一个跳动的数字，而是走势 + 1% low
  ② PC 程序没跑时：降级成离线态，不黑屏
  ③ 右侧：ESP32 在干什么 / 它干不了什么
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

W, H = 1480, 780
BG = "#f7f8fa"
INK = "#1b2430"
MUTED = "#6b7785"
SCREEN_BG = "#12161c"
SCREEN_BG2 = "#10141a"
TXT = "#e8eef6"
DIM = "#8b98a8"
ACCENT = "#4ea8ff"
GOOD = "#46d68a"
WARN = "#ffb347"


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


def text(x, y, s, size, col=TXT, anchor="mm", bold=False):
    d.text((x, y), s, font=f(size), fill=col, anchor=anchor)


def screen(cx, cy, r, bg=SCREEN_BG):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg, outline="#c9d2dd", width=3)


# ---------------------------------------------------------------- 标题
text(60, 44, "那这颗 ESP32-S3 到底在干什么", 38, INK, "lm")
text(60, 90, "它不是数据源，是呈现层：把电脑推来的原始数字，做成看得懂的走势和动效", 20, MUTED, "lm")

# ---------------------------------------------------------------- ① 主视图
CX, CY, R = 300, 440, 180
screen(CX, CY, R)

text(CX, 335, "09:41", 21, DIM)
text(CX, 386, "夜空中最亮的星", 21, TXT)
text(CX, 413, "逃跑计划", 17, DIM)
text(CX, 473, "144", 69, GOOD, bold=True)

# 帧率走势：贴在下半圆里的一条折线
SX0, SX1 = CX - 82, CX + 82
SY_BASE, SY_H = 558, 34
hist = [0.92, 0.88, 0.95, 0.72, 0.68, 0.80, 0.86, 0.90, 0.94, 0.97,
        0.93, 0.85, 0.78, 0.70, 0.76, 0.88, 0.95, 0.99, 0.93, 0.90,
        0.86, 0.90, 0.94, 1.0, 0.96, 0.91, 0.88, 0.93, 0.97, 0.95]
pts = []
for i, v in enumerate(hist):
    x = SX0 + (SX1 - SX0) * i / (len(hist) - 1)
    y = SY_BASE - v * SY_H
    pts.append((x, y))
# 折线下方淡淡的填充
poly = pts + [(SX1, SY_BASE), (SX0, SY_BASE)]
d.polygon(poly, fill="#1b3a2c")
d.line(pts, fill=GOOD, width=3, joint="curve")
text(CX, 581, "1% low  96", 17, DIM)

text(CX, 680, "① 主视图（升级后）", 21, INK, bold=True)
text(CX, 710, "帧数不只是那个跳动的数字，还带 30 秒走势和 1% low", 16, MUTED)

# ---------------------------------------------------------------- ② 离线态
CX2 = 730
screen(CX2, CY, R, SCREEN_BG2)
# 灰点
d.ellipse([CX2 + 104, 320, CX2 + 122, 338], fill="#4a5260")

text(CX2, 352, "09:41", 21, DIM)
text(CX2, 424, "PC 离线", 30, "#8b98a8", bold=True)
text(CX2, 460, "键盘在线 · 电脑上的程序没运行", 15, "#5c6a7a")
d.line([CX2 - 62, 492, CX2 + 62, 492], fill="#2a3340", width=2)
text(CX2, 524, "上次播放", 14, "#5c6a7a")
text(CX2, 550, "夜空中最亮的星", 17, "#6b7785")
text(CX2, 588, "帧数 —", 16, "#3f4855")

text(CX2, 680, "② 电脑那边掉线时", 21, INK, bold=True)
text(CX2, 710, "RTC 继续走，屏上有东西；不是一块黑砖", 16, MUTED)

# ---------------------------------------------------------------- ③ 分工
PX = 970
d.rounded_rectangle([PX - 30, 140, W - 50, 740], radius=14,
                    fill="#ffffff", outline="#dfe5ec", width=2)
text(PX, 176, "ESP32-S3 在干的事", 21, INK, "lm", bold=True)

jobs = [
    "LVGL 画 240×240 圆屏，60 fps",
    "触摸 + 旋钮正交解码 + RTC 走时",
    "帧数本地算滑动平均与 1% low",
    "本地绘制 30 秒帧率走势曲线",
    "音量插值：数字滚动而不硬跳",
    "断线降级：显示离线态，不黑屏",
]
for i, t in enumerate(jobs):
    y = 220 + i * 46
    d.ellipse([PX + 4, y - 6, PX + 16, y + 6], fill=GOOD)
    text(PX + 30, y, t, 17, "#34495e", "lm")

y2 = 220 + len(jobs) * 46 + 16
d.line([PX - 6, y2 - 20, W - 76, y2 - 20], fill="#e6ebf1", width=2)
text(PX, y2 + 6, "它干不了的", 19, "#c0392b", "lm", bold=True)

cant = [
    "读不到 PC 的帧数 / 曲名 / 音量",
    "替不了 QMK：只引出 4 根 GPIO",
]
for i, t in enumerate(cant):
    y = y2 + 44 + i * 40
    d.ellipse([PX + 4, y - 6, PX + 16, y + 6], fill="#c0392b")
    text(PX + 30, y, t, 17, "#34495e", "lm")

text(PX, y2 + 44 + 2 * 40 + 34, "数据源那三样都在电脑上；除非开 WiFi 走网络，否则", 15, MUTED, "lm")
text(PX, y2 + 44 + 2 * 40 + 58, "这颗芯片再快也读不到它。关掉无线之后更是如此。", 15, MUTED, "lm")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "esp32_role.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("saved", out, img.size)
