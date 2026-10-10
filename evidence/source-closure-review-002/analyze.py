"""Bounded primary metadata closure analysis; no acquired assets/code executed."""
import base64,datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git_blob(path):
    data=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def rows(path):
    raw=read(path);assert raw['truncated'] is False
    result={r['path']:r for r in raw['tree']};assert len(result)==len(raw['tree']);return result
fetch=read(OUT/'fetch-receipt.json');assert len(fetch['records'])==6
assert sum(r['bytes'] for r in fetch['records'])<=2*1024**2
for row in fetch['records']:assert row['status']==200 and sha(OUT/row['file'])==row['sha256']
before=rows(OUT/'pre-introduction-tree.json');intro=rows(OUT/'introduction-tree.json');atboard=rows(OUT/'board-date-library-tree.json')
later=rows(ROOT/'.runs/source-closure-review-001/library-tree.json');initialboard=rows(OUT/'board-initial-tree.json')
publishedboard=rows(ROOT/'.runs/corpus-next-001/metadata/sparkfun__SparkFun_Roller_Encoder_Breakout/tree.json')
prior=read(ROOT/'.runs/source-closure-review-001/closure.json');source=ROOT/'.data/corpus-expansion-audit-001/sparkfun__SparkFun_Roller_Encoder_Breakout'
source_binding={}
for path,old in prior['original_files_verified_unchanged'].items():
    actual=sha(source/path);assert old['expected']==old['actual']==actual
    blob=git_blob(source/path);assert publishedboard[path]['sha']==blob
    if path in initialboard:assert initialboard[path]['sha']==blob
    source_binding[path]={'sha256':actual,'git_blob':blob,'same_initial_commit_blob':path in initialboard}
readme=read(OUT/'historical-readme-blob.json');data=base64.b64decode(readme['content']);readme_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
assert readme_blob==readme['sha']==intro['README.md']['sha']==atboard['README.md']['sha']=='be474d7373f263fedd6923edb01956afae65e778'
text=data.decode();assert 'https://creativecommons.org/licenses/by/4.0/' in text
changed=[]
for path in sorted(set(before)|set(intro)):
    a,b=before.get(path),intro.get(path)
    if (a or b)['type']=='blob' and (a or {}).get('sha')!=(b or {}).get('sha'):changed.append({'path':path,'before':a,'after':b})
assert [x['path'] for x in changed]==['Footprints/SparkFun-3D-models/Electromechanical/Roller_Encoder.step']
board=sx.read(source/'Hardware/SparkFun_Roller_Encoder_Breakout.kicad_pcb')
references=sorted({sx.unquote(m[1]) for fp in sx.children(board,'footprint') for m in sx.children(fp,'model')})
models=[]
for lead in prior['candidate_models_not_acquired']:
    suffix=lead['path'].split('/',1)[1].replace('.3dshapes/','/')
    old='Footprints/SparkFun-3D-models/'+suffix
    assert intro[old]['sha']==atboard[old]['sha']==later[lead['path']]['sha']==lead['sha']
    assert intro[old]['size']==atboard[old]['size']==lead['size']
    models.append({'original_path':old,'introduction_tree_blob':intro[old]['sha'],'board_date_tree_blob':atboard[old]['sha'],'later_path':lead['path'],'later_blob':lead['sha'],'bytes':lead['size'],'same_git_blob':True,'matching_board_references':[r for r in references if r.endswith('/'+suffix)],'asset_fetched':False,'asset_specific_rights_inspected':False,'pin_url':'https://github.com/sparkfun/SparkFun-KiCad-Libraries/blob/61dfcfcea753a004b6bf6164578e6eb80973fffb/'+old})
names=sorted({sx.unquote(fp[1]) for fp in sx.children(board,'footprint') if ':' in sx.unquote(fp[1])})
footprints=[]
for identity in names:
    library,name=identity.split(':',1);suffix=library+'.pretty/'+name+'.kicad_mod'
    candidates={label:[r for path,r in tree.items() if path.endswith('/'+suffix)] for label,tree in [('introduction',intro),('board_date',atboard),('later',later)]}
    footprints.append({'board_identity':identity,'candidate_metadata':candidates,'embedded_geometry_upstream_equality_verified':False})
custom=next(x for x in footprints if x['board_identity']=='RollerEncoder:RollerEncoder');assert all(not rows for rows in custom['candidate_metadata'].values())
assert not [p for p in initialboard if p.endswith(('.kicad_mod','.kicad_sym')) or Path(p).name in ('fp-lib-table','sym-lib-table')]
dated=read(OUT/'board-date-library-head.json')[0]
result={'schema':1,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_pages':len(fetch['records']),'saved_response_bytes':sum(r['bytes'] for r in fetch['records']),'download_scope':'GitHub commit/tree metadata and one historical README license-text blob only; no footprint/model geometry payloads, binaries or dataset scripts','board_commit':prior['board_commit'],'source_bindings':source_binding,'introduction_commit':'61dfcfcea753a004b6bf6164578e6eb80973fffb','introduction_parent':'c5ac11e492f6c2ed87433ae8569217b91d8b097c','introduction_changed_blob_count':len(changed),'introduction_changed_blobs':changed,'board_date_library_commit':dated['sha'],'board_date_library_commit_date':dated['commit']['author']['date'],'board_date_scope':'Latest returned reachable commit before published board initial timestamp; this does not prove the board author used this library revision.','full_tree_entry_counts':{'introduction':len(intro),'before_introduction':len(before),'board_date':len(atboard),'later_prior_review':len(later),'board_initial':len(initialboard)},'models':models,'footprints':footprints,'historical_license':{'path':'README.md','git_blob':readme_blob,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'publisher_statement':'CC-BY-4.0 for the library; same README blob at introduction and board-date snapshot','pin_url':'https://github.com/sparkfun/SparkFun-KiCad-Libraries/blob/61dfcfcea753a004b6bf6164578e6eb80973fffb/README.md','limits':'No asset-specific notice/header or upstream author evidence inspected; broad library statement is not silently treated as per-asset third-party title clearance.'},'source_closure_complete':False,'redistribution_closure_complete':False,'independent_family_established':False,'production_eligible':False,'native_jobs':0,'engine_jobs':0,'unresolved':['Custom RollerEncoder standalone footprint not found in bounded historical/current complete trees or initial board repository; exact origin and upstream geometry equality remain unknown.','All five model payload headers and asset-specific upstream notices/authorship remain uninspected; original board references contain paths, no blob pin.','Other five named footprint paths exist as metadata candidates, not verified embedded/upstream geometry matches.','Published Git initial import and shared logo/standoff UUIDs cannot establish independent circuit ancestry.','Original text_on_edge_cuts, inactive5mil class, and B.Cu jumper semantics still require separately bounded native support qualification.'],'recommendation':'Stop repeated metadata-only closure attempts. Keep Roller unsupported/development-exposed. Next Roller-specific closure gate is inspect the exact pinned model notices and locate the standalone custom footprint or explicitly qualify a separate embedded-2D replay scope under original full project checks. Most immediately actionable existing-population experiment is finish shared floor-guidance qualification on already licensed/acquired multichannel under unchanged original rules; do not count this as a new independent family.'}
(OUT/'closure.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'models_same_blob':len(models),'standard_footprint_candidates':len(footprints)-1,'custom_found':False,'pages':result['requested_pages'],'saved_response_bytes':result['saved_response_bytes'],'closure_complete':False},indent=2))
