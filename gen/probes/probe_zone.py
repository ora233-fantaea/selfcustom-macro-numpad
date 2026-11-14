import sys, os
sys.path.insert(0, r'numpad/gen')
import pcbnew
PCB = r'numpad/kicad/numpad.kicad_pcb'
b = pcbnew.LoadBoard(PCB)
print('nets', [b.GetNetInfo().GetNetItem(i).GetNetname() for i in range(1,4)])
z = pcbnew.ZONE(b)
z.SetLayer(pcbnew.In1_Cu)
z.SetNet(b.FindNet('GND'))
z.SetLocalClearance(pcbnew.FromMM(0.25))
z.SetMinThickness(pcbnew.FromMM(0.2))
z.Outline().NewOutline()
for x,y in [(0,0),(107.25,0),(107.25,134.3),(0,134.3)]:
    z.Outline().Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
print('outline pts', z.Outline().Outline(0).PointCount())
b.Add(z)
print('zone added')
try:
    pcbnew.SaveBoard(r'numpad/kicad/test_zone.kicad_pcb', b)
    print('SaveBoard ok')
except Exception as e:
    print('err', e)
