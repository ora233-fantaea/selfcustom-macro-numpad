# M5Dial (K130 / K130-V11) 尺寸实测与来源备注

生成时间：2026-11-15 · 用于自制小键盘壳体嵌入设计

## 1. 官方机械图（docs 页面“尺寸图”）读数

来源图：https://static-cdn.m5stack.com/resource/docs/products/core/M5Dial/img-4739e0cc-227a-4f6b-9956-48915212e9c8.png
（K130 与 K130-V11 两个 docs 页面引用的是同一张图）

| 标注 | 含义（按图纸几何位置读取） |
|---|---|
| Ø51 | 最大外径（旋钮滚花外圈） |
| Suggested hole dimension Ø45 ± 0.2 | 官方建议面板开孔直径 |
| 32.3 | 总高（含背面凸出物） |
| 28.8 | 前面 → 背面平面 |
| 14.6 | 前面 → 前段台阶 |
| 5 | 中部滚花环宽度 |
| 0 ~ 6 mm | 位于背面一侧的间隙（卡扣/夹持行程） |
| 24 | 背面 StampS3 模块宽度（模块实测 24.0 × 18.0 × 4.7 mm） |

## 2. 官方结构文件实测（Dial.stl, m5stack/M5_Hardware/Products/K130_Dial/Structures）

STL 为多零件平铺网格（17 个 shell），坐标轴：Z = 轴向，+Z = 背面（StampS3 一侧）。
整体包围盒：Ø50.82 × 高 30.32 mm（比官方 32.3 少约 2 mm，STL 为外观简化件）。

| 部位 | 外径 | Z 范围 (mm) | 备注 |
|---|---|---|---|
| 前部环（屏幕外圈） | 45.03 | -17.32 … -11.22 | 内孔 Ø34.10（显示开口） |
| 前段旋钮圈 | 49.99 | -16.87 … -4.30 | 光面 |
| 中部滚花环 | 50.98 (=Ø51) | -0.90 … 4.10 | 宽 5.0 |
| 后段主体 | 48.00 | -5.00 … 11.70 | |
| 内部机架 | 44.20 | -15.47 … 1.00 | |
| RFID 天线环 | 36.67 | 6.80 … 11.50 | |
| 背面 StampS3 支架环 | 37.12 | 10.60 … 13.00 | 内孔 Ø16.2 |
| StampS3 模块 | 24 × 18 × 4.7 | 6.80 … 11.50 | 与官方模块规格一致 |

USB-C：模块板边连接器，口部位置约 r ≈ 18–22 mm（距轴心），位于背面边缘、与 DC 端子成 180°。

## 3. 电流（官方）

| 项目 | 数值 | 来源 |
|---|---|---|
| K130-V11 USB 5V 工作 | 88.19 mA | shop 规格表 |
| K130-V11 USB 5V 休眠 | 6.84 mA | shop 规格表 |
| K130-V11 电池 4V 工作 | 100 mA | shop 规格表 |
| K130 背部端子 6 / 12 / 36 V | 140.6 / 82.5 / 28.1 mA | docs 规格表 |
| K130 电池休眠 | 4.2V @ 1.9 µA | docs 规格表 |
| Wi-Fi 发射峰值 | 官方未公布 | — |

## 4. 硬件要点（原理图）

- Sch_M5Dial（https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/499/Sch_M5Dial.pdf）
  - U2 = TP4057 单节锂电线性充电；U6 = CN809 复位；Q2/Q3 = LP3218DT1G 负载开关
  - U7 = ME3116AM6G（6–36V → 5V）；U3 = SY7088（升压 → +5VOUT）；U4 = SY8089（buck → 3.3V）
  - M1 = STAMP-S3-DIP-1.27 插座（模块可换）
  - J3 = PORT.A（IIC_SCL/IIC_SDA，+5VOUT，GND）；J2 = PORT.B（GI/GO，+5VOUT，GND）
  - 板上无 USB 座、无 USB-Serial 芯片 → USB-C 完全在 StampS3 模块上
- Sch_M5StampS3_v0.2（https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/522/Sch_M5StampS3_v0.2.pdf）
  - J2 USB-C：CC1/CC2 各 5.1 kΩ 下拉（R1/R2）→ 标准 UFP；VIN_5V 经 F1 6V/1A PPTC
  - D+/D- = GPIO20 / GPIO19，直连 ESP32-S3 原生 USB
