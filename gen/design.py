# -*- coding: utf-8 -*-
"""numpad 设计的单一真值源（single source of truth）。

原理图（build_sch.py）与 PCB（build_pcb.py）都从本文件读取元件表与网络表，
因此"图"和"板"不可能各说各话。

坐标约定
--------
* 单位 mm，KiCad 坐标系：x 向右、y **向下**。
* 键区（1u = 19.05）的原点在板内 (MX, MY)。
* 键中心 = (MX + (col + w/2) * 19.05, MY + (row + h/2) * 19.05)。
* y 大的一侧 = 前缘（近手侧，低）；y 小的一侧 = 后缘（抬起侧，USB-C 所在）。
"""

PITCH = 19.05

# ---------------------------------------------------------------- 板几何
BOARD_W = 107.25            # = 95.25 + 6.0*2
BOARD_H = 138.30            # = 18.0(后部电子舱) + 114.3(键区) + 6.0
MX = 6.0                    # 键区左边界
MY = 18.0                   # 键区上边界（后缘 18 mm 电子舱）
CORNER_R = 3.0

MOUNT_HOLES = [             # 6 × φ3.4，孔心距板边 3.0
    (3.0, 3.0), (BOARD_W - 3.0, 3.0),
    (3.0, BOARD_H - 3.0), (BOARD_W - 3.0, BOARD_H - 3.0),
    (3.0, MY + 114.3 / 2), (BOARD_W - 3.0, MY + 114.3 / 2),
]

# ---------------------------------------------------------------- 键位
# (名称, col, row, w, h, 矩阵行, 矩阵列)
KEYS = [
    ("circ",   1, 0, 1, 1, 0, 1),
    ("tri",    2, 0, 1, 1, 0, 2),
    ("sq",     3, 0, 1, 1, 0, 3),
    ("crs",    4, 0, 1, 1, 0, 4),

    ("M1",     0, 1, 1, 1, 1, 0),
    ("numclr", 1, 1, 1, 1, 1, 1),
    ("slash",  2, 1, 1, 1, 1, 2),
    ("star",   3, 1, 1, 1, 1, 3),
    ("minus",  4, 1, 1, 1, 1, 4),

    ("M2",     0, 2, 1, 1, 2, 0),
    ("k7",     1, 2, 1, 1, 2, 1),
    ("k8",     2, 2, 1, 1, 2, 2),
    ("k9",     3, 2, 1, 1, 2, 3),
    ("plus",   4, 2, 1, 2, 2, 4),

    ("M3",     0, 3, 1, 1, 3, 0),
    ("k4",     1, 3, 1, 1, 3, 1),
    ("k5",     2, 3, 1, 1, 3, 2),
    ("k6",     3, 3, 1, 1, 3, 3),

    ("M4",     0, 4, 1, 1, 4, 0),
    ("k1",     1, 4, 1, 1, 4, 1),
    ("k2",     2, 4, 1, 1, 4, 2),
    ("k3",     3, 4, 1, 1, 4, 3),
    ("enter",  4, 4, 1, 2, 4, 4),

    ("M5",     0, 5, 1, 1, 5, 0),
    ("k0",     1, 5, 2, 1, 5, 1),
    ("dot",    3, 5, 1, 1, 5, 3),
]

KEY_LABEL = {
    "circ": "F1", "tri": "F2", "sq": "F3", "crs": "F4",
    "numclr": "NUM", "slash": "/", "star": "*", "minus": "-", "plus": "+",
    "M1": "M1", "M2": "M2", "M3": "M3", "M4": "M4", "M5": "M5",
    "enter": "ENTER", "dot": ".", "k0": "0",
    "k1": "1", "k2": "2", "k3": "3", "k4": "4", "k5": "5", "k6": "6",
    "k7": "7", "k8": "8", "k9": "9",
}


def key_center(col, row, w=1, h=1):
    return (MX + (col + w / 2.0) * PITCH, MY + (row + h / 2.0) * PITCH)


KNOB = key_center(0, 0)      # EC11 轴心 (15.525, 23.525)

# ---------------------------------------------------------------- 封装
FP = {
    'mx_hotswap': ('numpad', 'SW_Hotswap_Kailh_MX_1.00u'),
    'stab_2u':    ('numpad', 'SW_Stab_Cherry_MX_2.00u'),
    'mh_m3':      ('numpad', 'MountingHole_3.4mm'),
    'd_sod123':   ('Diode_SMD.pretty', 'D_SOD-123'),
    'r_0402':     ('Resistor_SMD.pretty', 'R_0402_1005Metric'),
    'c_0402':     ('Capacitor_SMD.pretty', 'C_0402_1005Metric'),
    'c_0603':     ('Capacitor_SMD.pretty', 'C_0603_1608Metric'),
    'fuse1206':   ('Fuse.pretty', 'Fuse_1206_3216Metric'),
    'qfn56':      ('Package_DFN_QFN.pretty', 'QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm'),
    'soic8':      ('Package_SO.pretty', 'SOIC-8_3.9x4.9mm_P1.27mm'),
    'sot23_5':    ('Package_TO_SOT_SMD.pretty', 'SOT-23-5'),
    'sot23_6':    ('Package_TO_SOT_SMD.pretty', 'SOT-23-6'),
    'crystal':    ('Crystal.pretty', 'Crystal_SMD_3225-4Pin_3.2x2.5mm'),
    'usbc16':     ('Connector_USB.pretty', 'USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A'),
    'ec11':       ('Rotary_Encoder.pretty', 'RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm'),
    'sw_push':    ('Button_Switch_SMD.pretty', 'Panasonic_EVQPUJ_EVQPUA'),
    'tp':         ('TestPoint.pretty', 'TestPoint_Pad_1.5x1.5mm'),
}

EC11_SHAFT = (7.5, 2.5)     # 轴心相对封装原点

# 不翻转的封装（热插拔座/稳定器自带 B 面焊盘；轴/编码器/连接器在正面）
NO_FLIP = {'mx_hotswap', 'stab_2u', 'mh_m3', 'ec11', 'usbc16'}

# ---------------------------------------------------------------- 网络名
N_3V3 = '3V3'
N_5V = '5V'
N_GND = 'GND'
N_1V1 = 'VREG_1V1'
N_VBUS = 'VBUS'

# ---------------------------------------------------------------- 元件表
COMPS = []


def add(ref, value, fp, at, rot=0, side='B', **kw):
    c = dict(ref=ref, value=value, fp=fp, at=at, rot=rot, side=side)
    c['flip'] = (side == 'B') and (fp not in NO_FLIP)
    c.update(kw)
    COMPS.append(c)
    return c


# ---- 26 颗轴 + 26 个二极管 -------------------------------------------------
SW_REF = {}
DIODE_REF = {}
for i, (name, col, row, w, h, r, cc) in enumerate(KEYS):
    cx, cy = key_center(col, row, w, h)
    sref = 'SW%d' % (i + 1)
    dref = 'D%d' % (i + 1)
    SW_REF[name] = sref
    DIODE_REF[name] = dref
    add(sref, 'MX', 'mx_hotswap', (cx, cy), 0, 'B',
        nets={'1': 'K_%s_A' % sref, '2': 'COL%d' % cc}, key=name, kx=cx, ky=cy)
    add(dref, '1N4148W', 'd_sod123', (cx - 7.50, cy + 5.60), 90, 'B',
        nets={'1': 'ROW%d' % r, '2': 'K_%s_A' % sref}, key=name)

# ---- 稳定器（0 键 2u）-----------------------------------------------------
_kx0, _ky0 = key_center(1, 5, 2, 1)
add('STB1', 'Stab_2u', 'stab_2u', (_kx0, _ky0), 0, 'B', nets={})

# ---- 旋钮 EC11 + 它的矩阵二极管 -------------------------------------------
add('ENC1', 'EC11E', 'ec11', (KNOB[0] - EC11_SHAFT[0], KNOB[1] - EC11_SHAFT[1]), 0, 'F',
    nets={'A': 'ENC_A', 'B': 'ENC_B', 'C': N_GND,
          'S1': 'K_ENC1_A', 'S2': 'COL0', 'MP': N_GND})
add('D27', '1N4148W', 'd_sod123', (21.0, 13.20), 90, 'B',
    nets={'1': 'ROW0', '2': 'K_ENC1_A'}, key='knob')

# ---- USB-C ---------------------------------------------------------------
USB_C_X = BOARD_W / 2.0
add('J1', 'USB_C_16P', 'usbc16', (USB_C_X, 5.22), 0, 'F',
    nets={'A4': N_VBUS, 'A9': N_VBUS, 'B4': N_VBUS, 'B9': N_VBUS,
          'A1': N_GND, 'A12': N_GND, 'B1': N_GND, 'B12': N_GND,
          'A5': 'CC1', 'B5': 'CC2',
          'A6': 'USB_DP_CON', 'B6': 'USB_DP_CON',
          'A7': 'USB_DM_CON', 'B7': 'USB_DM_CON',
          'A8': 'NC', 'B8': 'NC',
          'SH': N_GND})

# ---- RP2040 引脚映射 -----------------------------------------------------
# 引脚号 != GPIO 号，别混。QFN-56（封装 0°）：1-14 左边、15-28 下边、29-42 右边、43-56 上边。
# 板上把 U1 转 90°：1-14 朝南（对着键区）、15-28 朝东、29-42 朝北、43-56 朝西（对着 USB-C）。
GPIO_PIN = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8, 7: 9,
            8: 11, 9: 12, 10: 13, 11: 14, 12: 15, 13: 16, 14: 17, 15: 18,
            16: 27, 17: 28, 18: 29, 19: 30, 20: 31, 21: 32, 22: 34,
            23: 35, 24: 36, 25: 37, 26: 38, 27: 39, 28: 40, 29: 41}

RP_NETS = {
    # 电源 / 地
    '1': N_3V3, '10': N_3V3, '22': N_3V3, '33': N_3V3, '42': N_3V3, '49': N_3V3,
    '23': N_1V1, '50': N_1V1,      # DVDD <- 内部 LDO 输出
    '44': N_3V3,                   # VREG_VIN
    '45': N_1V1,                   # VREG_VOUT
    '43': N_3V3,                   # ADC_AVDD
    '48': N_3V3,                   # USB_VDD
    '19': N_GND,                   # TESTEN 必须接地
    '57': N_GND,                   # 裸露焊盘
    # 时钟
    '20': 'XIN', '21': 'XOUT_C',
    # SWCLK/SWDIO/RUN 本版不引出（只靠 USB 引导烧录），悬空；RP2040 内部对
    # SWDIO 有下拉、RUN 有上拉，悬空不影响上电启动。
    # USB / QSPI
    '46': 'USB_DM', '47': 'USB_DP',
    '51': 'QSPI_SD3', '52': 'QSPI_SCLK', '53': 'QSPI_SD0',
    '54': 'QSPI_SD2', '55': 'QSPI_SD1', '56': 'QSPI_SS',
}
# 矩阵：行 GP2..GP7（南边）、列 GP8..GP10（南边）+ GP16/GP17（东边）
_ROW_GPIO = [2, 3, 4, 5, 6, 7]
_COL_GPIO = [8, 9, 10, 16, 17]
for _i, _g in enumerate(_ROW_GPIO):
    RP_NETS[str(GPIO_PIN[_g])] = 'ROW%d' % _i
for _i, _g in enumerate(_COL_GPIO):
    RP_NETS[str(GPIO_PIN[_g])] = 'COL%d' % _i
RP_NETS[str(GPIO_PIN[12])] = 'ENC_A'                   # GP12 -> pin15（西侧，直接出线）
RP_NETS[str(GPIO_PIN[13])] = 'ENC_B'                   # GP13 -> pin16
# GP18/GP19/GP20（RGB、I2C）本版不引出背光/OLED，留悬空，不放网络标签，
# 否则每个都是一根只有一头的小网络，原理图 ERC 和 PCB 都会当成断线。

# ---- MCU 区（板底，后缘电子舱）-------------------------------------------
# U1 转 90° 后实测：1-14 在南（朝键区）、15-28 在西、29-42 在北、43-56 在东。
add('U1', 'RP2040', 'qfn56', (67.0, 9.0), 90, 'B', nets=dict(RP_NETS))

# QSPI Flash 在 QFN 东侧（转 90°，1-4 在南、5-8 在北）
add('U2', 'W25Q32JVSS', 'soic8', (84.0, 9.0), 90, 'B', nets={
    '1': 'QSPI_SS', '2': 'QSPI_SD0', '3': 'QSPI_SD1', '4': N_GND,
    '5': 'QSPI_SD2', '6': 'QSPI_SCLK', '7': 'QSPI_SD3', '8': N_3V3})

# 12 MHz 晶振在 QFN 西侧（XIN=20 / XOUT=21 在西边）
add('Y1', '12MHz', 'crystal', (55.0, 11.5), 180, 'B', nets={
    '1': 'XIN', '2': N_GND, '3': 'XOUT', '4': N_GND})

# ---- 电源（板面：USB-C 西侧）---------------------------------------------
add('J2', 'FUSE_1.1A', 'fuse1206', (36.0, 11.4), 0, 'F', nets={'1': N_VBUS, '2': N_5V})
add('U3', 'ME6211C33M5', 'sot23_5', (36.0, 8.0), 0, 'F', nets={
    '1': N_5V, '2': N_GND, '3': N_5V, '4': 'NC', '5': N_3V3})

# ---- USB ESD + 串阻 + CC 下拉 --------------------------------------------
add('U4', 'USBLC6-2SC6', 'sot23_6', (61.2, 3.6), 0, 'F', nets={
    '1': 'USB_DP_CON', '2': N_GND, '3': 'USB_DM_CON',
    '4': 'USB_DM_CON', '5': N_VBUS, '6': 'USB_DP_CON'})

# ---- 按键 / 调试 ---------------------------------------------------------
# 官方参考：QSPI_SS -> 1k -> 按键 -> GND（1k 必须有）。
# BOOTSEL 用焊盘短接（TP4/TP5）代替实体按键：QMK 里双击 RESET 就能进 BOOT，
# 实体键只在救砖时用，省下按键高度和姿态冲突。
add('TP4', 'BOOT', 'tp', (86.5, 14.4), 0, 'B', nets={'1': 'BOOT_N'})
add('TP5', 'GND', 'tp', (89.5, 14.4), 0, 'B', nets={'1': N_GND})
# ---- 阻容 ---------------------------------------------------------------
PASSIVES = [
    # --- 板面：USB 前端 / 电源链（USB-C 西侧）---
    ('C1',  '22uF',  'c_0603', (31.0, 8.6),  0,  'F', {'1': N_5V, '2': N_GND}),
    ('C2',  '10uF',  'c_0603', (41.0, 11.4), 0,  'F', {'1': N_3V3, '2': N_GND}),
    ('R3',  '5k1',   'r_0402', (46.4, 4.8),  90, 'F', {'1': 'CC1', '2': N_GND}),
    ('R4',  '5k1',   'r_0402', (46.4, 7.6),  90, 'F', {'1': 'CC2', '2': N_GND}),
    ('R6',  '27',    'r_0402', (67.0, 4.7),  0,  'F', {'1': 'USB_DM_CON', '2': 'USB_DM'}),
    ('R5',  '27',    'r_0402', (67.0, 2.5),  0,  'F', {'1': 'USB_DP_CON', '2': 'USB_DP'}),

    # --- 板面：MCU 去耦（贴在 QFN 附近，过孔下到 B 面焊盘）---
    ('C11', '100nF', 'c_0402', (63.0, 1.3),  0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C12', '100nF', 'c_0402', (70.6, 1.3),  0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C3',  '100nF', 'c_0402', (59.4, 16.6), 0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C5',  '100nF', 'c_0402', (74.6, 15.4), 0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C4',  '100nF', 'c_0402', (79.0, 4.4),  0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C7',  '100nF', 'c_0402', (76.5, 4.4),  0,  'F', {'1': N_1V1, '2': N_GND}),
    ('C8',  '100nF', 'c_0402', (61.9, 14.6), 0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C13', '1uF',   'c_0402', (61.9, 15.8), 0,  'F', {'1': N_1V1, '2': N_GND}),
    ('C6',  '100nF', 'c_0402', (81.5, 4.4),  0,  'F', {'1': N_3V3, '2': N_GND}),
    ('C14', '100nF', 'c_0402', (74.0, 4.4),  0,  'F', {'1': N_1V1, '2': N_GND}),

    # --- 板底：晶振网络（晶振在 (55,11.5)，R1 在其西侧，C9/C10 就近）---
    ('R1',  '1k',    'r_0402', (50.5, 12.35), 0, 'B', {'1': 'XOUT', '2': 'XOUT_C'}),
    ('C9',  '15pF',  'c_0402', (58.4, 10.4), 0,  'B', {'1': 'XIN', '2': N_GND}),
    ('C10', '15pF',  'c_0402', (49.0, 14.0), 90, 'B', {'1': 'XOUT', '2': N_GND}),

    # --- 板底：BOOTSEL 短接焊盘（TP4=BOOT_N，TP5=GND，镊子短接上电即进 BOOT）
    # 官方要求 QSPI_SS 经 1k 再下地，不能直连，否则正常启动时 CS 被拉死。
    ('R7',  '1k',    'r_0402', (89.0, 11.8), 0,  'B', {'1': 'QSPI_SS', '2': 'BOOT_N'}),

    # QSPI_SS 上拉（官方标 DNF；保留焊盘，装 10k 亦无害）
    ('R2',  '10k',   'r_0402', (78.6, 17.4), 0,  'B', {'1': N_3V3, '2': 'QSPI_SS'}),
]
for _ref, _val, _fp, _at, _rot, _side, _nets in PASSIVES:
    add(_ref, _val, _fp, _at, _rot, _side, nets=_nets)


# ---------------------------------------------------------------- 网络统计
def net_table():
    """返回 {net: [(ref, pad), ...]}"""
    tbl = {}
    for c in COMPS:
        for pad, net in c.get('nets', {}).items():
            if not net or net == 'NC':
                continue
            tbl.setdefault(net, []).append((c['ref'], pad))
    return tbl


def comp(ref):
    for c in COMPS:
        if c['ref'] == ref:
            return c
    raise KeyError(ref)


if __name__ == '__main__':
    tbl = net_table()
    print('元件 %d 个，网络 %d 个' % (len(COMPS), len(tbl)))
    for net in sorted(tbl):
        pts = ', '.join('%s.%s' % p for p in tbl[net])
        print('%-12s %s' % (net, pts))
