# -*- coding: utf-8 -*-
"""生成 M5Dial 屏幕贴图（240×240），给 Blender 渲染用。

输出 img/dial_face_240.png：深色圆屏，中间显示
  时钟 / 曲名+歌手 / 大号帧数 / 30 秒帧率走势 / 1% low
内容全部落在内接圆里，方形贴图的四角会被圆屏遮掉。
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

SIZE = 240
FONT_DIR = r"C:\Windows\Fonts"


def font(name, size):
    p = os.path.join(FONT_DIR, name)
    if os.path.exists(p):
        try:
            return ImageFont.truetype(p, size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


img = Image.new("RGB", (SIZE, SIZE), "#0f131a")
d = ImageDraw.Draw(img)
C = SIZE / 2.0

# 一层很淡的内发光，让屏幕看起来不是纯黑
for i in range(28, 0, -1):
    a = int(6 * (1 - i / 28.0)) + 1
    r = 118 - i * 1.2
    d.ellipse([C - r, C - r, C + r, C + r], outline=(16 + a, 22 + a, 32 + a))

F_CLOCK = font("msyh.ttc", 21)
F_TRACK = font("msyhbd.ttc", 23)
F_ART = font("msyh.ttc", 15)
F_FPS = font("msyhbd.ttc", 46)
F_LOW = font("msyh.ttc", 12)


def ctext(y, s, fnt, col):
    box = d.textbbox((0, 0), s, font=fnt)
    w = box[2] - box[0]
    h = box[3] - box[1]
    d.text((C - w / 2 - box[0], y - h / 2 - box[1]), s, font=fnt, fill=col)


ctext(50, "09:41", F_CLOCK, "#7d8b9c")
ctext(96, "夜空中最亮的星", F_TRACK, "#eef3f9")
ctext(120, "逃跑计划", F_ART, "#7d8b9c")

# 细分隔线
d.line([C - 46, 138, C + 46, 138], fill="#25303d", width=1)

ctext(166, "144", F_FPS, "#46d68a")

# 30 秒帧率走势
hist = [0.92, 0.86, 0.94, 0.70, 0.66, 0.79, 0.85, 0.90, 0.95, 0.98,
        0.92, 0.84, 0.76, 0.68, 0.75, 0.87, 0.94, 1.0, 0.92, 0.89,
        0.85, 0.90, 0.94, 1.0, 0.96, 0.90, 0.87, 0.92, 0.97, 0.94]
x0, x1 = 62, 178
ybase, yh = 208, 20
pts = [(x0 + (x1 - x0) * i / (len(hist) - 1), ybase - v * yh) for i, v in enumerate(hist)]
d.polygon(pts + [(x1, ybase), (x0, ybase)], fill="#16301f")
d.line(pts, fill="#46d68a", width=2, joint="curve")

ctext(224, "1% low  96", F_LOW, "#6b7785")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "dial_face_240.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("saved", out, img.size)
