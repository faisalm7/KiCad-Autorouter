"""Pure readback of completed exports; no Native rerun or routing admission."""
from pathlib import Path
import copy,importlib.util,json,sys,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];RUNTIME=ROOT/'.runs/runtime042 fresh install 001'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import native_edge as prior,adapter as a,sexpr as sx,pipeline as p,floor_route as f,placement_clearance as pc
path=ROOT/'autorouter/native_edge.py';spec=importlib.util.spec_from_file_location('autorouter.fractional_candidate',path);candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
base=ROOT/'.runs/native7-fractional-export-controls-001';plan=f.read_json(base/'protocol.json');result=f.read_json(base/'result.json');pins={str(path.relative_to(ROOT)):p.sha(path)};rows=[]
for row in result['rows']:
 case=row['case'];source=Path(plan['cases'][case]['source']);dsn=base/case/'export/native.dsn';raw=pc.read_bytes(dsn)
 assert p.sha(dsn)==row['dsn_sha256'] and pc.inventory(source.parent)==plan['cases'][case]['source_hashes']
 context=candidate.derive_context(pc.read_bytes(source),pc.read_bytes(source.with_suffix('.kicad_pro')))
 adapted,adapter=a.adapt_bytes(raw,'both',[]);corrected,proof=candidate.correct(adapted,context)
 assert proof['inward_boundary']['native_host_version']=='10.0.7' and proof['inward_boundary']['output_within_original_boundary'] and proof['requested_clearance_um']=='300'
 try:prior.correct(adapted,context)
 except ValueError as exc:assert 'qualified Native10 scope' in str(exc)
 else:raise AssertionError('old guard unexpectedly admitted')
 tree=a._parse_dsn(adapted.decode());parser=sx.one(tree,'parser');faults={}
 for fault in ('missing_host','unknown_host','wrong_cad','wrong_grid','discrepancy','sub_nm_source'):
  changed=copy.deepcopy(tree);ctx=copy.deepcopy(context);parser=sx.one(changed,'parser')
  if fault=='missing_host':parser.remove(sx.one(parser,'host_version'))
  elif fault=='unknown_host':sx.one(parser,'host_version')[1]='"10.0.8"'
  elif fault=='wrong_cad':sx.one(parser,'host_cad')[1]='"Other"'
  elif fault=='wrong_grid':sx.one(changed,'resolution')[2]='100'
  elif fault=='discrepancy':
   from decimal import Decimal
   shape=sx.one(sx.one(changed,'structure'),'boundary')[1];coords=list(map(Decimal,shape[3:]));xmin=min(coords[::2]);replacement=min(Decimal(context['rect_um'][0]),xmin)-Decimal('0.501')
   for i in range(3,len(shape),2):
    if Decimal(shape[i])==xmin:shape[i]=str(replacement)
  else:ctx['rect_um'][0]=str(__import__('decimal').Decimal(ctx['rect_um'][0])+__import__('decimal').Decimal('0.0001'))
  try:candidate.correct(a._dump_dsn(changed).encode(),ctx)
  except ValueError as exc:faults[fault]=str(exc)
  else:raise AssertionError('fault admitted:'+fault)
 rows.append({'case':case,'source_hashes':plan['cases'][case]['source_hashes'],'dsn_sha256':row['dsn_sha256'],'source_unchanged':True,'prior_version_guard_refused':True,'candidate_transform':proof,'pure_invalid_mutation_refusals':faults})
assert all(p.sha(ROOT/n)==v for n,v in pins.items())
record={'schema':1,'kind':'native7-fractional-owned-export-pure-replay-v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'Native_reexecuted':False,'routing_accepted':False,'full_schematic_validation':False,'source_code':pins,'protocol_sha256':p.sha(base/'protocol.json'),'export_result_sha256':p.sha(base/'result.json'),'rows':rows,'scope':'Pure transform/refusal replay of four completed pinned10.0.7 exports. Numerical domain unchanged; actual Native DRC and final candidate qualification remain separate.'}
p.save_json(ROOT/'.runs/native7-fractional-export-pure-replay-001.json',record);print(json.dumps({'passed':True,'cases':len(rows),'pure_refusals':sum(len(x['pure_invalid_mutation_refusals']) for x in rows)}))
