import sys, os, time
sys.path.insert(0, r'numpad/gen')
t0=time.time()
import pcbnew
print('import %.1fs' % (time.time()-t0)); sys.stdout.flush()
b = pcbnew.LoadBoard(r'numpad/kicad/numpad.kicad_pcb')
print('load %.1fs tracks=%d fps=%d' % (time.time()-t0, len(b.GetTracks()), len(list(b.GetFootprints())))); sys.stdout.flush()
import render as R
print('render import %.1fs' % (time.time()-t0)); sys.stdout.flush()
bbx = b.GetBoardEdgesBoundingBox()
print('bbox %.1fs' % (time.time()-t0)); sys.stdout.flush()
cv = R.Canvas(pcbnew.ToMM(bbx.GetWidth()), pcbnew.ToMM(bbx.GetHeight()), 3.0)
print('canvas %.1fs' % (time.time()-t0)); sys.stdout.flush()
n=0
for fp in b.GetFootprints():
    for it in fp.GraphicalItems():
        R.shape_points(it); n+=1
print('graphics %d %.1fs' % (n, time.time()-t0)); sys.stdout.flush()
