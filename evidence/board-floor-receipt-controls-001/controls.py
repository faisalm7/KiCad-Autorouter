"""Offline copies of actual native001 evidence. No native/engine execution."""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,sexpr as sx
BASE=ROOT/'.runs/board-floor-production-native-001';ORIGINAL=json.loads((BASE/'result.json').read_text());SOURCE=Path(ORIGINAL['source']);LIMIT=16*1024*1024
CASES=['positive','missing_ses','missing_import','missing_refill','arbitrary_source_command','downgraded_policy','wrong_generated_width','changed_candidate_rules','stale_source_copy']
def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def size(root):return sum(x.stat().st_size for x in root.rglob('*') if x.is_file())
def refresh(run,data):
 data['floor_evidence_hashes']=f.evidence_inventory(run);dump(run/'result.json',data)
def replace_paths(value,replacements):
 if isinstance(value,str):
  for old,new in replacements:value=value.replace(old,new)
  return value
 if isinstance(value,list):return [replace_paths(x,replacements) for x in value]
 if isinstance(value,dict):return {k:replace_paths(v,replacements) for k,v in value.items()}
 return value
def relocate(label):
 case=HERE/'cases'/label;case.mkdir(parents=True,exist_ok=False);run=case/'run';source=case/'source'
 shutil.copytree(BASE,run);shutil.copytree(SOURCE.parent,source)
 replacements=[(str(BASE),str(run)),(str(SOURCE.parent),str(source))];modified=[]
 # Only top-level run receipts are rebound. Boards, DSN, SES, original project
 # files, logs, code snapshots and nested source seeds remain exact raw copies.
 for path in sorted(run.glob('*.json')):
  value=json.loads(path.read_text());changed=replace_paths(value,replacements)
  if changed!=value:dump(path,changed);modified.append(path.name)
 data=json.loads((run/'result.json').read_text());context=json.loads((run/'floor-export-context.json').read_text());policy=json.loads((run/'floor-policy.json').read_text())
 policy['transformation']['native_context_content_sha256']=hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump(run/'floor-policy.json',policy)
 final=json.loads((run/'floor-final-audit.json').read_text());final['native_context_sha256']=p.sha(run/'floor-final-context.json');dump(run/'floor-final-audit.json',final)
 data['floor_policy']['sha256']=p.sha(run/'floor-policy.json');refresh(run,data)
 if size(HERE)>LIMIT:raise RuntimeError('16MiB control artifact ceiling exceeded')
 checked=p.check_result(run/'result.json')
 raw_names=['native.dsn','floor-guided.dsn','task.dsn','routes.ses','imported.kicad_pcb','candidate/'+SOURCE.name,'refill/'+SOURCE.name,'engine.log','source-drc.log','refill-drc.log','final-drc.log']
 assert all((run/name).read_bytes()==(BASE/name).read_bytes() for name in raw_names)
 return case,run,source,data,{'positive_readback':checked,'rebound_top_level_json':modified,'raw_selected_files_unchanged':raw_names,'source_copy_hashes':p.tree_hash(source)}
def mutate(label,run,source,data):
 if label=='missing_ses':(run/'routes.ses').unlink();return ('SES',)
 if label=='missing_import':(run/'imported.kicad_pcb').unlink();return ('import',)
 if label=='missing_refill':(run/'refill'/SOURCE.name).unlink();return ('native stage input changed','No such file')
 if label=='arbitrary_source_command':
  path=run/'source-drc-process.json';proc=json.loads(path.read_text());proc['argv']=['/usr/bin/true'];dump(path,proc);next(s for s in data['steps'] if s['name']=='source-drc')['argv']=proc['argv'];return ('provenance differs: source-drc',)
 if label=='downgraded_policy':data.update(schema=1,input_policy='native');return ('downgraded floor policy',)
 if label=='wrong_generated_width':
  board=run/'candidate'/SOURCE.name;tree=sx.read(board);sx.one(sx.children(tree,'segment')[0],'width')[1]='0.2';sx.write(board,tree);data['candidate_sha256']=p.sha(board);return ('generated track differs',)
 if label=='changed_candidate_rules':
  path=run/'candidate'/SOURCE.with_suffix('.kicad_pro').name;project=json.loads(path.read_text());project['board']['design_settings']['rule_severities']['clearance']='warning';dump(path,project);return ('candidate project/rules/file set changed',)
 if label=='stale_source_copy':
  board=source/SOURCE.name;board.write_bytes(board.read_bytes()+b'\n; deliberate local-source staleness control\n');return ('stale source project',)
 raise ValueError(label)
def main():
 if (HERE/'summary.json').exists() or (HERE/'cases').exists():raise RuntimeError('refuse control collision')
 base_hashes=p.tree_hash(BASE);source_hashes=p.tree_hash(SOURCE.parent);estimated=len(CASES)*(size(BASE)+size(SOURCE.parent))+size(HERE)
 if estimated>LIMIT:raise RuntimeError('planned copies exceed16MiB')
 summary={'schema':1,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Synthetic relocation of actual native evidence; read-only checker controls, no authentication or fresh native execution','base_run':str(BASE),'base_result_sha256':p.sha(BASE/'result.json'),'base_source':str(SOURCE),'disk_ceiling_bytes':LIMIT,'estimated_copy_bytes':estimated,'cases':[]}
 for label in CASES:
  row={'case':label,'relocation_positive':False,'expected_negative':label!='positive','passed':False}
  try:
   case,run,source,data,binding=relocate(label);row['relocation_positive']=True;dump(case/'relocation.json',binding)
   if label=='positive':row['passed']=True;row['outcome']='accepted unchanged relocated evidence'
   else:
    expected=mutate(label,run,source,data);refresh(run,data);row['expected_reason_fragments']=expected
    try:p.check_result(run/'result.json')
    except Exception as exc:
     row['outcome']='rejected';row['reason']=type(exc).__name__+': '+str(exc);row['passed']=any(text in str(exc) for text in expected)
    else:row['outcome']='UNEXPECTED ACCEPTANCE'
   dump(case/'control.json',row)
  except Exception as exc:row['outcome']='relocation/control error, not a negative pass';row['reason']=type(exc).__name__+': '+str(exc)
  summary['cases'].append(row);summary['bytes_so_far']=size(HERE);dump(HERE/'summary.partial.json',summary)
  if not row['passed']:break
 summary['original_run_unchanged']=p.tree_hash(BASE)==base_hashes;summary['original_source_unchanged']=p.tree_hash(SOURCE.parent)==source_hashes;summary['total_bytes']=size(HERE)
 summary['passed']=len(summary['cases'])==len(CASES) and all(r['passed'] for r in summary['cases']) and summary['original_run_unchanged'] and summary['original_source_unchanged'] and summary['total_bytes']<=LIMIT
 summary['limitations']=['Paths/context hashes were synthetically rebound; logs/boards/DSN/SES/code bytes remain actual original evidence until each declared mutation.','Every negative case first passed complete check_result after relocation. Rejected copies are never new native routing results.','These controls test mutable evidence consistency and fail-closed checks, not authenticity or fresh DRC.']
 dump(HERE/'summary.json',summary);print(json.dumps({'passed':summary['passed'],'cases':summary['cases'],'total_bytes':summary['total_bytes']},indent=2));return summary['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
