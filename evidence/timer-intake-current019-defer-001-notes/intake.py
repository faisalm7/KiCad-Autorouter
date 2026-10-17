from pathlib import Path
import sys,time,resource,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.licensed_acquisition_v1 import fetch as shared
start=time.monotonic();cpu=time.process_time();out=ROOT/'.runs/timer-intake-current019-001';out.mkdir()
repo='jenna2004jna/-STEM-Toy-PCB-Design-Using-555-Timer-KiCad-'
plan=dict(schema=1,repository=repo,reason='One ordinary low-complexity timer development-family lead for the documented licensed-coverage gap; no baseline outcome used in selection.',requests_max=3,response_bytes_total_max=192*1024,HTTP_wall_seconds=90,CAD_downloads=0,Native_jobs=0,replacement_leads=0,scope='Bounded metadata/notice intake, not a routing experiment. Earlier web search2queries and authoring time are outside this subprocess and not zero; complete researchCPU is unknown.')
(out/'predeclaration.json').write_text(json.dumps(plan,indent=2)+'\n');requests=[];total=0
record=dict(schema=1,admitted=False,routing_executed=False,repository=repo,requests=requests)
def remaining():
 left=90-(time.monotonic()-start)
 if left<=0:raise TimeoutError('finite90s intake wall deadline')
 return left
def get(label,url):
 global total
 assert len(requests)<3
 row={};requests.append(row);cap=min(64*1024,192*1024-total)
 raw=shared.fetch_one(dict(raw_url=url,bytes=cap),row,out/(label+'.raw'),cap,remaining)
 total+=len(raw);assert len(raw)<=cap
 return raw
try:
 commit=shared.decode(get('commit','https://api.github.com/repos/'+repo+'/commits/HEAD'));sha=commit['sha'];record['commit']=sha
 tree=shared.decode(get('tree','https://api.github.com/repos/'+repo+'/git/trees/'+commit['commit']['tree']['sha']+'?recursive=1'));assert tree.get('truncated') is False
 entries=tree['tree'];record['tree_entries']=len(entries);record['tree_sha']=tree['sha']
 names=[row['path'] for row in entries if row.get('type')=='blob'];record['matching_KiCad_files']=[name for name in names if name.endswith(('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru'))]
 record['license_paths']=[name for name in names if Path(name).name.lower().startswith(('license','licence','copying'))]
 raw=get('README','https://raw.githubusercontent.com/'+repo+'/'+sha+'/README.md');text=raw.decode('utf8');record['README_sha256']=hashlib.sha256(raw).hexdigest()
 record['README_license_statement_present']='MIT' in text and 'retain attribution' in text
 record['decision']='defer_pending_complete_rights_notice_review'
 record['reason']='Complete matching KiCad triplet exists, but the tree has no standalone license/copying file. README namesMIT and asks retained attribution; no complete MIT grant/notice body was verified. No rawCAD was downloaded, source rewritten or routing/family acceptance claimed. This is a documented research lead, not a legal conclusion that MIT-by-reference is invalid.'
except BaseException as exc:
 record.update(decision='defer_failed_metadata',error=type(exc).__name__+': '+str(exc))
record.update(received_bytes=total,subprocess_inner_wall_seconds=time.monotonic()-start,subprocess_parent_CPU_seconds=time.process_time()-cpu,within_subprocess_limits=time.monotonic()-start<=90 and total<=192*1024)
(out/'decision.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record.get(k)for k in('decision','commit','tree_entries','license_paths','README_license_statement_present','received_bytes','subprocess_inner_wall_seconds','within_subprocess_limits','error')}))
