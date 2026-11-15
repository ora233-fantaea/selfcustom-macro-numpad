"""v3 布局方案顶视图：三区分离 + M5Dial φ51（概念图，不涉及 PCB）。

相对 v2 的变化：
  1. 旋钮换成 M5Dial：外径 φ51 / 总高 32.3 / 面板开孔 Ø45.2
  2. 键区分成三块独立岛：宏键 / 功能键 / 数字区，之间留 4 mm 沟槽
  3. 电子舱取消 —— 拨盘把整条顶带吃掉，MCU 改放 PCB 背面
  4. 矩阵不变：7 行 × 6 列，35 键（固件不用改）

用法：python gen/draw_layout_v3.py
输出：img/layout_v3.png
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

# ---------- 几何参数（mm） ----------
PITCH = 19.05
GAP = 4.00                    # 岛与岛之间的沟槽
MARGIN_EDGE = 6.00            # 板边到岛的留白

DIAL_D = 51.00                # M5Dial 实物直径
DIAL_TH = 32.30               # M5Dial 总高（官方 32.3，不是 22）
HOLE_D = 45.20                # 面板开孔（官方建议 Ø45±0.2）
DIAL_ISLAND = 53.00           # 拨盘岛（四周各留 1 mm 装配间隙）

FN_COLS, FN_ROWS = 4, 2       # 顶部功能键 4 × 2 = 8
MAC_COLS, MAC_ROWS = 2, 5     # 宏键 2 × 5 = 10
NUM_COLS, NUM_ROWS = 4, 5     # 数字区 4 × 5 格 = 17 键

FN_W = FN_COLS * PITCH        # 76.20
NUM_W = NUM_COLS * PITCH      # 76.20
MAC_W = MAC_COLS * PITCH      # 38.10
FN_H = FN_ROWS * PITCH        # 38.10
NUM_H = NUM_ROWS * PITCH      # 95.25

# ---- 岛的坐标 ----
LEFT_ISLAND = (MARGIN_EDGE, MARGIN_EDGE,
               MARGIN_EDGE + DIAL_ISLAND, None)          # 左下角稍后算
BOARD_W = MARGIN_EDGE + DIAL_ISLAND + GAP + NUM_W + MARGIN_EDGE
BOARD_H = MARGIN_EDGE + DIAL_ISLAND + GAP + NUM_H + MARGIN_EDGE

LX0 = MARGIN_EDGE                              # 左岛
LX1 = LX0 + DIAL_ISLAND                        # 59.00
LY0 = MARGIN_EDGE                              # 6.00
LY1 = BOARD_H - MARGIN_EDGE                    # 158.25

RX0 = LX1 + GAP                                # 63.00
RX1 = RX0 + NUM_W                              # 139.20
RY0 = LY0
RY1 = LY1

SPLIT_Y0 = LY0 + DIAL_ISLAND                   # 59.00  横向沟槽上沿
SPLIT_Y1 = SPLIT_Y0 + GAP                      # 63.00  横向沟槽下沿

DIAL_C = (LX0 + DIAL_ISLAND / 2, LY0 + DIAL_ISLAND / 2)   # (32.50, 32.50)

# 键区原点
FN_X0, FN_Y0 = RX0, LY0 + (DIAL_ISLAND - FN_H) / 2        # 功能键在顶带内居中
MAC_X0 = DIAL_C[0] - MAC_W / 2                            # 宏键在拨盘岛内居中
MAC_Y0 = SPLIT_Y1
NUM_X0, NUM_Y0 = RX0, SPLIT_Y1

# ---------- 键位表 ----------
# (标签, 副标签, 区, 列, 行, 宽u, 高u)
KEYS = [
    # 顶部功能键 4 × 2
    ("播放", "F1", "fn", 0, 0, 1, 1), ("上一曲", "F2", "fn", 1, 0, 1, 1),
    ("下一曲", "F3", "fn", 2, 0, 1, 1), ("静音", "F4", "fn", 3, 0, 1, 1),
    ("计算器", "F5", "fn", 0, 1, 1, 1), ("剪贴板", "F6", "fn", 1, 1, 1, 1),
    ("截屏", "F7", "fn", 2, 1, 1, 1), ("锁屏", "F8", "fn", 3, 1, 1, 1),
    # 左侧宏键 2 × 5
    ("M1", "宏1", "mac", 0, 0, 1, 1), ("M2", "宏2", "mac", 0, 1, 1, 1),
    ("M3", "宏3", "mac", 0, 2, 1, 1), ("M4", "宏4", "mac", 0, 3, 1, 1),
    ("M5", "宏5", "mac", 0, 4, 1, 1),
    ("M6", "宏6", "mac", 1, 0, 1, 1), ("M7", "宏7", "mac", 1, 1, 1, 1),
    ("M8", "宏8", "mac", 1, 2, 1, 1), ("M9", "宏9", "mac", 1, 3, 1, 1),
    ("M10", "宏10", "mac", 1, 4, 1, 1),
    # 数字区 4 × 5
    ("num", "clear", "num", 0, 0, 1, 1), ("/", "", "num", 1, 0, 1, 1),
    ("*", "", "num", 2, 0, 1, 1), ("−", "", "num", 3, 0, 1, 1),
    ("7", "", "num", 0, 1, 1, 1), ("8", "", "num", 1, 1, 1, 1),
    ("9", "", "num", 2, 1, 1, 1), ("+", "", "num", 3, 1, 1, 2),
    ("4", "", "num", 0, 2, 1, 1), ("5", "", "num", 1, 2, 1, 1),
    ("6", "", "num", 2, 2, 1, 1),
    ("1", "", "num", 0, 3, 1, 1), ("2", "", "num", 1, 3, 1, 1),
    ("3", "", "num", 2, 3, 1, 1),
    ("enter", "", "num", 3, 3, 1, 2),
    ("0", "", "num", 0, 4, 2, 1), (".", "", "num", 2, 4, 1, 1),
]

ZONE_ORIGIN = {"fn": (FN_X0, FN_Y0), "mac": (MAC_X0, MAC_Y0), "num": (NUM_X0, NUM_Y0)}

# ---------- 画布 ----------
S = 8.0
MARGIN = 210
W = int(BOARD_W * S) + 2 * MARGIN
H = int(BOARD_H * S) + 2 * MARGIN + 180
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

FD = "C:/Windows/Fonts"


def f(size: int, bold: bool = False):
    return ImageFont.truetype(os.path.join(FD, "msyhbd.ttc" if bold else "msyh.ttc"), size)


F_KEY = f(22, True)
F_KEY_S = f(18, True)
F_SUB = f(14)
F_DIM = f(19)
F_DIM_S = f(16)
F_NOTE = f(16)
F_PANEL = f(17)
F_PANEL_T = f(19, True)


def X(mm):
    return MARGIN + mm * S


def Y(mm):
    return MARGIN + mm * S


def ctext(x, y, s, font, fill="black"):
    box = d.textbbox((0, 0), s, font=font)
    d.text((x - (box[2] - box[0]) / 2 - box[0], y - (box[3] - box[1]) / 2 - box[1]),
           s, font=font, fill=fill)


def vtext(x, y, s, font, fill):
    tmp = Image.new("RGBA", (620, 44), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((6, 6), s, font=font, fill=fill)
    tmp = tmp.rotate(90, expand=True)
    img.paste(tmp, (int(x), int(y)), tmp)


def dashed_line(p0, p1, color, width=2, dash=10, gap=7):
    (x0, y0), (x1, y1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    if n == 0:
        return
    step = dash + gap
    for i in range(0, n, step):
        t0, t1 = i / n, min((i + dash) / n, 1.0)
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=color, width=width)


def dashed_circle(cx, cy, r, color, width=2, dash=11, gap=8):
    import math as _mm
    circ = 2 * _mm.pi * r
    step = dash + gap
    n = max(12, int(round(circ / step)))
    span = (dash / circ) * 360.0
    for i in range(n):
        a0 = 360.0 * i / n
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + span, fill=color, width=width)


# ---------- 板框（底色 = 沟槽色，靠深浅把缝读出来） ----------
d.rounded_rectangle([X(0), Y(0), X(BOARD_W), Y(BOARD_H)], radius=3.0 * S,
                    outline="#2c3e50", width=5, fill="#c3cbd6")

# ---------- 四块岛（十字沟槽把它们切开） ----------
ISLAND = "#f7f9fc"
QUADS = [
    (LX0, LY0, LX1, SPLIT_Y0),
    (LX0, SPLIT_Y1, LX1, LY1),
    (RX0, RY0, RX1, SPLIT_Y0),
    (RX0, SPLIT_Y1, RX1, RY1),
]
for (x0, y0, x1, y1) in QUADS:
    d.rectangle([X(x0), Y(y0), X(x1), Y(y1)], fill=ISLAND, outline="#8d97a5", width=3)

# 沟槽中心虚线（视觉上确认是 4 mm 的缝）
dashed_line((X(LX1 + GAP / 2), Y(LY0)), (X(LX1 + GAP / 2), Y(LY1)), "#ffffff", 2, 9, 7)
dashed_line((X(LX0), Y(SPLIT_Y0 + GAP / 2)), (X(RX1), Y(SPLIT_Y0 + GAP / 2)), "#ffffff", 2, 9, 7)

# ---------- M5Dial ----------
import math as _m


def arrow_head(cx, cy, R, ang_deg, color, size=12):
    a = _m.radians(ang_deg)
    x, y = cx + R * _m.cos(a), cy + R * _m.sin(a)
    tx, ty = -_m.sin(a), _m.cos(a)
    nx, ny = _m.cos(a), _m.sin(a)
    d.polygon([(x + tx * size, y + ty * size),
               (x - tx * size * 0.35 + nx * size * 0.8, y - ty * size * 0.35 + ny * size * 0.8),
               (x - tx * size * 0.35 - nx * size * 0.8, y - ty * size * 0.35 - ny * size * 0.8)],
              fill=color)


dx, dy = DIAL_C
rr = DIAL_D / 2 * S          # 旋钮最大外径 φ51（前面能看见的那圈）
rh = HOLE_D / 2 * S          # 面板开孔 Ø45.2（官方建议 Ø45±0.2）
d.ellipse([X(dx) - rr, Y(dy) - rr, X(dx) + rr, Y(dy) + rr],
          fill="#f7d3ce", outline="#c0392b", width=5)
dashed_circle(X(dx), Y(dy), rh, "#d9695c", 3, 11, 8)
# 旋转提示：左右各一段箭头，画在屏外与开孔之间的面板圈上
rkb = (32.5 / 2 + HOLE_D / 2) / 2 * S
for a_mid in (180, 0):
    d.arc([X(dx) - rkb, Y(dy) - rkb, X(dx) + rkb, Y(dy) + rkb],
          a_mid - 30, a_mid + 30, fill="#c0392b", width=4)
    arrow_head(X(dx), Y(dy), rkb, a_mid + 30, "#c0392b")
rs = 32.5 / 2 * S            # 1.28 吋圆屏，有效显示区 Ø32.5
d.ellipse([X(dx) - rs, Y(dy) - rs, X(dx) + rs, Y(dy) + rs],
          fill="#fbd9d4", outline="#7f8c8d", width=3)
d.line([X(dx) - rs, Y(dy), X(dx) + rs, Y(dy)], fill="#e8b4ad", width=1)
d.line([X(dx), Y(dy) - rs, X(dx), Y(dy) + rs], fill="#e8b4ad", width=1)
ctext(X(dx), Y(dy) + 30, "1.28″ 圆屏", f(14), "#a0524a")


def chip(cx, cy, s, font, fg, bg="#ffffff"):
    x0, y0, x1, y1 = d.textbbox((0, 0), s, font=font)
    w, h = x1 - x0, y1 - y0
    d.rounded_rectangle([cx - w / 2 - 8, cy - h / 2 - 5, cx + w / 2 + 8, cy + h / 2 + 5],
                        radius=6, fill=bg, outline="#e0b3ac", width=1)
    d.text((cx, cy), s, font=font, fill=fg, anchor="mm")


chip(X(dx), Y(dy) - 20.2 * S, "M5Dial", f(15, True), "#c0392b")
chip(X(dx), Y(dy) + 20.6 * S, f"外径φ{DIAL_D:.0f}·高{DIAL_TH:.1f}·开孔φ{HOLE_D:.1f}",
     f(13), "#c0392b")

# ---------- 键位 ----------
INSET = 1.3
for label, sub, zone, c, r_, wu, hu in KEYS:
    ox, oy = ZONE_ORIGIN[zone]
    x0 = X(ox + c * PITCH) + INSET * S
    y0 = Y(oy + r_ * PITCH) + INSET * S
    x1 = X(ox + (c + wu) * PITCH) - INSET * S
    y1 = Y(oy + (r_ + hu) * PITCH) - INSET * S
    d.rounded_rectangle([x0, y0, x1, y1], radius=8,
                        fill="#ffffff", outline="#95a5a6", width=3)
    ty = (y0 + y1) / 2 - (9 if sub else 0)
    ctext((x0 + x1) / 2, ty, label, F_KEY if len(label) <= 4 else F_KEY_S, "#2c3e50")
    if sub:
        ctext((x0 + x1) / 2, ty + 25, sub, F_SUB, "#95a5a6")

# ---------- 安装孔 ----------
HOLES = [(3, 3), (BOARD_W - 3, 3), (3, BOARD_H - 3), (BOARD_W - 3, BOARD_H - 3),
         (3, BOARD_H / 2), (BOARD_W - 3, BOARD_H / 2)]
for hx, hy in HOLES:
    hrr = 1.7 * S
    d.ellipse([X(hx) - hrr, Y(hy) - hrr, X(hx) + hrr, Y(hy) + hrr],
              outline="#2c3e50", width=3)
    d.line([X(hx) - hrr, Y(hy), X(hx) + hrr, Y(hy)], fill="#2c3e50", width=2)
    d.line([X(hx), Y(hy) - hrr, X(hx), Y(hy) + hrr], fill="#2c3e50", width=2)

# ---------- 尺寸标注 ----------
# 板宽
y_dim = Y(BOARD_H) + 44
d.line([X(0), y_dim, X(BOARD_W), y_dim], fill="#c0392b", width=2)
for xx in (X(0), X(BOARD_W)):
    d.line([xx, y_dim - 11, xx, y_dim + 11], fill="#c0392b", width=2)
ctext(X(BOARD_W / 2), y_dim + 28, f"板 / 外壳 {BOARD_W:.2f} mm", F_DIM, "#c0392b")

# 板高
x_dim = X(BOARD_W) + 48
d.line([x_dim, Y(0), x_dim, Y(BOARD_H)], fill="#c0392b", width=2)
for yy in (Y(0), Y(BOARD_H)):
    d.line([x_dim - 11, yy, x_dim + 11, yy], fill="#c0392b", width=2)
vtext(x_dim + 16, Y(BOARD_H / 2) - 130, f"板 / 外壳 {BOARD_H:.2f} mm", F_DIM, "#c0392b")

# 左岛宽（顶带内）
y_ld = Y(0) - 42
d.line([X(0), y_ld, X(LX1), y_ld], fill="#2980b9", width=2)
for xx in (X(0), X(LX1)):
    d.line([xx, y_ld - 9, xx, y_ld + 9], fill="#2980b9", width=2)
ctext(X(LX1 / 2), y_ld - 24, f"左岛 {DIAL_ISLAND:.2f}", F_DIM_S, "#2980b9")

# 右岛宽（顶带内）
d.line([X(RX0), y_ld, X(RX1), y_ld], fill="#2980b9", width=2)
for xx in (X(RX0), X(RX1)):
    d.line([xx, y_ld - 9, xx, y_ld + 9], fill="#2980b9", width=2)
ctext(X((RX0 + RX1) / 2), y_ld - 24, f"右岛 {NUM_W:.2f}（4 × 19.05）", F_DIM_S, "#2980b9")

# 沟槽 4 mm（在十字交点做标注）
gx = X(LX1 + GAP / 2)
gy = Y(SPLIT_Y0 + GAP / 2)
d.line([X(LX1) - 16, gy, X(LX1) + 10, gy], fill="#27ae60", width=2)
d.line([X(RX0) + 16, gy, X(RX0) - 10, gy], fill="#27ae60", width=2)
d.line([gx, Y(SPLIT_Y0) - 16, gx, Y(SPLIT_Y0) + 10], fill="#27ae60", width=2)
d.line([gx, Y(SPLIT_Y1) + 16, gx, Y(SPLIT_Y1) - 10], fill="#27ae60", width=2)
ctext(gx - 92, gy - 2, f"沟槽 {GAP:.1f} mm", f(16, True), "#27ae60")

# 键区高（左侧）
x_kh = X(0) - 44
d.line([x_kh, Y(NUM_Y0), x_kh, Y(NUM_Y0 + NUM_H)], fill="#2980b9", width=2)
for yy in (Y(NUM_Y0), Y(NUM_Y0 + NUM_H)):
    d.line([x_kh - 9, yy, x_kh + 9, yy], fill="#2980b9", width=2)
vtext(x_kh - 64, Y(NUM_Y0 + NUM_H / 2) - 150,
      f"下段 {NUM_H:.2f}（5 × 19.05）", F_DIM_S, "#2980b9")

# 上段高（左侧，拨盘/功能键那一带）
d.line([x_kh, Y(LY0), x_kh, Y(SPLIT_Y0)], fill="#2980b9", width=2)
for yy in (Y(LY0), Y(SPLIT_Y0)):
    d.line([x_kh - 9, yy, x_kh + 9, yy], fill="#2980b9", width=2)
vtext(x_kh - 64, Y(LY0) + 40,
      f"上段 {DIAL_ISLAND:.2f}", F_DIM_S, "#2980b9")

# ---------- 左上：区域说明 ----------
def panel(x, y, w, h, title, lines, title_color="#2c3e50"):
    d.rectangle([x, y, x + w, y + h], outline="#bdc3c7", width=2, fill="white")
    d.text((x + 16, y + 12), title, font=F_PANEL_T, fill=title_color)
    for i, (txt, col) in enumerate(lines):
        d.text((x + 16, y + 46 + i * 27), txt, font=F_PANEL, fill=col)


ly = Y(BOARD_H) + 96
panel(MARGIN, ly, 620, 178, "v3 十字沟槽 + M5Dial（2026-11-15）", [
    ("四块岛：左上拨盘 / 左下宏键 10 / 右上功能键 8 / 右下数字区 17", "#34495e"),
    (f"岛与岛之间 {GAP:.0f} mm 沟槽 —— 切的是上盖/定位板，PCB 仍是整块", "#34495e"),
    (f"M5Dial 外径 φ{DIAL_D:.0f}、总高 {DIAL_TH:.1f}，面板开孔 φ{HOLE_D:.1f}（不是 51）", "#c0392b"),
    ("单线出线：板载 CH334P Hub，键盘与拨盘共用一个 USB-C", "#1e8449"),
    (f"键数 35，矩阵仍 7 × 6 —— 与 v2 完全一致，固件不用改", "#27ae60"),
])

panel(MARGIN + 650, ly, 620, 178, "尺寸对比（v2 → v3）", [
    (f"板宽 126.30 → {BOARD_W:.2f} mm（+{BOARD_W - 126.30:.2f}）", "#2c3e50"),
    (f"板高 157.35 → {BOARD_H:.2f} mm（+{BOARD_H - 157.35:.2f}）", "#2c3e50"),
    (f"左上岛 {DIAL_ISLAND:.2f} × {DIAL_ISLAND:.2f}，φ{DIAL_D:.0f} 机身四周各留 1.0", "#7f8c8d"),
    ("右上岛 76.20 × 53.00，功能键 2 行在其中垂直居中", "#7f8c8d"),
    ("左下/右下岛高 95.25（5 × 19.05），键位 19.05 栅格对齐", "#7f8c8d"),
])

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "layout_v3.png")
img.save(out)
print("saved", out, img.size)
print(f"BOARD {BOARD_W:.2f} x {BOARD_H:.2f}")
print(f"islands L({LX0},{LY0})-({LX1},{LY1})  R({RX0},{RY0})-({RX1},{RY1})")
print(f"split y {SPLIT_Y0:.2f}..{SPLIT_Y1:.2f}   dial center {DIAL_C}")
print(f"fn origin ({FN_X0},{FN_Y0})  mac origin ({MAC_X0},{MAC_Y0})  num origin ({NUM_X0},{NUM_Y0})")
