# -*- coding: utf-8 -*-
"""v4 概念成品渲染：35 键 numpad + M5Dial（Blender 5.x，无头）。

几何全部取自 gen/draw_layout_v3.py 的同一套 mm 坐标：
  板 145.20 × 164.25，键位 19.05 栅格，四块岛 + 4 mm 十字沟槽，
  拨盘 Ø51 / 面板开孔 Ø45.2 / 屏 Ø32.5。
整机前缘 21.4 / 后缘 34.6 mm，键面按这个高差倾斜。

用法（headless）：
  blender -b -P gen/render_product.py -- --res 1600x1200 --samples 128 --out img/product_hero.png
环境变量 PREVIEW=1 时降级成 720x720 / 24 samples，用于快速看形。
"""
import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector

# ------------------------------------------------------------------ 参数
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


PREVIEW = os.environ.get("PREVIEW") == "1"
RES_X, RES_Y = (720, 720) if PREVIEW else (1600, 1200)
SAMPLES = 24 if PREVIEW else 128
OUT = arg("--out") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "img", "product_hero.png")
if arg("--res"):
    RES_X, RES_Y = (int(v) for v in arg("--res").split("x"))
if arg("--samples"):
    SAMPLES = int(arg("--samples"))

# ------------------------------------------------------------------ 尺寸（mm）
MM = 0.001
PITCH = 19.05
GAP = 4.00
MARGIN_EDGE = 6.00
DIAL_D = 51.00
HOLE_D = 45.20
DIAL_ISLAND = 53.00

FN_COLS, FN_ROWS = 4, 2
MAC_COLS, MAC_ROWS = 2, 5
NUM_COLS, NUM_ROWS = 4, 5

FN_W = FN_COLS * PITCH
NUM_W = NUM_COLS * PITCH
MAC_W = MAC_COLS * PITCH
FN_H = FN_ROWS * PITCH
NUM_H = NUM_ROWS * PITCH

BOARD_W = MARGIN_EDGE + DIAL_ISLAND + GAP + NUM_W + MARGIN_EDGE      # 145.20
BOARD_H = MARGIN_EDGE + DIAL_ISLAND + GAP + NUM_H + MARGIN_EDGE      # 164.25

LX0, LX1 = MARGIN_EDGE, MARGIN_EDGE + DIAL_ISLAND
LY0, LY1 = MARGIN_EDGE, BOARD_H - MARGIN_EDGE
RX0, RX1 = LX1 + GAP, LX1 + GAP + NUM_W
SPLIT_Y0 = LY0 + DIAL_ISLAND
SPLIT_Y1 = SPLIT_Y0 + GAP
DIAL_C = (LX0 + DIAL_ISLAND / 2, LY0 + DIAL_ISLAND / 2)

FN_X0, FN_Y0 = RX0, LY0 + (DIAL_ISLAND - FN_H) / 2
MAC_X0, MAC_Y0 = DIAL_C[0] - MAC_W / 2, SPLIT_Y1
NUM_X0, NUM_Y0 = RX0, SPLIT_Y1
ZONE_ORIGIN = {"fn": (FN_X0, FN_Y0), "mac": (MAC_X0, MAC_Y0), "num": (NUM_X0, NUM_Y0)}

H_FRONT, H_BACK = 21.40, 34.60
SLOPE = (H_BACK - H_FRONT) / BOARD_H
THETA = math.atan(SLOPE)                 # 键面倾角
GROOVE_DEPTH = 3.00
CAP_H = 8.40
CAP_DISH = 0.75
KEY_INSET = 0.55

KEYS = [
    ("播放", "", "fn", 0, 0, 1, 1), ("上一曲", "", "fn", 1, 0, 1, 1),
    ("下一曲", "", "fn", 2, 0, 1, 1), ("静音", "", "fn", 3, 0, 1, 1),
    ("计算器", "", "fn", 0, 1, 1, 1), ("剪贴板", "", "fn", 1, 1, 1, 1),
    ("截屏", "", "fn", 2, 1, 1, 1), ("锁屏", "", "fn", 3, 1, 1, 1),
    ("M1", "", "mac", 0, 0, 1, 1), ("M2", "", "mac", 0, 1, 1, 1),
    ("M3", "", "mac", 0, 2, 1, 1), ("M4", "", "mac", 0, 3, 1, 1),
    ("M5", "", "mac", 0, 4, 1, 1),
    ("M6", "", "mac", 1, 0, 1, 1), ("M7", "", "mac", 1, 1, 1, 1),
    ("M8", "", "mac", 1, 2, 1, 1), ("M9", "", "mac", 1, 3, 1, 1),
    ("M10", "", "mac", 1, 4, 1, 1),
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

ISLANDS = [
    (LX0, LY0, LX1, SPLIT_Y0),
    (LX0, SPLIT_Y1, LX1, LY1),
    (RX0, LY0, RX1, SPLIT_Y0),
    (RX0, SPLIT_Y1, RX1, LY1),
]


# ------------------------------------------------------------------ 坐标换算
def deck_mm(y_bl_mm):
    """给定 Blender 空间 Y（mm，+Y 为后缘），返回该处的键面高度（mm）。"""
    return H_FRONT + (y_bl_mm + BOARD_H / 2) * SLOPE


def to_bl(x_layout_mm, y_layout_mm):
    """布局图坐标（y 向下）→ Blender 坐标（mm，+Y 为后缘）。"""
    return x_layout_mm - BOARD_W / 2, BOARD_H / 2 - y_layout_mm


def hx(s):
    s = s.lstrip("#")
    v = [int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in v)


# ------------------------------------------------------------------ 场景清理
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0


def link(name, mesh):
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    return ob


def mat_solid(name, rgb, rough=0.5, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*hx(rgb), 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    return m


MAT_CASE = mat_solid("M_Case", "#1e2228", 0.46, 0.25)
MAT_DECK = mat_solid("M_Deck", "#313842", 0.42, 0.15)
MAT_CAP = mat_solid("M_Key", "#e7e3da", 0.55, 0.0)
MAT_CAP_FN = mat_solid("M_KeyFn", "#c3c8cf", 0.52, 0.0)
MAT_CAP_MAC = mat_solid("M_KeyMac", "#c8673c", 0.55, 0.0)
MAT_LEGEND = mat_solid("M_Legend", "#1b1f24", 0.62, 0.0)
MAT_RING = mat_solid("M_Knob", "#1a1d22", 0.33, 0.72)
MAT_RING_TOP = mat_solid("M_KnobTop", "#0e1013", 0.16, 0.35, 0.7)
MAT_GROUND = mat_solid("M_Ground", "#c9ccd1", 0.45, 0.0)


# ------------------------------------------------------------------ 几何工具
def rrect_points(w, d, r, seg=10):
    """圆角矩形轮廓（mm），逆时针。"""
    pts = []
    corners = [(w / 2 - r, d / 2 - r, 0), (-(w / 2 - r), d / 2 - r, 90),
               (-(w / 2 - r), -(d / 2 - r), 180), (w / 2 - r, -(d / 2 - r), 270)]
    for cx, cy, a0 in corners:
        for i in range(seg):
            a = math.radians(a0 + 90.0 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def prism(name, pts, z_bot_fn, z_top_fn, material, edge_bevel=0.0):
    bm = bmesh.new()
    vb = [bm.verts.new((x * MM, y * MM, z_bot_fn(x, y) * MM)) for x, y in pts]
    vt = [bm.verts.new((x * MM, y * MM, z_top_fn(x, y) * MM)) for x, y in pts]
    bm.verts.ensure_lookup_table()
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(name, me)
    me.materials.append(material)
    if edge_bevel > 0:
        md = ob.modifiers.new("bev", "BEVEL")
        md.width = edge_bevel * MM
        md.segments = 2
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(40)
    return ob


def keycap(name, w, d, h, material, taper=0.80, dish=0.75, grid=6):
    tw, td = w * taper, d * taper
    bm = bmesh.new()
    bot = [bm.verts.new((sx * w / 2 * MM, sy * d / 2 * MM, 0.0))
           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    # 顶面做成 N×N 网格，中间下凹成球形（真实键帽的 dish）
    top = []
    for iv in range(grid):
        v = -1.0 + 2.0 * iv / (grid - 1)
        row = []
        for iu in range(grid):
            u = -1.0 + 2.0 * iu / (grid - 1)
            z = h - dish * (1.0 - u * u) * (1.0 - v * v)
            row.append(bm.verts.new((u * tw / 2 * MM, v * td / 2 * MM, z * MM)))
        top.append(row)
    bm.faces.new(list(reversed(bot)))
    for iv in range(grid - 1):
        for iu in range(grid - 1):
            bm.faces.new((top[iv][iu], top[iv][iu + 1],
                          top[iv + 1][iu + 1], top[iv + 1][iu]))
    rim = ([top[0][i] for i in range(grid)] +
           [top[i][grid - 1] for i in range(1, grid)] +
           [top[grid - 1][i] for i in range(grid - 2, -1, -1)] +
           [top[i][0] for i in range(grid - 2, 0, -1)])
    for i in range(4):
        j = (i + 1) % 4
        k0 = i * (grid - 1)
        k1 = j * (grid - 1)
        bm.faces.new((bot[i], bot[j], rim[k1], rim[k0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(name, me)
    me.materials.append(material)
    md = ob.modifiers.new("bev", "BEVEL")
    md.width = 1.35 * MM
    md.segments = 3
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(40)
    return ob


FONT = None
for fp in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
           r"C:\Windows\Fonts\simhei.ttf"):
    if os.path.exists(fp):
        try:
            FONT = bpy.data.fonts.load(fp)
            break
        except Exception:
            continue


def legend(name, body, size_mm, location, tw, td, material=MAT_LEGEND,
           lift=0.06):
    """刻字：转成网格后按键帽盘面下凹量逐点抬高，字随曲面走而不是一块浮板。"""
    cu = bpy.data.curves.new(name + "_CRV", type="FONT")
    cu.body = body
    if FONT:
        cu.font = FONT
    cu.size = size_mm * MM
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    src = link(name + "_SRC", cu)
    src.location = location
    src.rotation_euler = (THETA, 0.0, 0.0)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
    hx_, hy_ = tw * 0.5 * MM, td * 0.5 * MM
    for v in me.vertices:
        u = min(1.0, abs(v.co.x) / hx_)
        w = min(1.0, abs(v.co.y) / hy_)
        v.co.z += (CAP_DISH * (1.0 - (1.0 - u * u) * (1.0 - w * w)) + lift) * MM
    me.name = name
    bpy.data.objects.remove(src, do_unlink=True)
    bpy.data.curves.remove(cu)
    ob = link(name, me)
    me.materials.append(material)
    ob.location = location
    ob.rotation_euler = (THETA, 0.0, 0.0)
    return ob


# ------------------------------------------------------------------ 外壳
case_pts = rrect_points(BOARD_W, BOARD_H, 3.0, seg=12)
prism("CASE", case_pts,
      z_bot_fn=lambda x, y: 0.0,
      z_top_fn=lambda x, y: deck_mm(y) - GROOVE_DEPTH,
      material=MAT_CASE, edge_bevel=2.2)

for i, (x0, y0, x1, y1) in enumerate(ISLANDS):
    w, d = x1 - x0, y1 - y0
    pts_local = rrect_points(w, d, 2.2, seg=8)
    cx, cy = to_bl((x0 + x1) / 2, (y0 + y1) / 2)
    pts = [(cx + px, cy + py) for px, py in pts_local]
    prism("ISLAND_%d" % i, pts,
          z_bot_fn=lambda x, y: deck_mm(y) - GROOVE_DEPTH,
          z_top_fn=lambda x, y: deck_mm(y),
          material=MAT_DECK, edge_bevel=0.9)

# ------------------------------------------------------------------ 键帽
for label_text, sub, zone, c, r, wu, hu in KEYS:
    ox, oy = ZONE_ORIGIN[zone]
    x_mm = ox + (c + wu / 2.0) * PITCH
    y_lay = oy + (r + hu / 2.0) * PITCH
    x_bl, y_bl = to_bl(x_mm, y_lay)
    z = deck_mm(y_bl)
    w = wu * PITCH - 2 * KEY_INSET
    d = hu * PITCH - 2 * KEY_INSET
    m = MAT_CAP_MAC if zone == "mac" else (MAT_CAP_FN if zone == "fn" else MAT_CAP)
    ob = keycap("KEY_" + label_text, w, d, CAP_H, m)
    ob.location = (x_bl * MM, y_bl * MM, z * MM)
    ob.rotation_euler = (THETA, 0.0, 0.0)
    # 顶面刻字
    n = (0.0, -math.sin(THETA), math.cos(THETA))
    top = (Vector((x_bl * MM, y_bl * MM, z * MM))
           + Vector(n) * ((CAP_H - CAP_DISH) * MM))
    fsz = 4.6 if len(label_text) <= 2 else 3.5
    legend("LBL_" + label_text, label_text, fsz, tuple(top),
           w * 0.80, d * 0.80)

# ------------------------------------------------------------------ M5Dial
dx_l, dy_l = DIAL_C
kx, ky = to_bl(dx_l, dy_l)
kz = deck_mm(ky)                     # 面板顶面
KH = 7.6                             # 旋钮露出高度
R_OUT, R_GROOVE = DIAL_D / 2, DIAL_D / 2 - 0.65
N_FLUTE = 44
R_BEZEL_IN = 18.00
R_SCREEN = 17.05
RECESS = 1.60

bm = bmesh.new()
outer_top, outer_bot, inner_top = [], [], []
for i in range(N_FLUTE * 2):
    a = 2 * math.pi * i / (N_FLUTE * 2)
    rr = R_OUT if i % 2 == 0 else R_GROOVE
    x, y = kx + rr * math.cos(a), ky + rr * math.sin(a)
    outer_bot.append(bm.verts.new((x * MM, y * MM, kz * MM)))
    outer_top.append(bm.verts.new((x * MM, y * MM, (kz + KH) * MM)))
    x, y = kx + R_BEZEL_IN * math.cos(a), ky + R_BEZEL_IN * math.sin(a)
    inner_top.append(bm.verts.new((x * MM, y * MM, (kz + KH) * MM)))
inner_low = []
for i in range(N_FLUTE * 2):
    a = 2 * math.pi * i / (N_FLUTE * 2)
    x, y = kx + R_SCREEN * math.cos(a), ky + R_SCREEN * math.sin(a)
    inner_low.append(bm.verts.new((x * MM, y * MM, (kz + KH - RECESS) * MM)))
n = N_FLUTE * 2
for i in range(n):
    j = (i + 1) % n
    bm.faces.new((outer_bot[i], outer_bot[j], outer_top[j], outer_top[i]))     # 侧壁滚花
    bm.faces.new((outer_top[i], outer_top[j], inner_top[j], inner_top[i]))     # 顶环
    bm.faces.new((inner_top[i], inner_top[j], inner_low[j], inner_low[i]))     # 内锥
bm.faces.new(list(reversed(outer_bot)))
bm.faces.new(list(reversed(inner_low)))                                        # 屏底
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("KNOB")
bm.to_mesh(me)
bm.free()
knob = link("KNOB", me)
me.materials.append(MAT_RING)
me.materials.append(MAT_RING_TOP)
# 顶环（第 3i+1 个面）用更亮的光面塑料，滚花侧壁保持哑光
for i in range(n):
    k = 3 * i + 1
    if k < len(me.polygons):
        me.polygons[k].material_index = 1

# 屏幕：贴图 + 自发光
tex_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img", "dial_face_240.png")
tex_path = os.path.normpath(tex_path)
mat_screen = bpy.data.materials.new("M_Screen")
mat_screen.use_nodes = True
nt = mat_screen.node_tree
for nd in list(nt.nodes):
    if nd.type != "OUTPUT_MATERIAL":
        nt.nodes.remove(nd)
out_node = nt.nodes["Material Output"]
emi = nt.nodes.new("ShaderNodeEmission")
img_node = nt.nodes.new("ShaderNodeTexImage")
if os.path.exists(tex_path):
    img_node.image = bpy.data.images.load(tex_path)
    img_node.image.colorspace_settings.name = "sRGB"
    nt.links.new(img_node.outputs["Color"], emi.inputs["Color"])
    emi.inputs["Strength"].default_value = 1.75
else:
    emi.inputs["Color"].default_value = (0.1, 0.4, 0.2, 1)
    emi.inputs["Strength"].default_value = 1.0
nt.links.new(emi.outputs["Emission"], out_node.inputs["Surface"])

bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
cz = (kz + KH - RECESS) * MM
center = bm.verts.new((kx * MM, ky * MM, cz))
ring = []
M = 48
for i in range(M):
    a = 2 * math.pi * i / M
    ring.append(bm.verts.new(((kx + R_SCREEN * math.cos(a)) * MM,
                              (ky + R_SCREEN * math.sin(a)) * MM, cz)))
for i in range(M):
    j = (i + 1) % M
    f = bm.faces.new((center, ring[i], ring[j]))
    for loop, vv in zip(f.loops, (center, ring[i], ring[j])):
        px, py = vv.co.x / MM - kx, vv.co.y / MM - ky
        loop[uvl].uv = (px / (2 * R_SCREEN) + 0.5, py / (2 * R_SCREEN) + 0.5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("SCREEN")
bm.to_mesh(me)
bm.free()
# recalc 对开放面片可能给出 -Z；屏幕必须正面朝上，否则贴图会被镜像
if me.polygons and me.polygons[0].normal.z < 0:
    me.flip_normals()
scr = link("SCREEN", me)
me.materials.append(mat_screen)
for p in me.polygons:
    p.use_smooth = True

# ------------------------------------------------------------------ 背部 USB-C 与线
bx = 0.0
by = BOARD_H / 2
port = keycap("USBC_PORT", 9.2, 4.0, 1.2, MAT_LEGEND)
port.location = (bx * MM, (by - 1.0) * MM, (deck_mm(by) - 7.0) * MM)
port.rotation_euler = (0, 0, 0)

cu = bpy.data.curves.new("CABLE", type="CURVE")
cu.dimensions = "3D"
cu.bevel_depth = 1.7 * MM
cu.bevel_resolution = 4
sp = cu.splines.new("BEZIER")
pts_c = [(0.0, by / 2 + 3, deck_mm(by) / 2 + 2),
         (0.0, by + 22, deck_mm(by) / 2 + 1),
         (34.0, by + 52, -6.0),
         (78.0, by + 80, -11.0)]
sp.bezier_points.add(len(pts_c) - 1)
for i, p in enumerate(pts_c):
    sp.bezier_points[i].co = (p[0] * MM, p[1] * MM, p[2] * MM)
    sp.bezier_points[i].handle_left_type = "AUTO"
    sp.bezier_points[i].handle_right_type = "AUTO"
cable = link("CABLE", cu)
cu.materials.append(mat_solid("M_Cable", "#1e2126", 0.62, 0.0))

# ------------------------------------------------------------------ 地面
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.6)
me = bpy.data.meshes.new("GROUND")
bm.to_mesh(me)
bm.free()
ground = link("GROUND", me)
me.materials.append(MAT_GROUND)
ground.location = (0.0, 0.06, -0.0004)

# ------------------------------------------------------------------ 灯光
def add_area(name, loc, target, power, size, color=(1, 1, 1), shape="SQUARE"):
    ld = bpy.data.lights.new(name, type="AREA")
    ld.energy = power
    ld.shape = shape
    ld.size = size
    ld.color = color
    ob = link(name, ld)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


TGT = (0.01, 0.0, 0.02)
add_area("KEY", (-0.42, -0.46, 0.44), TGT, 6.0, 0.75, (1.0, 0.98, 0.95))
add_area("FILL", (0.46, -0.30, 0.24), TGT, 2.0, 0.85, (0.93, 0.96, 1.0))
add_area("RIM", (0.16, 0.52, 0.34), TGT, 4.5, 0.55, (0.88, 0.93, 1.0))
add_area("TOP", (0.0, 0.02, 0.62), TGT, 2.5, 0.9, (1.0, 1.0, 1.0))

# 世界：柔和渐变
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes["Background"]
tc = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
ramp = wn.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.30
ramp.color_ramp.elements[0].color = (0.02, 0.023, 0.028, 1)
ramp.color_ramp.elements[1].position = 0.85
ramp.color_ramp.elements[1].color = (0.16, 0.18, 0.21, 1)
wn.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
wn.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
wn.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.08

# ------------------------------------------------------------------ 相机
cam_data = bpy.data.cameras.new("CAM")
cam_data.lens = 78.0
cam_data.sensor_width = 36.0
cam = link("CAM", cam_data)
scene.camera = cam

direction = Vector((0.62, -0.86, 0.60)).normalized()   # 目标 → 相机


def cam_basis(direction):
    d = Vector(direction).normalized()
    fwd = -d
    up = Vector((0, 0, 1))
    if abs(fwd.dot(up)) > 0.995:
        up = Vector((0, 1, 0))
    Z = -fwd
    Y = (up - Z * up.dot(Z)).normalized()
    X = Y.cross(Z).normalized()
    return d, fwd, X, Y, Z


def scene_bounds():
    xs, ys, zs = [], [], []
    bpy.context.view_layer.update()
    skip = ("GROUND", "CABLE")
    for ob in bpy.data.objects:
        if ob.type not in {"MESH", "CURVE", "FONT"}:
            continue
        if ob.name.startswith(skip):
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


bb = scene_bounds()
_, _, X_, Y_, Z_ = cam_basis(direction)
tan_h = (cam_data.sensor_width / 2.0) / cam_data.lens
tan_v = tan_h * (RES_Y / float(RES_X))
corners = [Vector((x, y, z)) for x in (bb[0], bb[1]) for y in (bb[2], bb[3]) for z in (bb[4], bb[5])]
look = Vector(((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, (bb[4] + bb[5]) / 2))
look.z -= 0.004
dist = max(bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4]) * 2.6 + 0.05
MARGIN = 1.16
for _ in range(60):
    C = look + direction * dist
    k = 0.0
    for P in corners:
        V = P - C
        dep = V.dot(-direction)
        if dep <= 1e-6:
            k = 99
            break
        k = max(k, abs(V.dot(X_) / (dep * tan_h)), abs(V.dot(Y_) / (dep * tan_v)))
    if k >= 99:
        dist *= 1.6
        continue
    dist *= (k / (1.0 / MARGIN)) ** 0.88
    if abs(k * MARGIN - 1.0) < 0.004:
        break
cam.location = look + direction * dist
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()

# 调试：正上方俯视拨盘，用来核对屏幕贴图方向（DIAL_TOP=1）
if os.environ.get("DIAL_TOP") == "1":
    cam_data.lens = 85.0
    cam.location = (kx * MM, ky * MM, (kz + KH + 132.0) * MM)
    cam.rotation_euler = (0.0, 0.0, 0.0)

# 取景自检
bpy.context.view_layer.update()
mw = cam.matrix_world
C = mw.translation
CX_ = mw.col[0].to_3d().normalized()
CY_ = mw.col[1].to_3d().normalized()
CF = -mw.col[2].to_3d().normalized()
worst = 0.0
for ob in bpy.data.objects:
    if ob.type != "MESH" or ob.name == "GROUND":
        continue
    for v in ob.data.vertices:
        V = (ob.matrix_world @ v.co) - C
        dep = V.dot(CF)
        if dep > 1e-5:
            worst = max(worst, abs(V.dot(CX_) / (dep * tan_h)), abs(V.dot(CY_) / (dep * tan_v)))
print("FRAMING worst_ndc=%.3f dist=%.3f" % (worst, dist))

# ------------------------------------------------------------------ 渲染设置
engines = [e.identifier for e in
           bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    if cand in engines:
        scene.render.engine = cand
        break
try:
    scene.eevee.taa_render_samples = SAMPLES
except Exception:
    pass
for attr, val in (("use_raytracing", True), ("use_shadows", True)):
    try:
        setattr(scene.eevee, attr, val)
    except Exception:
        pass
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT
try:
    scene.render.use_persistent_data = True
    assert scene.render.use_persistent_data is True
except Exception as e:
    print("persistent_data skipped:", e)

# 合成：轻微泛光（5.x 合成器走 node_group）
try:
    ng = bpy.data.node_groups.get("Comp") or bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    scene.compositing_node_group = ng
    ng.nodes.clear()
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Fog Glow"
    gl.inputs["Quality"].default_value = "High"
    gl.inputs["Threshold"].default_value = 1.0
    gl.inputs["Size"].default_value = 7.0
    gl.inputs["Strength"].default_value = 0.22
    o = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], o.inputs["Image"])
    scene.render.use_compositing = True
except Exception as e:
    print("compositor skipped:", e)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT, RES_X, RES_Y, "samples", SAMPLES, "worst_ndc", round(worst, 3))
