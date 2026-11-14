# numpad 原理图 / PCB 现状

> 单一真值源：`gen/design.py`（元件表 + 网表 + 键位坐标）。原理图和 PCB 都由脚本从
> 同一份 `net_table()` 生成，所以「图」和「板」不可能各说各话。改设计只改 design.py，
> 然后重跑下面四条命令，不手改 KiCad 文件。

```powershell
python gen/sch.py                    # 原理图（A0，全部网络标签连线）
kicad-cli sch erc -o kicad/erc.rpt kicad/numpad.kicad_sch
python gen/build_pcb.py --place      # 板框 + 91 个封装 + 叠放自检（必须只跑一次）
python gen/freeroute.py --export     # 导 DSN（含 0.15/0.15 规则）
java -jar tools/freerouting/freerouting-1.9.0.jar -de kicad/numpad.dsn `
     -do kicad/numpad.ses -mp 30 -mt 1     # 自动布线（约 2 分半）
python gen/freeroute.py --import     # 回灌 SES + 收口成 2 层 + 双面 GND 覆铜
kicad-cli pcb drc --severity-all kicad/numpad.kicad_pcb   # 期望 0 违规 0 未连接
kicad-cli pcb export gerbers --output kicad/gerber kicad/numpad.kicad_pcb
python gen/render.py                 # 出 PNG
```

## 1. 原理图（已完成）

| 项 | 值 |
| --- | --- |
| 文件 | `kicad/numpad.kicad_sch`（A0）、`kicad/numpad_sch.pdf`、`svg_sch/numpad.svg` |
| ERC | **0 违规** |
| 网表一致性 | 从原理图导出网表与 `design.py` 的 61 个网络**逐一比对，61/61 完全相同** |
| 元件 | 85 个（26 热插拔轴 + 27 二极管 + RP2040 + W25Q32 + 晶振 + LDO + USBLC6 + USB-C + EC11 + 阻容） |

生成方式：**连线全部用网络标签**。每个引脚拉 2.54 mm 短引线接一个同名标签，连通性靠
标签名成立，因此不会有「图画错了但网络对」或反过来的情况——图就是网表的可视化。
四个分区：左上 USB/ESD/保险丝、左下 电源、右上 矩阵、右下 主控/晶振/QSPI。

已知取舍：

- **EC11 的 MP 安装脚没有画**。`Device:RotaryEncoder_Switch` 只有 A/B/C/S1/S2 五个引脚，
  而封装有 MP 焊盘（接 GND）。封装里 MP 直接连 GND 平面，原理图这一步省掉。
- **USBLC6-2SC6 用的是自制符号**（`kicad/numpad_lib.kicad_sym`）。库里的同名符号是
  `(extends "USBLC6-2P6")` 的派生符号，嵌进 `lib_symbols` 后 KiCad 报 `lib_symbol_mismatch`
  且引脚位置对不上，所以画了一个 6 脚黑盒，脚序与 SOT-23-6 封装一一对应。
- 图形是机器摆的，能看能查，不是手绘那种美观度。

## 2. 板子规格

| 项 | 值 |
| --- | --- |
| 外形 | 107.25 × **138.30** mm，R3 圆角（后缘 **18 mm** 电子舱 + 键区 114.3 + 前缘 6） |
| 叠层 | **2 层**：F.Cu（信号 + GND 覆铜）/ B.Cu（全部焊盘 + 信号 + GND 覆铜）。见 §3 的取舍说明 |
| 键区 | 6 行 × 5 列，19.05 mm 间距，26 键 + 左上 EC11 旋钮 |
| 轴 | Kailh 热插拔座（B 面），1N4148W 贴在轴下方偏西 |
| 主控 | RP2040 QFN-56 @(67, 9) 转 90°，W25Q32 @(84, 9)，3225 晶振 @(55, 11.5) |
| 供电 | USB-C 16P → F2 保险丝 → ME6211 → 3.3 V；USBLC6 做 ESD |
| 安装 | **6 个 φ3.4 安装孔**（四角 + 左右腰中各一，孔心距板边 3.0） |
| 烧录 | TP4(BOOT_N)/TP5(GND) 短接焊盘经 R7 1 k 接 QSPI_SS（见 §4） |

## 3. 层间分工（为什么最后是 2 层）

| 层 | 内容 |
| --- | --- |
| F.Cu | 207 段信号 + **GND 覆铜**（离板边 0.4，孤岛自动移除） |
| B.Cu | 全部 405 个焊盘 + 406 段信号 + **GND 覆铜** |
| Edge.Cuts | 圆角板框 |

中间过程是 6 层（F / In1 GND 平面 / In2 3V3 平面 / In3 / In4 / B），手工布线时需要
内层当躲线空间。**改用 FreeRouting 之后它把 613 段全走在 F.Cu 和 B.Cu 上，内层四层一段没
用**——继续保留的话，那两块平面既没有过孔和任何焊盘相连，是孤立铜皮（DRC 的
`isolated_copper`），等于花 6 层的钱做 2 层的板。

所以收口成 2 层：GND 靠双面覆铜 + 走线，3V3 靠走线（电流只有几十 mA）。代价是
USB 差分对底下没有专门的地平面，但它只有十几毫米长、全速 12 Mbps，铺铜已经够了；
换来的是打样价格从 6 层的四五百块降到几十块。要更稳的话，把叠层改回 4 层
（F/B + In1 GND + In2 3V3）再补缝合过孔即可，走线不用重做。

## 4. 这一版改了什么

- ~~**四层改六层**~~（后来改回 2 层，见 §3）：当时是为了把 In2 让出来做 3.3 V 平面。
- **USB 前端重排**：USB-C 的 4 个信号脚用交错过孔换位，USBLC6 移到连接器东侧，
  27 Ω 紧跟 ESD，CC 下拉直接吊在 CC 焊盘下方；连接器内缩 0.75 mm 消掉板边间距违规。
- **恢复 BOOTSEL 通路（重要）**：上一轮把实体键、R7 一起删掉后，QSPI_SS 上再没有任何
  下地路径，**板子实际上无法进 BOOT**（也没有 SWD 焊盘，等于救不回来）。现在补回
  R7=1 k（QSPI_SS → BOOT_N）+ TP4/TP5 短接焊盘：上电前用镊子短接即进 BOOTSEL。
  1 k 不能省，直连会在正常启动时把 CS 拉死。
- **清掉 6 根单端网络**（SWCLK/SWDIO/RUN/RGB/I2C_SDA/I2C_SCL）。这些是删器件后留下的
  只有一头的网络，原理图 ERC 会报「标签只连了一个引脚」，PCB 上是断头线。GP18–GP20
  直接悬空（RP2040 内部有上下拉，不影响启动）。
- **晶振符号换成 4 脚** `Device:Crystal_GND24`：3225 封装是 1=XIN、2=GND、3=XOUT、4=GND，
  两脚符号会让两个 GND 焊盘在原理图上消失。
- **电子舱 14 → 18 mm（板高 134.3 → 138.3）**：主控南侧原来只剩 1.5 mm 给 9 根矩阵线扇出
  （6 行 + 3 列，焊盘 0.4 mm 间距、过孔 0.45 mm 排不下）。加长后南侧有 5.5 mm，扇出深度从
  1.0/1.55/2.1 改到 1.3/2.4/3.5，行车道整体南移到 y=17.2~20.0。C3/C5（3V3 去耦）与 R2
  （QSPI_SS 上拉）原来压在扇出带里，已挪到 x=59.4 / 74.6 / 78.6。
- **改走 FreeRouting，从 205 条电气 error 直接到 0**：手工布线在电子舱那一小片
  （约 25×12 mm，QFN 四面扇出 + 晶振 + flash + USB 抢同一条走廊）已经卡死，
  交给自己布线器后一次跑通。
- **叠层 6 层 → 2 层**：freerouting 一段都没用内层，留着就是孤立铜皮（见 §3）。
- **丝印清理方式改了**：位号/值全部隐藏（正面被轴体和热插拔座占满），二极管/阻容的丝印线
  从丝印层挪到 Fab 层，键位名字直接不画（装键帽后看不见）。
- **规则按嘉立创能力放开**：`numpad.kicad_dru` 里 `clr_0.15`、`hole_clr_0.15`、
  `edge_clr_0.2`、`via_0.45`、`track_0.15`。其中 hole_clearance 是 USB-C 16P 公版封装
  固有的（A1/A12 焊盘离外壳孔 0.1847），不是布线问题。

## 5. 布线结果（已完成，可下单）

`kicad-cli pcb drc --severity-all`：**0 条违规、0 条未连接**（连外观类警告也是 0）。

| 项 | 值 |
| --- | --- |
| 走线 | 613 段，线宽全 0.15 mm（F.Cu 207 / B.Cu 406） |
| 过孔 | 37 个，0.45 / 0.25 |
| 未连接 | **0**（61 个网络全部布通） |
| 覆铜 | F.Cu / B.Cu 两块 GND，已填充 |
| 电源 | F2 保险丝 → ME6211 → 3V3 全部布通；USB-C 4 个信号脚经 USBLC6 到 RP2040 |
| 生产资料 | `kicad/gerber/` 27 个文件（F_Cu / B_Cu / 两面膜 / 两面粉丝印 / Edge_Cuts / PTH+NPTH 钻孔） |
| 图 | `kicad/img/top.png`、`bottom.png`、`stack.png` |
| 备份 | `numpad_mt8_9err.kicad_pcb`（多线程版，电气 9 条，留作对比） |

布线由 **FreeRouting 1.9.0** 完成（自动布线 5.8 秒 + 优化约 2 分 17 秒），参数是
`-mt 1`（单线程优化；多线程会自己警告会产出间距违规）。回灌后用
`gen/freeroute.py --import` 收口：改 2 层、补双面 GND 覆铜、填铜、存盘。

## 6. 工具链坑（踩过的，别再踩）

- `kicad_dru` 文件**不能带 BOM**，PowerShell 的 `Set-Content -Encoding UTF8` 会写 BOM，
  导致整份自定义规则被静默忽略（表现为所有过孔突然报 `via_diameter`）。
- 改源码只能用编辑器工具，`Set-Content` 会把 UTF-8 写坏。
- `board.Save()` 在含覆铜的板上会崩，用 `pcbnew.SaveBoard(path, board)`。
- `LSET` 不能用 `pcbnew.LSET(layer)` 构造，要 `ls = pcbnew.LSET(); ls.AddLayer(layer)`。
- 自制封装写 `(fill (none))` 会让该 footprint 之后的所有 pad 静默丢弃，必须 `(fill no)`。
- 渲染时 pcbnew 的 assert 会把 PowerShell 管道堵死，要 `2>$null`。
- **`route.py` 只能跑一次**。跑第二遍会在已布线的板上再叠一层（走线 289→578、过孔 127→254），
  DRC 直接爆到 792 条。正确顺序是 `build_pcb.py --place` → `route.py` 各一次。
  （现在 `route.py` 已被 FreeRouting 流水线取代，只在归档里。）
- 原理图引脚连接点 = 符号坐标 (x, −y) 加实例偏移；符号原点必须落在 **1.27 栅格**上，
  否则 ERC 报一屏 `endpoint_off_grid`（0.635 栅格不够）。
- **车道表是硬编码绝对坐标**（ly = 13.00 + 0.45*(2-i) 之类）。改板框或挪主控之后必须
  同步改这些常量，否则会出现「加长了但 DRC 只从 224 降到 222」——第一次加长就踩了这个坑。
- 原理图工程要有 `sym-lib-table` / `fp-lib-table`，且 portable 版 KiCad 不认
  `${KICAD10_SYMBOL_DIR}`，必须写绝对路径，否则每个符号都报 `lib_symbol_issues`。
- **`fp.Remove(g)` 会让这个封装后续的 SWIG 取值器全部失效**：之后 `GraphicalItems()`
  返回不可迭代的裸 `SwigPyObject`，`GetPosition()`/`GetBoundingBox()` 返回的裸指针连
  `.x`/`.GetLeft()` 都没有。表现是一串 `TypeError: 'SwigPyObject' object is not iterable`
  和 `AttributeError`。要改封装内容就**换层（SetLayer）别删**。
- **同一个封装上，`GraphicalItems()` 之前不要先调 `GetReference()`/`GetPadCount()`**，
  也会触发上面那个裸对象问题。需要位号/焊盘数就在建件时就记下来，别回头查。
- **`fp.GetFPID()` 常常直接返回裸 `SwigPyObject`**，`GetLibItemName()` 不存在；判断
  自制封装别靠它。
- `PCB_VIA.GetWidth()` 不带层参数会弹 wxWidgets Debug Alert（KiCad 10 的 assert），
  必须 `GetWidth(pcbnew.F_Cu)`。
- **FreeRouting 2.5.0 的 GUI 读不了 KiCad 10 导出的 DSN**：弹
  「91 session item(s) were skipped due to unresolved reference, layer, or padstack」，
  把全部 91 个元件跳过。同一份 DSN 用 **1.9.0 的 CLI 完全正常**，所以流水线走命令行，
  不需要开 GUI。
- **SES 回灌前必须是一块完整的板子**：`build_pcb` 崩过一次、board 被写成空板，回灌后得到
  613 条无网络走线 + 178 条 `track_dangling` + `invalid_outline`，DRC 还会假报
  「电气 0」。`freeroute.py --import` 现在会检查封装数 < 50 就拒绝回灌。
