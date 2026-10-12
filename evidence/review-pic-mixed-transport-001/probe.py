"""Retained actual-byte derivation plus synthetic importer observations; no Java/native."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
D=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve()
if not OUT.is_relative_to(H) or OUT.exists():raise ValueError('new review output only')
OUT.mkdir();sys.dont_write_bytecode=True;sys.path.insert(0,str(D));sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('author_pure',D/'test_draft.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
t.Pure.setUpClass();case=t.Pure();e=case.expected
# Explicit native census differs from actual DSN pin inventory: retain both.
original=case.context;tree=t._parse_dsn(case.raw.decode());s=t.sx
images={s.unquote(x[1]):x for x in s.children(s.one(tree,'library'),'image')}
placed=[]
for c in s.children(s.one(tree,'placement'),'component'):
 for p in s.children(c,'place'):
  for pin in s.children(images[s.unquote(c[1])],'pin'):
   atoms=[x for x in pin[2:] if isinstance(x,str)];placed.append((s.unquote(p[1]),s.unquote(atoms[0])))
assert len(placed)==len(set(placed))==240
assigned={(x['reference'],x['number']) for x in e['terminals']};unassigned=set(placed)-assigned
assert unassigned=={('P3','@1'),('P3','@2'),('J1','SH'),('J1','SH@1')}
def observation():
 o=case.synthetic();o['ses_executed']=False
 for row in o['cases']:
  row['post_load_awaited']=True
  # Original synthetic builder omits these; revised builders may already include them.
  if len(row['state']['pins'])==236:
   candidates=[p for p in original['pads'] if not p['netcode'] and p['reference'] in ('P3','J1')]
   names={'P3':['@1','@2'],'J1':['SH','SH@1']};counts={k:0 for k in names}
   for i,p in enumerate(candidates):
    ref=p['reference'];number=names[ref][counts[ref]];counts[ref]+=1
    row['state']['pins'].append({'id':500+i,'reference':ref,'number':number,'nets':[],
      'position_um':[x/1000 for x in p['position_nm']],'padstack_name':'other','clearance_class_index':0,'contacts':[]})
 return o
mutations={
 'positive':lambda o:None,
 'post_router_enabled':lambda o:o['cases'][0]['settings_after'].update(router_enabled=True),
 'post_optimizer_enabled':lambda o:o['cases'][0]['settings_after'].update(optimizer_enabled=True),
 'post_load_not_awaited':lambda o:o['cases'][0].update(post_load_awaited=False),
 'post_load_marker_missing':lambda o:o['cases'][0].pop('post_load_awaited'),
 'ses_executed':lambda o:o.update(ses_executed=True),
 'boolean_schema':lambda o:o.update(schema=True),
 'missing_four_unassigned':lambda o:o['cases'][0]['state'].update(pins=[p for p in o['cases'][0]['state']['pins'] if p['nets']]),
 'extra_unassigned':lambda o:o['cases'][0]['state']['pins'].append({'id':999,'reference':'UNKNOWN','number':'1','nets':[], 'position_um':[0,0],'padstack_name':'other','clearance_class_index':0,'contacts':[]}),
 'moved_unassigned':lambda o:next(p for p in o['cases'][0]['state']['pins'] if not p['nets']).update(position_um=[0,0]),
}
rows=[]
for name,mutate in mutations.items():
 o=observation();mutate(o)
 try:
  comparison=t.transport.validate(o,e);accepted=all(x['observed'] for x in comparison);error=None
 except (ValueError,KeyError,TypeError,AssertionError) as exc:accepted=False;error=str(exc)
 rows.append({'case':name,'observations_complete':accepted,'expected_complete':name=='positive','matches_expectation':accepted==(name=='positive'),'error':error})
report={'scope':'Synthetic import JSON against real retained DSN/native expectation, no worker jobs','source_sha256':hashlib.sha256((D/'transport.py').read_bytes()).hexdigest(),'native_total_pads':len(original['pads']),'assigned_native_copper_pads':len(assigned),'dsn_placed_pins':len(placed),'dsn_unassigned_pins':sorted(unassigned),'cases':rows}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
