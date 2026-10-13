"""Original project-owned KiCad8 grammar; not a relabelled modern board."""
import copy,json,uuid
from autorouter import sexpr as sx,pipeline as p
CASES=('positive','missing_track','narrow_track')
NS=uuid.UUID('e4c17396-9212-4bb9-a2b4-efb53b8c88a9')
def uid(label):return str(uuid.uuid5(NS,label))
TRACK=uid('signal-track');PADS=[uid('pad-'+str(i)) for i in range(4)]

def board(case):
    if case not in CASES:raise p.Rejected('unknown compatibility fixture')
    # KiCad8 numeric net declarations, old numeric layer indices, modern UUID
    # identity and property references are authored explicitly from scratch.
    tree=sx.parse('''(kicad_pcb (version 20240108) (generator "pcbnew") (generator_version "8.0") (general (thickness 1.6)) (paper "A4")
      (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (35 "F.Paste" user) (34 "B.Paste" user) (37 "F.SilkS" user) (36 "B.SilkS" user) (39 "F.Mask" user) (38 "B.Mask" user) (44 "Edge.Cuts" user) (49 "F.Fab" user) (48 "B.Fab" user))
      (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no)) (net 0 "") (net 1 "SIGNAL") (net 2 "GND"))''')
    for i,(x,y,net,name) in enumerate(((10,10,1,'SIGNAL'),(20,10,1,'SIGNAL'),(10,16,2,'GND'),(20,16,2,'GND'))):
        tree.append(sx.parse('(footprint "owned_compat_terminal" (layer "F.Cu") (uuid "'+uid('fp-'+str(i))+'") (at '+str(x)+' '+str(y)+') '
            '(property "Reference" "J'+str(i+1)+'" (at 0 0 0) (layer "F.SilkS") (hide yes) (uuid "'+uid('reference-'+str(i))+'") (effects (font (size 1 1) (thickness 0.15)))) '
            '(property "Value" "owned_compat_terminal" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "'+uid('value-'+str(i))+'") (effects (font (size 1 1) (thickness 0.15)))) '
            '(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "'+uid('datasheet-'+str(i))+'") (effects (font (size 1 1) (thickness 0.15)))) '
            '(property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "'+uid('description-'+str(i))+'") (effects (font (size 1 1) (thickness 0.15)))) '
            '(pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 0.8) (layers "*.Cu" "*.Mask") (net '+str(net)+' "'+name+'") (uuid "'+PADS[i]+'")))'))
    tree.append(sx.parse('(gr_rect (start 5 5) (end 25 21) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts") (uuid "'+uid('edge')+'"))'))
    tree.append(sx.parse('(zone (net 2) (net_name "GND") (layer "B.Cu") (uuid "'+uid('zone')+'") (hatch edge 0.5) (connect_pads yes (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy 6 13) (xy 24 13) (xy 24 20) (xy 6 20))))'))
    if case!='missing_track':tree.append(sx.parse('(segment (start 10 10) (end 20 10) (width '+('0.2' if case=='narrow_track' else '0.3')+') (layer "F.Cu") (net 1) (uuid "'+TRACK+'"))'))
    return (sx.dump(tree)+'\n').encode()


def expected(case,native):
    if case not in CASES:raise p.Rejected('unknown compatibility fixture')
    if native['exclusions']:return False,[]
    if case=='positive':return p.native_accepted(native) and native['warnings']==0 and not native['findings'],[]
    kind='unconnected_items' if case=='missing_track' else 'track_width'
    target=set(PADS[:2]) if case=='missing_track' else {TRACK}
    hits=[row for row in native['findings'] if row['type']==kind and row['severity']=='error' and row.get('excluded',False) is False
          and target<={item.get('uuid') for item in row['items']}]
    return not p.native_accepted(native) and bool(hits),hits
