# -*- coding: utf-8 -*-
"""探针：确认 pcbnew 的 Flip / 旋转 / 焊盘世界坐标语义（写完就删也行）。"""
import sys
import pcbnew

LIB = r'tools\kicad-libs\kicad-footprints-master\Diode_SMD.pretty'
b = pcbnew.NewBoard('numpad/gen/_probe.kicad_pcb')

def dump(tag, fp):
    out = []
    for p in fp.Pads():
        pos = p.GetPosition()
        out.append('%s@(%.2f,%.2f)' % (p.GetNumber(), pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)))
    print('%-22s %s' % (tag, '  '.join(out)))

fp = pcbnew.FootprintLoad(LIB, 'D_SOD-123')
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(50), pcbnew.FromMM(50)))
dump('orig rot0', fp)

fp.SetOrientationDegrees(90)
dump('orig rot90', fp)

fp.SetOrientationDegrees(270)
dump('orig rot270', fp)

fp2 = pcbnew.FootprintLoad(LIB, 'D_SOD-123')
fp2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(50), pcbnew.FromMM(50)))
fp2.Flip(fp2.GetPosition(), False)
dump('flip(no LR) rot0', fp2)

fp2.SetOrientationDegrees(90)
dump('flip rot90', fp2)

fp2.SetOrientationDegrees(270)
dump('flip rot270', fp2)

fp3 = pcbnew.FootprintLoad(LIB, 'D_SOD-123')
fp3.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(50), pcbnew.FromMM(50)))
fp3.Flip(fp3.GetPosition(), True)
dump('flip(LR) rot0', fp3)

print('layers:', [pcbnew.BOARD_GetStandardLayerName(l) for l in (0, 31, 32, 36, 37)])
for l in fp2.Pads()[0].GetLayerSet().Seq():
    print(' pad layer', pcbnew.BOARD_GetStandardLayerName(l))
