"""Original diagnostic fixture, GPL-3.0-or-later. Run with KiCad bundled Python.
Not a representative benchmark family or held-out evaluation.
"""
from pathlib import Path
import json
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'fixtures/smoke'
out.mkdir(parents=True,exist_ok=True)
b=p.BOARD()
def xy(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
nets={}
for name in ['SIGNAL_A','SIGNAL_B','GND']:
    n=p.NETINFO_ITEM(b,name); b.Add(n); nets[name]=n
for i,(x,y,net) in enumerate([(10,10,'SIGNAL_A'),(40,10,'SIGNAL_A'),(10,20,'SIGNAL_B'),(40,20,'SIGNAL_B'),(10,30,'GND'),(40,30,'GND')]):
    fp=p.FOOTPRINT(b); fp.SetFPID(p.LIB_ID('', 'diagnostic_terminal')); fp.SetReference('J'+str(i+1)); fp.SetValue('diagnostic_terminal'); fp.SetPosition(xy(x,y))
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    pad=p.PAD(fp); pad.SetNumber('1'); pad.SetPosition(xy(x,y)); pad.SetSize(xy(2,2)); pad.SetDrillSize(xy(0.8,0.8)); pad.SetShape(p.PAD_SHAPE_CIRCLE); pad.SetAttribute(p.PAD_ATTRIB_PTH); pad.SetLayerSet(p.LSET.AllCuMask()); pad.SetNet(nets[net]); fp.Add(pad); b.Add(fp)
for a,z in [((5,5),(45,5)),((45,5),(45,35)),((45,35),(5,35)),((5,35),(5,5))]:
    s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_SEGMENT); s.SetStart(xy(*a)); s.SetEnd(xy(*z)); s.SetLayer(p.Edge_Cuts); s.SetWidth(p.FromMM(0.05)); b.Add(s)
zone=p.ZONE(b); zone.SetLayer(p.B_Cu); zone.SetNet(nets['GND']); zone.SetLocalClearance(p.FromMM(0.3)); zone.SetThermalReliefGap(p.FromMM(.3)); zone.SetThermalReliefSpokeWidth(p.FromMM(.3)); zone.SetPadConnection(p.ZONE_CONNECTION_FULL)
poly=zone.Outline(); poly.NewOutline()
for x,y in [(6,6),(44,6),(44,34),(6,34)]: poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(zone)
p.SaveBoard(str(out/'smoke.kicad_pcb'),b)
(out/'smoke.kicad_pro').write_text(json.dumps({'meta':{'filename':'smoke.kicad_pro','version':1}},indent=2)+'\n')
print(out/'smoke.kicad_pcb')
