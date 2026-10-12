"""Static source/API and retained-byte checks only; never starts a JVM."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
old=(HERE/'MixedClassProbe-before-local250.java').read_text()
path=ROOT/'experiments/pic_mixed_transport_probe_v1/MixedClassProbe.java'
new=path.read_text()
start=new.index('  /** Finite post-load diagnostic')
end=new.index('  static void run(',start)
legacy=new[:start]+new[end:]
legacy=legacy.replace('Map<String,Object> row,boolean local250)throws Exception{','Map<String,Object> row)throws Exception{')
legacy=legacy.replace('    if(local250){var before=map();row.put("state_before_local",before);observe(board,before);applyLocal250(board,row);}\n','')
legacy=legacy.replace('    if(args.length!=2&&(args.length!=3||!"local250".equals(args[2])))\n      throw new IllegalArgumentException("input DSN, output JSON and optional literal local250 required");\n    boolean local250=args.length==3;','    if(args.length!=2)throw new IllegalArgumentException("input DSN and output JSON required");')
legacy=legacy.replace('try{run(raw,flag,row,local250);}','try{run(raw,flag,row);}')
assert legacy==old,'unexpected changes in original two-argument control path'
api={
 '.runs/pic-local-clearance-api-001/javap.log':['public void clearanceValueChanged();','public void reinsertTreeItems();','public boolean validateEntries(app.freerouting.board.model.items.Item);'],
 '.runs/custom-pad-area-api-inspection-006/public.txt':['public boolean appendClass(java.lang.String);','public void setValue(int, int, int, int);','public int getLayerCount();'],
 '.runs/custom-pad-area-api-inspection-002/app.freerouting.board.model.items.Item.txt':['public void changeClearanceClassIndex(int);']}
for name,signatures in api.items():
 text=(ROOT/name).read_text()
 for signature in signatures:assert signature in text,(name,signature)
actual=json.loads((ROOT/'.runs/pic-mixed-transport-probe-005/observations.json').read_text())
identities=[]
for case in actual['cases']:
 state=case['state'];assert state['clearance_class_names']==['null','default','smd','POWER','board_edge']
 assert state['board_units_per_um']==10
 pins=sorted([p for p in state['pins'] if p['reference']=='JP1'],key=lambda p:p['number'])
 assert [(p['number'],p['nets'],p['clearance_class_index']) for p in pins]==[('1',['VCC'],3),('2',['/pic_sockets/VCC_PIC'],2)]
 targets=[]
 for pin in pins:
  areas=[a for a in state['areas'] if a['nets']==pin['nets']]
  assert len(areas)==1
  area=areas[0];assert area['fixed']=='USER_FIXED' and area['id'] in pin['contacts'] and pin['id'] in area['contacts']
  targets.extend([pin['id'],area['id']])
  for layer in range(2):
   for a,b in [(pin['clearance_class_index'],4),(4,pin['clearance_class_index'])]:
    entry=[x for x in state['matrix'] if (x['a'],x['b'],x['layer'])==(a,b,layer)]
    assert len(entry)==1 and entry[0]['raw_um']==250
 identities.append({'obstacle':case['requested_obstacle'],'changed_item_ids':sorted(targets)})
print(json.dumps({'scope':'Static source/API and retained005 data checks only; no compiler/JVM/native execution.',
 'legacy_path_reverse_source_equal':True,'api_signatures_present':True,'retained005_prerequisites':identities,
 'java_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'compilation_or_runtime_qualified':False},indent=2))
