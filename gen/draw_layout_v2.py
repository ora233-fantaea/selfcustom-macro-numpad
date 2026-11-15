"""v2 布局方案顶视图（概念图，不涉及 PCB）。

用法：python gen/draw_layout_v2.py
输出：img/layout_v2.png
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

# ---------- 几何参数（mm） ----------
PITCH = 19.05
COLS, ROWS = 6, 7
BOARD_W, BOARD_H = 126.30, 157.35
BAY_H = 18.0                      # 后缘电子舱
MX, MY = 6.0, BAY_H               # 键区原点
CORNER_R = 3.0
MODULE_MM = 43.5                  # 圆屏旋钮模块占位（最小款）
MODULE_CELL = 2 * PITCH           # 预留 2x2 格 = 38.10

# ---------- 键位表 ----------
# (标签, 副标签, 列, 行, 宽u, 高u)
KEYS = [
    # 顶排功能键（2 排 × 4）
    ("播放", "F1", 2, 0, 1, 1), ("上一曲", "F2", 3, 0, 1, 1),
    ("下一曲", "F3", 4, 0, 1, 1), ("静音", "F4", 5, 0, 1, 1),
    ("计算器", "F5", 2, 1, 1, 1), ("剪贴板", "F6", 3, 1, 1, 1),
    ("截屏", "F7", 4, 1, 1, 1), ("锁屏", "F8", 5, 1, 1, 1),
    # 左侧宏键（2 列 × 5）
    ("M1", "宏1", 0, 2, 1, 1), ("M2", "宏2", 0, 3, 1, 1),
    ("M3", "宏3", 0, 4, 1, 1), ("M4", "宏4", 0, 5, 1, 1),
    ("M5", "宏5", 0, 6, 1, 1),
    ("M6", "宏6", 1, 2, 1, 1), ("M7", "宏7", 1, 3, 1, 1),
    ("M8", "宏8", 1, 4, 1, 1), ("M9", "宏9", 1, 5, 1, 1),
    ("M10", "宏10", 1, 6, 1, 1),
    # 数字区（4 列 × 5 行，17 键）
    ("num", "clear", 2, 2, 1, 1), ("/", "", 3, 2, 1, 1),
    ("*", "", 4, 2, 1, 1), ("−", "", 5, 2, 1, 1),
    ("7", "", 2, 3, 1, 1), ("8", "", 3, 3, 1, 1),
    ("9", "", 4, 3, 1, 1), ("+", "", 5, 3, 1, 2),
    ("4", "", 2, 4, 1, 1), ("5", "", 3, 4, 1, 1), ("6", "", 4, 4, 1, 1),
    ("1", "", 2, 5, 1, 1), ("2", "", 3, 5, 1, 1), ("3", "", 4, 5, 1, 1),
    ("enter", "", 5, 5, 1, 2),
    ("0", "", 2, 6, 2, 1), (".", "", 4, 6, 1, 1),
]

S = 8.0          # 每毫米像素
MARGIN = 200     # 标注留白

W = int(BOARD_W * S) + 2 * MARGIN
H = int(BOARD_H * S) + 2 * MARGIN + 170
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

FD = "C:/Windows/Fonts"


def f(size: int, bold: bool = False):
    return ImageFont.truetype(os.path.join(FD, "msyhbd.ttc" if bold else "msyh.ttc"), size)


F_KEY = f(21, True)
F_KEY_S = f(18, True)
F_SUB = f(14)
F_DIM = f(18)
F_NOTE = f(16)
F_PANEL = f(17)


def X(mm: float) -> float:
    return MARGIN + mm * S


def Y(mm: float) -> float:
    return MARGIN + mm * S


def ctext(x, y, s, font, fill="black"):
    box = d.textbbox((0, 0), s, font=font)
    d.text((x - (box[2] - box[0]) / 2 - box[0], y - (box[3] - box[1]) / 2 - box[1]),
           s, font=font, fill=fill)


def dashed_rect(box, color, width=3, dash=12, gap=8):
    x0, y0, x1, y1 = box
    for x in range(int(x0), int(x1), dash + gap):
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=color, width=width)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=color, width=width)
    for y in range(int(y0), int(y1), dash + gap):
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=color, width=width)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=color, width=width)


def vtext(x, y, s, font, fill):
    tmp = Image.new("RGBA", (600, 44), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((6, 6), s, font=font, fill=fill)
    tmp = tmp.rotate(90, expand=True)
    img.paste(tmp, (int(x), int(y)), tmp)


# ---------- 板框 ----------
d.rounded_rectangle([X(0), Y(0), X(BOARD_W), Y(BOARD_H)], radius=CORNER_R * S,
                    outline="#2c3e50", width=5, fill="#f4f5f7")

# ---------- 电子舱 ----------
d.rectangle([X(0), Y(0), X(BOARD_W), Y(BAY_H)], fill="#e4e7ec")
d.line([X(0), Y(BAY_H), X(BOARD_W), Y(BAY_H)], fill="#2c3e50", width=3)
d.text((X(50), Y(5) - 12),
       "电子舱 18 mm　RP2040 / Flash / 晶振 / LDO / ESD 贴背面",
       font=f(15), fill="#34495e")
d.text((X(50), Y(12) - 12),
       "USB-C 靠右后缘（模块占位处只放扁平件）",
       font=f(15), fill="#34495e")

# ---------- 模块占位 ----------
mx0, my0 = X(MX), Y(MY)
mx1, my1 = X(MX + MODULE_CELL), Y(MY + MODULE_CELL)
d.rectangle([mx0, my0, mx1, my1], fill="#fdecea", outline="#c0392b", width=4)
off = (MODULE_CELL - MODULE_MM) / 2 * S
dashed_rect([mx0 - off, my0 - off, mx1 + off, my1 + off], "#c0392b", width=3)
cx, cy = (mx0 + mx1) / 2, (my0 + my1) / 2
r = 32.4 / 2 * S     # 1.28 吋圆屏 φ32.4
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#7f8c8d", width=3)
d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill="#7f8c8d")
d.line([cx - r, cy, cx + r, cy], fill="#bdc3c7", width=1)
d.line([cx, cy - r, cx, cy + r], fill="#bdc3c7", width=1)
ctext(cx, Y(0) + 26, "ESP32-S3 圆屏旋钮", F_KEY_S, "#c0392b")
ctext(cx, Y(0) + 52, "43.5 × 43.5（外凸 2.7）", F_SUB, "#c0392b")

# ---------- 键位 ----------
for label, sub, c, r_, wu, hu in KEYS:
    x0 = X(MX + c * PITCH) + 1.3 * S
    y0 = Y(MY + r_ * PITCH) + 1.3 * S
    x1 = X(MX + (c + wu) * PITCH) - 1.3 * S
    y1 = Y(MY + (r_ + hu) * PITCH) - 1.3 * S
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill="#ffffff", outline="#95a5a6", width=3)
    ty = (y0 + y1) / 2 - (10 if sub else 0)
    ctext((x0 + x1) / 2, ty, label, F_KEY if len(label) <= 4 else F_KEY_S, "#2c3e50")
    if sub:
        ctext((x0 + x1) / 2, ty + 26, sub, F_SUB, "#95a5a6")

# ---------- 安装孔 ----------
HOLES = [(3, 3), (BOARD_W - 3, 3), (3, BOARD_H - 3), (BOARD_W - 3, BOARD_H - 3),
         (3, 88), (BOARD_W - 3, 88)]
for hx, hy in HOLES:
    rr = 1.7 * S
    d.ellipse([X(hx) - rr, Y(hy) - rr, X(hx) + rr, Y(hy) + rr], outline="#2c3e50", width=3)
    d.line([X(hx) - rr, Y(hy), X(hx) + rr, Y(hy)], fill="#2c3e50", width=2)
    d.line([X(hx), Y(hy) - rr, X(hx), Y(hy) + rr], fill="#2c3e50", width=2)

# ---------- 尺寸标注 ----------
# 键区宽（板外上方）
y_kd = Y(0) - 46
d.line([X(MX), y_kd, X(MX + COLS * PITCH), y_kd], fill="#2980b9", width=2)
for xx in (X(MX), X(MX + COLS * PITCH)):
    d.line([xx, y_kd - 9, xx, y_kd + 9], fill="#2980b9", width=2)
ctext(X(MX + COLS * PITCH / 2), y_kd - 24, "键区 114.30 mm（6 × 19.05）", F_DIM, "#2980b9")

# 键区高（板外左侧）
x_kh = X(0) - 46
d.line([x_kh, Y(MY), x_kh, Y(MY + ROWS * PITCH)], fill="#2980b9", width=2)
for yy in (Y(MY), Y(MY + ROWS * PITCH)):
    d.line([x_kh - 9, yy, x_kh + 9, yy], fill="#2980b9", width=2)
vtext(x_kh - 62, Y(MY + ROWS * PITCH / 2) - 150, "键区 133.35 mm（7 × 19.05）", F_DIM, "#2980b9")

# 外壳宽（板外下方）
y_dim = Y(BOARD_H) + 40
d.line([X(0), y_dim, X(BOARD_W), y_dim], fill="#c0392b", width=2)
for xx in (X(0), X(BOARD_W)):
    d.line([xx, y_dim - 10, xx, y_dim + 10], fill="#c0392b", width=2)
ctext(X(BOARD_W / 2), y_dim + 26, "外壳 126.30 mm", F_DIM, "#c0392b")

# 外壳高（板外右侧）
x_dim = X(BOARD_W) + 46
d.line([x_dim, Y(0), x_dim, Y(BOARD_H)], fill="#c0392b", width=2)
for yy in (Y(0), Y(BOARD_H)):
    d.line([x_dim - 10, yy, x_dim + 10, yy], fill="#c0392b", width=2)
vtext(x_dim + 16, Y(BOARD_H / 2) - 130, "外壳 157.35 mm", F_DIM, "#c0392b")

# ---------- 左下：图例 ----------
lx, ly = MARGIN, Y(BOARD_H) + 92
d.rectangle([lx, ly, lx + 540, ly + 128], outline="#bdc3c7", width=2)
d.text((lx + 16, ly + 12), "35 键 + ESP32 模块（v2 概念）", font=f(18, True), fill="#2c3e50")
d.text((lx + 16, ly + 44), f"矩阵 {ROWS} 行 × {COLS} 列，模块占 R0C0~R1C1 共 4 格不用", font=F_PANEL, fill="#34495e")
d.text((lx + 16, ly + 72), "轴座 35 / 二极管 35 / 安装孔 6 × φ3.4", font=F_PANEL, fill="#34495e")
d.text((lx + 16, ly + 100), "没有 EC11——旋钮与屏幕都在 ESP32 模块上", font=F_PANEL, fill="#c0392b")

# ---------- 右下：还能往外长 ----------
px = lx + 560
d.rectangle([px, ly, px + 500, ly + 128], outline="#bdc3c7", width=2)
d.text((px + 16, ly + 12), "还想加键的话（按箭头方向）", font=f(18, True), fill="#2c3e50")
d.text((px + 16, ly + 44), "顶排 +1 排（4 键）→ 板高 +19.05，电子舱上移", font=F_PANEL, fill="#34495e")
d.text((px + 16, ly + 72), "左列 +1 列（5 键）→ 板宽 +19.05", font=F_PANEL, fill="#34495e")
d.text((px + 16, ly + 100), "两方向都加满：44 键，133.35 × 152.40 键区", font=F_PANEL, fill="#34495e")

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "layout_v2.png")
img.save(out)
print("saved", out, img.size)
