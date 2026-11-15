# -*- coding: utf-8 -*-
"""M5Dial 240×240 圆屏界面示意（1.5 倍绘制，便于看清）。

输出 img/dial_screen_mock.png：
  ① 待机主视图（时钟 + 曲目 + 帧数）
  ② 转旋钮时的音量视图（环形进度）
  ③ 右侧：每个元素的数据来源与刷新率
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

W, H = 1480, 800
BG = "#f7f8fa"
INK = "#1b2430"
MUTED = "#6b7785"

SCREEN_BG = "#12161c"
SCREEN_BG2 = "#161c24"
TXT = "#e8eef6"
DIM = "#8b98a8"
ACCENT = "#4ea8ff"
GOOD = "#46d68a"
WARN = "#ffb347"
TRACK_COL = "#2a3340"


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


def circle_screen(cx, cy, r, bg=SCREEN_BG):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg, outline="#c9d2dd", width=3)


def text(x, y, s, size, col=TXT, anchor="mm", bold=False):
    d.text((x, y), s, font=f(size), fill=col, anchor=anchor)


# ---------------------------------------------------------------- 标题
text(60, 46, "M5Dial 240 × 240 圆屏：三件事同时看得到", 38, INK, "lm")
text(60, 92, "旋钮调音量 · 常驻显示帧数 / 当前曲目 / 时间", 20, MUTED, "lm")

# ---------------------------------------------------------------- ① 主视图
CX1, CY, R = 300, 460, 180
circle_screen(CX1, CY, R)

# 时钟
text(CX1, 330, "09:41", 34, TXT, bold=True)
# 曲目
text(CX1, 382, "夜空中最亮的星", 23, TXT)
text(CX1, 414, "逃跑计划 · 正在播放", 17, DIM)
# 细分隔线
d.line([CX1 - 62, 440, CX1 + 62, 440], fill="#3d4757", width=2)
# 帧数
text(CX1, 492, "144", 84, GOOD, bold=True)
text(CX1, 558, "F P S", 19, DIM)

text(CX1, 690, "① 待机主视图", 21, INK, "mm", bold=True)
text(CX1, 720, "静置时默认停在这一页", 16, MUTED, "mm")

# ---------------------------------------------------------------- ② 音量视图
CX2 = 720
circle_screen(CX2, CY, R, SCREEN_BG2)

VOL = 0.62
A0, SWEEP = 135, 270
bbox = [CX2 - 152, CY - 152, CX2 + 152, CY + 152]
d.arc(bbox, A0, A0 + SWEEP, fill=TRACK_COL, width=22)
d.arc(bbox, A0, A0 + SWEEP * VOL, fill=ACCENT, width=22)
# 两端圆头
for ang, col in ((A0, TRACK_COL), (A0 + SWEEP * VOL, ACCENT)):
    a = math.radians(ang)
    px, py = CX2 + 152 * math.cos(a), CY + 152 * math.sin(a)
    d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=col)

text(CX2, CY - 26, "62", 96, TXT, bold=True)
text(CX2, CY + 58, "音 量", 22, ACCENT)
text(CX2, CY + 100, "顺转增大 · 逆转减小", 15, DIM)

text(CX2, 690, "② 转旋钮时", 21, INK, "mm", bold=True)
text(CX2, 720, "临时接管屏幕，停手 2 秒自动回主视图", 16, MUTED, "mm")

# ---------------------------------------------------------------- ③ 数据来源
PX = 960
d.rounded_rectangle([PX - 30, 150, W - 50, 760], radius=14,
                    fill="#ffffff", outline="#dfe5ec", width=2)
text(PX, 184, "每个元素的数据从哪来", 22, INK, "lm", bold=True)

rows = [
    ("时钟", "PC 开机时对一次时", "之后靠板上 BM8563 RTC 自己走", "1 次 / 开机", "#8e44ad"),
    ("帧数", "PC 抓帧程序", "PresentMon，或读 RTSS 共享内存", "2 次 / 秒", "#1e8449"),
    ("曲目", "Windows 媒体会话", "SMTC：标题 / 歌手 / 播放状态", "变化时推送", "#2980b9"),
    ("音量", "Windows Core Audio", "旋钮只发「+2 格」，PC 回读真实值", "转动时", "#d35400"),
]
for i, (name, src, how, rate, col) in enumerate(rows):
    y0 = 226 + i * 104
    d.ellipse([PX + 2, y0 + 2, PX + 26, y0 + 26], fill=col)
    text(PX + 40, y0 + 14, name, 20, INK, "lm", bold=True)
    text(W - 90, y0 + 14, rate, 15, col, "rm")
    text(PX + 40, y0 + 46, src, 17, "#34495e", "lm")
    text(PX + 40, y0 + 72, how, 15, MUTED, "lm")

d.line([PX - 6, 636, W - 76, 636], fill="#e6ebf1", width=2)
text(PX, 662, "全部由电脑上一个小后台程序推送；键盘只转发，不解码", 16, "#34495e", "lm")
text(PX, 690, "帧数来源二选一：PresentMon（需管理员权限）", 15, MUTED, "lm")
text(PX, 716, "或 RTSS 共享内存（需装 MSI Afterburner）", 15, MUTED, "lm")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "dial_screen_mock.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("saved", out, img.size)
