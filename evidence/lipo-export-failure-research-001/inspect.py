"""Read-only source/failure census. No native tools, network, or source mutation."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import sexpr as s,placement_clearance as io
SOURCE=ROOT/'.data/expansion003/lipo-disconnector/lipo_disconnector.kicad_pcb'
RUN=ROOT/'.runs/lipo-native-diagnostic-001'
def sha(path):return hashlib.sha256(io.read_bytes(path,20*1024*1024)).hexdigest()
before=io.inventory(SOURCE.parent);raw=json.loads(io.read_bytes(RUN/'summary.json'))
assert before==raw['source_hashes']
assert io.inventory(RUN/'observe-input')==before
board=s.read(SOURCE);footprints=[]
for fp in s.children(board,'footprint'):
    refs=[x for x in s.children(fp,'fp_text') if x[1]=='reference'];assert len(refs)==1
    footprints.append({'uuid':s.unquote(s.one(fp,'tstamp')[1]),'reference':s.unquote(refs[0][2]),'library_identifier':s.unquote(fp[1]),'pads':len(s.children(fp,'pad')),'position':s.one(fp,'at')[1:],'layer':s.one(fp,'layer')[1:],'attributes':(s.one(fp,'attr') or [])[1:]})
refs=Counter(x['reference'] for x in footprints)
edge=[x for x in board if isinstance(x,list) and x and x[0] in ('gr_line','gr_arc') and s.unquote(s.one(x,'layer')[1])=='Edge.Cuts']
endpoints=Counter(tuple(s.one(x,key)[1:]) for x in edge for key in ('start','end'))
metadata={'schema':1,'scope':'static original/source/failure analysis only; no new native/engine','source_sha256':sha(SOURCE),'project_sha256':sha(SOURCE.with_suffix('.kicad_pro')),'original_inventory':before,'source_file_count':len(before),
 'original_unchanged':True,'failed_run_summary_sha256':sha(RUN/'summary.json'),'failed_run_observe_log_sha256':sha(RUN/'observe.log'),'failed_run_process_sha256':sha(RUN/'observe-process.json'),
 'failed_run_code_head':raw['tools']['git_head'],'failed_run_status':raw['status'],'failed_run_wall_seconds':raw['wall_seconds'],'failed_run_total_cpu_seconds':raw['total_cpu_seconds'],'native_observation_json_exists':(RUN/'observation.json').exists(),'native_dsn_exists':(RUN/'native.dsn').exists(),'drc_report_exists':(RUN/'original-drc.json').exists(),
 'footprints':footprints,'duplicate_references':{k:v for k,v in refs.items() if v>1},'empty_references':refs.get('',0),'pads':sum(x['pads'] for x in footprints),'padless_footprints':sum(x['pads']==0 for x in footprints),'board_vias':s.children(board,'via'),
 'edges':edge,'edge_counts':dict(Counter(x[0] for x in edge)),'edge_endpoints_all_degree_two':all(n==2 for n in endpoints.values()),'edge_endpoint_degree_only_not_native_outline_validation':True,
 'native_failure_exception_not_exposed_by_bool_api':True,'duplicate_reference_cause':'strong source-backed explanation conditional on unchanged native loaded references; native all-footprint census still pending',
 'via_warning_source':'observer calls no-layer GetWidth before type dispatch; pinned API warning returns all-layer diameter; do not conflate with DSN failure',
 'native_executed_by_research':False,'engine_executed_by_research':False,'original_renamed_removed_or_saved':False}
assert io.inventory(SOURCE.parent)==before
(OUT/'analysis.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:metadata[k] for k in ['source_file_count','duplicate_references','padless_footprints','edge_counts','edge_endpoints_all_degree_two','original_unchanged']}))
