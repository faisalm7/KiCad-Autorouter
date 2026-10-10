#!/usr/bin/env python3
"""Read-only audit of retained thermal diagnostic002; invokes no native tools."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, sexpr as s
import collections, hashlib, json, math, subprocess
OUT=Path(__file__).resolve().parent
RUN=ROOT/'.runs/interf-thermal-bridge-002'
BASE=ROOT/'.runs/interf-native-003'
checks={}
def check(name,value):
    checks[name]=bool(value)
    if not value:raise AssertionError(name)
def j(path):return json.loads(path.read_text())
def h(data):return hashlib.sha256(data).hexdigest()
def within(point,poly):
    x,y=point;crossings=0
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x < ax+(y-ay)*(bx-ax)/(by-ay):crossings+=1
    return crossings%2==1

def segment_distance(pt,a,b):
    v=[b[i]-a[i] for i in (0,1)];w=[pt[i]-a[i] for i in (0,1)]
    t=max(0,min(1,sum(v[i]*w[i] for i in (0,1))/sum(x*x for x in v)))
    return math.dist(pt,[a[i]+t*v[i] for i in (0,1)])

def polygon_record(poly):
    return {'vertices':len(poly),'area_mm2':abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2),'bbox':[min(v[0] for v in poly),min(v[1] for v in poly),max(v[0] for v in poly),max(v[1] for v in poly)]}

protocol=j(RUN/'protocol.json');summary=j(RUN/'diagnostic-summary.json');trial=j(RUN/'bridge-01/diagnostic-result.json');base_receipt=j(BASE/'result.json')
source=Path(protocol['source']);board=Path(trial['candidate']);original=s.read(source);base=s.read(BASE/'candidate'/source.name);candidate=s.read(board);hashes=protocol['source_hashes'];selected=protocol['proposals'][0];uid=selected['uuid']
check('one_trial_selected',len(summary['trials'])==1 and summary['trials'][0]==trial and summary['selected']=='bridge-01')
check('diagnostic_only',summary['validation_passed'] and summary['native_executed'] and summary['native_validation_requested'] and not summary['comparison_eligible'] and not summary['applied'] and not summary['physical_electrical_validation'])
check('protocol_binding',summary['protocol_sha256']==p.sha(RUN/'protocol.json'))
check('script_binding',protocol['script_sha256']==p.sha(RUN/'probe.py'))
commit=protocol['tools']['git_head']
check('script_committed',h(subprocess.check_output(['git','show',commit+':scripts/native_thermal_bridge_control.py'],cwd=ROOT))==protocol['script_sha256'])
for name,digest in protocol['tools']['implementation_sha256'].items():
    check('frozen_code:'+name,p.sha(RUN/'code'/name)==digest==h(subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)))
for name,digest in protocol['tools']['files'].items():check('pinned_tool:'+Path(name).name,p.sha(Path(name))==digest)
check('base_receipt_binding',protocol['base_receipt_sha256']==p.sha(BASE/'result.json'))
check('base_candidate_binding',protocol['base_candidate_sha256']==p.sha(BASE/'candidate'/source.name))
check('base_report_binding',protocol['base_native_report_sha256']==base_receipt['native_report_sha256']==p.sha(BASE/'final-drc.json'))
check('source_current_immutable',p.tree_hash(source.parent)==hashes)
check('both_original_snapshots',p.tree_hash(RUN/'snapshot')==p.tree_hash(BASE/'snapshot')==hashes)
check('semantic_invariants',p.immutable(candidate)==p.immutable(base)==p.immutable(original))
check('all_saved_zone_fields_unchanged',s.children(candidate,'zone')==s.children(base,'zone'))
check('candidate_final_hash',p.sha(board)==trial['candidate_sha256']==trial['proposed_candidate_sha256'])
expected=dict(hashes);expected[source.name]=trial['candidate_sha256']
check('candidate_tree_exact',p.tree_hash(board.parent)==expected)
check('exact_single_route_addition',p.routes(candidate)==p.routes(base)+[selected['node']])
protected=[r for r in p.routes(original) if p.locked(r)]
check('protected_routes',all(r in p.routes(candidate) for r in protected))
removed=[v for v in candidate if v!=selected['node']]
check('remove_bridge_restores_exact_base_bytes',h((s.dump(removed)+'\n').encode())==protocol['base_candidate_sha256'])
for phase,dirname in [('refill-drc','refill'),('final-drc','final-drc-input')]:
    binding=j(RUN/'bridge-01'/(phase+'-binding.json'))
    check(phase+':before_binding',binding['before']==expected)
    check(phase+':after_binding',binding['after']==p.tree_hash(RUN/'bridge-01'/dirname))
    if phase=='final-drc':check(phase+':unchanged_inputs',all(binding['after'].get(k)==v for k,v in expected.items()))
for step in trial['steps']:
    name=step['name'];process=j(RUN/'bridge-01'/(name+'-process.json'))
    check(name+':process_receipt',all(step[k]==v for k,v in process.items()))
    check(name+':successful_clean',step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] and not step['log_truncated'])
    check(name+':log_size',Path(step['log']).stat().st_size==step['log_bytes'])
    check(name+':owned_cwd',Path(step['cwd'])==RUN/'bridge-01')
    if name.endswith('drc'):
        check(name+':required_flags',all(x in step['argv'] for x in ['--refill-zones','--severity-all','--all-track-errors','--exit-code-violations']))
        check(name+':bound_input_hash',step['validated_input_sha256']==trial['candidate_sha256'])
        check(name+':exact_input_path',step['argv'][-1]==str(RUN/'bridge-01'/('refill' if name=='refill-drc' else 'final-drc-input')/source.name))
    else:
        check(name+':exact_candidate_path',str(board) in step['argv'])
raw=p.parse_report(RUN/'bridge-01/final-drc.json',source.name)
check('raw_native_report_binding',p.sha(RUN/'bridge-01/final-drc.json')==trial['native_report_sha256'] and raw==trial['native'])
check('refill_native_also_clean',p.parse_report(RUN/'bridge-01/refill-drc.json',source.name)==raw)
check('native_zero_findings',all(raw[k]==0 for k in ('opens','blocking','warnings','exclusions')) and raw['findings']==[])
check('native_ignored_checks_unchanged',raw['ignored_checks']==base_receipt['native']['ignored_checks'])
mapping=j(RUN/'bridge-01/final-netclasses.json');audit=p.audit_candidate_netclasses(board,protected,mapping);audit['native_map_file_sha256']=p.sha(RUN/'bridge-01/final-netclasses.json')
check('strict_native_class_audit_recomputed',audit==j(RUN/'bridge-01/final-netclass-audit.json'))
metrics=j(RUN/'bridge-01/metrics.json');check('metrics_receipt',metrics==trial['metrics'])
length=sum(math.dist(list(map(float,s.one(r,'start')[1:3])),list(map(float,s.one(r,'end')[1:3]))) for r in p.routes(candidate) if r[0]=='segment')
check('length_recomputed',abs(length-metrics['track_length_mm'])<1e-7)
check('no_unmeasured_arcs',not any(r[0]=='arc' for r in p.routes(candidate)))
check('via_count_recomputed',sum(r[0]=='via' for r in p.routes(candidate))==metrics['vias']==35)
child=sum(step['cpu_seconds']+step['monitor_cpu_seconds'] for step in trial['steps'])
check('total_accounts_children',0<=child<=summary['total_CPU_seconds'])
check('bounded_repair_only',summary['wall_seconds']<=protocol['wall_budget_seconds']==60 and summary['total_CPU_seconds']<=protocol['CPU_budget_seconds']==60)
zone=s.children(candidate,'zone')[0];check('correct_same_net_zone',s.one(zone,'net')==['net','100'] and s.one(zone,'layer')==['layer','"B.Cu"'])
polys=[[list(map(float,v[1:3])) for v in s.one(f,'pts')[1:]] for f in s.children(zone,'filled_polygon')]
points=[selected['start_mm'],selected['end_mm']];members=[[i for i,poly in enumerate(polys) if within(point,poly)] for point in points]
check('distinct_preexisting_filled_regions',members==[[20],[17]])
endpoint_info=[]
for point,membership in zip(points,members):
    poly=polys[membership[0]]
    endpoint_info.append({'point_mm':point,'saved_fill_polygon_index':membership[0],'distance_to_fill_boundary_mm':min(segment_distance(point,a,b) for a,b in zip(poly,poly[1:]+poly[:1])),'polygon':polygon_record(poly)})
# A strict copper-overlap witness to another terminal avoids relying solely on
# disappearance of a thermal finding or the checker's manual-track heuristic.
u9=next(f for f in s.children(candidate,'footprint') if any(prop[:3]==['property','"Reference"','"U9"'] for prop in s.children(f,'property')))
check('terminal_transform_unambiguous_180_degrees',s.one(u9,'at')==['at','158.115','82.55','180'] and s.one(u9,'layer')==['layer','"F.Cu"'])
terminal_witnesses=[]
for number,poly_index,degrees in [('C4',20,225),('G11',17,135)]:
    pad=next(n for n in s.children(u9,'pad') if s.unquote(n[1])==number)
    check(number+':same_net_circular_PTH',pad[2:4]==['thru_hole','circle'] and s.one(pad,'net')[1]=='100' and s.one(pad,'size')==['size','1.4','1.4'] and s.one(pad,'drill')==['drill','0.8'] and '"*.Cu"' in s.one(pad,'layers'))
    at=s.one(pad,'at');center=[158.115-float(at[1]),82.55-float(at[2])]
    angle=math.radians(degrees);point=[center[0]+.6*math.cos(angle),center[1]+.6*math.sin(angle)]
    poly=polys[poly_index];boundary=min(segment_distance(point,a,b) for a,b in zip(poly,poly[1:]+poly[:1]))
    overlap_radius=min(boundary,.7-.6,.6-.4)
    check(number+':positive_area_pad_fill_copper_overlap',within(point,poly) and overlap_radius>0.01)
    terminal_witnesses.append({'reference':'U9','pad':number,'uuid':s.unquote(s.one(pad,'uuid')[1]),'net':'GND','global_center_mm':center,'local_pad_at':at,'footprint_at':s.one(u9,'at'),'fill_polygon':poly_index,'annulus_inner_radius_mm':.4,'annulus_outer_radius_mm':.7,'witness_point_mm':point,'witness_radius_from_pad_center_mm':.6,'minimum_open_disk_overlap_radius_mm':overlap_radius,'kind':'positive-area intersection of unchanged saved fill and PTH annular copper, independent of proposed bridge'})
check('destination_independently_reaches_other_terminal',terminal_witnesses[1]['pad']!='C4' and terminal_witnesses[1]['fill_polygon']==17)
geometry={'bridge':selected,'endpoint_memberships':endpoint_info,'saved_fill_unchanged':True,'terminal_copper_overlap_witnesses':terminal_witnesses,'explanation':'The continuous 0.5 mm B.Cu GND track has its centerline endpoints strictly inside two different pre-existing polygons of the same GND zone. Those polygon vertices remain identical after native refill. Copper connectivity can join separate fill polygons through a track without merging their polygon records.'}
control={'kind':'prospective negative counterfactual; not executed','source_positive_run':str(RUN),'wall_and_CPU_budget_seconds':30,'heavy_workers':1,'max_trials':1,'engine_jobs':0,'edit':'Copy bridge-01 candidate into a fresh project-local output. Delete only segment UUID '+uid+'.','before_native_assertions':['Positive input SHA '+trial['candidate_sha256'],'Exactly one matching segment with exact saved proposal geometry','Deleted result serialized by sexpr.write equals base SHA '+protocol['base_candidate_sha256'],'All project sidecars, source/snapshots, immutable geometry and protected routes unchanged'],'validation':'Use validate_candidate with original immutable board, original source hashes and protected routes; full refill, strict native netclass audit and final native DRC. Retain raw reports, all process receipts, final input hashes and wall/CPU totals. No geometry/rule changes after deletion.','expected':'Rejected: zero opens and one blocking starved_thermal on pad 387e8928-4a73-4b3a-ae74-249440996e94 and zone 00000000-0000-0000-0000-00004cdec22b, matching retained failed003. Other outcomes are evidence, never coerced to this expectation.','claim_scope':'Tests whether exact bridge removal restores the native failure. Does not establish repair generalization or a fair complete-routing comparison.'}
report={'schema':1,'passed':all(checks.values()),'check_count':len(checks),'checks':checks,'review_scope':'Independent read-only audit of retained native execution; reviewer did not rerun native tools. Original diagnostic author re-review, not independent external PCB review.','native_jobs_executed_by_review':0,'frozen_commit':commit,'candidate_sha256':trial['candidate_sha256'],'native_report_sha256':trial['native_report_sha256'],'native_counts':{k:raw[k] for k in ['opens','blocking','warnings','exclusions']},'metrics':metrics,'repair_wall_seconds':summary['wall_seconds'],'repair_total_CPU_seconds':summary['total_CPU_seconds'],'reaped_native_CPU_seconds':child,'derived_nonchild_CPU_seconds':summary['total_CPU_seconds']-child,'geometry':geometry,'counterfactual':control,'limitations':['One exposed failed incumbent and one successful fixed bridge diagnostic; no end-to-end improvement claim.','Native zero reported findings respects original ignored checks, including connection_width; it is not universal physical/electrical signoff.','Frozen receipts establish internal consistency rather than authenticity against wholly fabricated history.']}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'native':report['native_counts'],'wall':summary['wall_seconds'],'CPU':summary['total_CPU_seconds'],'endpoints':endpoint_info},indent=2))
