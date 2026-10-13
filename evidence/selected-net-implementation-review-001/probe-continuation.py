"""Synthetic full-checker receipt controls only; no native or solver execution.
Authored minimal legacy board and fabricated process/report/code metadata are
NOT native qualification. All production checks remain unpatched.
"""
import copy,hashlib,json,shutil,sys,uuid
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, preferences as pref, routing_scope as rs, sexpr as sx
from autorouter import review_export as e
OWN=Path(__file__).resolve().parent
SOURCE_FILES=['autorouter/routing_scope.py','autorouter/preferences.py','autorouter/pipeline.py','autorouter/floor_route.py','autorouter/review_export.py','autorouter/__main__.py']
initial={f:p.sha(ROOT/f) for f in SOURCE_FILES}
base=OWN/'synthetic';source=base/'source/board.kicad_pcb';source_dir=source.parent;run=base/'run';candidate=run/'candidate'/source.name;receipt=run/'result.json';native_input=run/'final-drc-input'/source.name
original=sx.read(source);final=copy.deepcopy(original);final.remove(final[-3]);final.append(['segment',['start','1','1'],['end','2','1'],['width','0.2'],['layer','"F.Cu"'],['net','1'],['uuid','"00000000-0000-0000-0000-000000000004"']])
data=json.loads(receipt.read_text());data['candidate_sha256']=hashlib.sha256((sx.dump(final)+'\n').encode()).hexdigest();data['steps'][-1]['validated_input_sha256']=data['candidate_sha256']
process=json.loads((run/'final-drc-process.json').read_text());choice={'scope':'selected_nets','nets':['SEL'],'profile':'completion-only'};request={'snapshot':pref.snapshot(overrides=choice)}
def route(net,ident):return ['segment',['start','1','1'],['end','2','1'],['width','0.2'],['layer','"F.Cu"'],['net',str(net)],['uuid','"'+str(uuid.UUID(int=ident))+'"']]
def bind_final(d):
 d['candidate_sha256']=p.sha(candidate);expected=dict(d['source_hashes']);expected[candidate.name]=d['candidate_sha256'];native_input.write_bytes(candidate.read_bytes());p.save_json(run/'final-drc-binding.json',{'source':str(candidate),'input':str(native_input),'saved':False,'before':expected,'after':expected});d['steps'][-1]['validated_input_sha256']=d['candidate_sha256']
# No native/process execution is permitted. Any unexpected process call fails.
results=[]
def check(label,mutation=None,expect='reject'):
 d=copy.deepcopy(data); candidate.write_bytes((sx.dump(final)+'\n').encode());native_input.write_bytes(candidate.read_bytes())
 (run/'routing-preferences.json').write_bytes(request['snapshot']);p.save_json(run/'final-drc-process.json',process)
 if mutation:mutation(d)
 bind_final(d);p.save_json(receipt,d)
 try:
  with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):
   value=p.check_result(receipt)
  outcome='current'
 except (p.Rejected,ValueError,KeyError,FileNotFoundError) as exc:
  outcome='reject';value={'type':type(exc).__name__,'reason':str(exc)}
 entry={'case':label,'expected':expect,'outcome':outcome,'matched':outcome==expect,'detail':value};results.append(entry);print(json.dumps(entry,sort_keys=True))
check('resumed controlling positive',expect='current')
def changednetlist(d):
 tree=sx.read(candidate);sx.children(tree,'net')[1][2]='"ALTERED"';sx.write(candidate,tree)
check('changed netlist with all final hashes rebound',changednetlist)
check('false schematic parity declaration',lambda d:d.update(schematic_parity='unavailable: no native schematic in source project'))
def no_flag(d):
 current=copy.deepcopy(process);current['argv'].remove('--schematic-parity');p.save_json(run/'final-drc-process.json',current);d['steps'][-1].update(argv=current['argv'])
check('final native parity argv missing despite copied schematic',no_flag)
def absent_dsn(d):
 d.pop('native_dsn_sha256');d.pop('task_dsn_sha256')
check('selected DSN provenance downgraded by removing both retained hash fields',absent_dsn)
def changed_dsn(d):
 absent_dsn(d);(run/'native.dsn').write_text('changed wrong task export\n');(run/'task.dsn').write_text('changed unrelated solver task\n')
check('changed retained routing exports with downgrade hash fields removed',changed_dsn)
def logs():
 old=[]
 for line in (OWN/'probe.log').read_text().splitlines():
  if line.startswith('{"case"'):old.append(json.loads(line))
 return old
p.save_json(OWN/'results.json',{'kind':'synthetic consistency controls only','native_validation_performed':False,'subprocesses_executed':0,'source_sha256_before':initial,'source_sha256_after':{f:p.sha(ROOT/f) for f in SOURCE_FILES},'preserved_controller_error':'probe.log original changed-netlist mutation called sx.one on multiple root nets; remaining cases resumed here without repeating first13','results':logs()+results})
