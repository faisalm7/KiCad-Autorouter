"""Offline independent actual fixture002 audit; no native/engine processes."""
from pathlib import Path
import sys,json,math,hashlib
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path[:0]=[str(ROOT),str(ROOT/'experiments/placement_diagnostic_v1')]
from autorouter import pipeline as p,sexpr as sx,board_floor as g,floor_route as f
import diagnostic_route as d,experiment_pair as pair
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-routing-fixture-002';OLD=ROOT/'.runs/placement-routing-fixture-001';read=lambda x:json.loads(x.read_text());checks=[]
def ok(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def main():
 data=read(RUN/'result.json');before=p.tree_hash(RUN);old_before=p.tree_hash(OLD);source=Path(data['source']);source_before=p.tree_hash(source.parent);candidate=Path(data['candidate']);original=sx.read(source);final=sx.read(candidate)
 ok('accepted diagnostic scope only',data['status']=='diagnostic_accepted' and data['routing_accepted'] is True and data['production_qualified'] is False and data['comparison_eligible'] is False and data['physical_electrical_validation'] is False)
 ok('same current frozen code/tools for prospective pair',p.tool_manifest()==data['tools'] and data['tools']['git_head']=='73107be01a4e561d68d85a99ef8efab08ce4161c')
 d.verify_freeze(data['freeze']);checks.append('full helper/core/protocol freeze still exact')
 for name,digest in data['freeze']['files_sha256'].items():ok('retained implementation '+name,p.sha(RUN/'code/source'/name)==digest)
 ok('original complete project/source/snapshot unchanged',p.tree_hash(RUN/'snapshot')==source_before==data['source_hashes'])
 ok('candidate original nonboard files unchanged',p.tree_hash(candidate.parent)=={**source_before,source.name:data['candidate_sha256']} and candidate.read_bytes()==(sx.dump(final)+'\n').encode())
 ok('exact candidate hash and immutable original semantic geometry',p.sha(candidate)==data['candidate_sha256']=='1156fd0919db5ad1aa40f54fd8c631fcc950b975757686f42048f0c95a969b5f' and p.immutable(final)==p.immutable(original))
 areas=d.narrow_source(original);ok('one exact unrestricted area; no genuine keepout',len(areas)==1 and areas[0]['is_rule_area'] and areas[0]['placement_enabled'] and areas[0]['placement_source_type']=='SHEETNAME' and not any(areas[0]['disallow'].values()))
 ok('original area and no copper fill changed',sx.children(original,'zone')==sx.children(final,'zone') and all(not sx.children(z,'filled_polygon') and not sx.children(z,'fill_segments') for z in sx.children(final,'zone')))
 task,contract,chain=d.derive(RUN,source_before,data['policy']);ok('rederived raw floor placement both chain exact',chain==data['chain'] and chain['placement_removed_count']==2)
 raw=g._parse_dsn((RUN/'native.dsn').read_text());guided=g._parse_dsn((RUN/'floor-guided.dsn').read_text());placed=g._parse_dsn((RUN/'pre-adapter.dsn').read_text());adapted=g._parse_dsn((RUN/'task.dsn').read_text())
 rawkeep=sx.children(sx.one(raw,'structure'),'keepout');guidekeep=sx.children(sx.one(guided,'structure'),'keepout')
 ok('two exact false keepouts only removed after floor',len(rawkeep)==2 and guidekeep==rawkeep and not sx.children(sx.one(placed,'structure'),'keepout') and placed==adapted)
 export=read(RUN/'floor-export-context.json');area=read(RUN/'area-context.json');nfinal=read(RUN/'floor-final-context.json');ok('same-load floor+area identities and no retained routes',all(export[k]==area[k] for k in ('source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after','board_saved')) and export['routes']==[] and len(export['pads'])==4 and len(export['nets'])==2 and area['footprint_zone_count']==area['footprint_rulearea_count']==0)
 ok('native preference/floor semantics preserved',export['floors_nm']==nfinal['floors_nm'] and export['nets']==nfinal['nets'] and export['pads']==nfinal['pads'] and contract['transformation']['raw_nm']=={'width_nm':200000,'clearance_nm':200000,'via_diameter_nm':600000,'via_drill_nm':300000} and contract['transformation']['derived_nm']=={'width_nm':300000,'clearance_nm':300000,'via_diameter_nm':1500000,'via_drill_nm':300000})
 ok('SES and imported route transport retained',0<(RUN/'routes.ses').stat().st_size<=sx.MAX_BYTES and (RUN/'imported.kicad_pcb').is_file())
 f.audit_transport(RUN,data,task,candidate);checks.append('exact source DRC / import route / saved refill reconstruction')
 routes=p.routes(final);segments=[x for x in routes if x[0]=='segment'];vias=[x for x in routes if x[0]=='via'];length=sum(math.dist([float(v) for v in sx.one(t,'start')[1:]],[float(v) for v in sx.one(t,'end')[1:]]) for t in segments)
 ok('direct generated dimensions and required via',len(vias)==1 and all(sx.one(t,'width')==['width','0.3'] for t in segments) and sx.one(vias[0],'size')==['size','1.5'] and sx.one(vias[0],'drill')==['drill','0.3'] and sx.unquote(sx.one(vias[0],'net')[1])=='SIGNAL_A')
 ok('direct geometric metrics agree',len(segments)==7 and abs(length-data['metrics']['track_length_mm'])<1e-8 and data['metrics']['vias']==1 and data['metrics']['pads']==4 and data['metrics']['zones']==1)
 for name in ('source-drc','refill-drc','final-drc'):
  native=p.parse_report(RUN/(name+'.json'),source.name);ok(name+': actual raw findings clean',all(native[k]==0 for k in ('opens','blocking','warnings','exclusions')) and native['findings']==[] and native['ignored_checks']==data['source_drc']['ignored_checks'])
 ok('exact final raw report and native candidate copy',p.sha(RUN/'final-drc.json')==data['native_report_sha256'] and p.sha(RUN/'final-drc-input'/source.name)==p.sha(candidate) and read(RUN/'final-drc-binding.json')['before']==p.tree_hash(candidate.parent))
 ok('all eight actual processes completed once',len(data['steps'])==8 and [s['name'] for s in data['steps']]==['source-drc','floor-area-export','engine','import','refill-drc','floor-final','final-drc','metrics'] and all(s['status']=='success' and s['exit_code']==0 and s['cleanup_complete'] for s in data['steps']))
 ok('completion-only strict target flags',{'--router.optimizer.enabled=false','--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0'}<=set(data['engine_budget']['argv']) and data['engine_budget']['assigned_job_timeout_seconds']==16 and data['engine_budget']['native_finalization_reserve_seconds']==10 and data['engine_budget']['engine_grace_reserve_seconds']==30)
 verdict=d.check_result(RUN/'result.json');ok('independent full diagnostic process/native readback',verdict=={'diagnostic_verified':True,'routing_accepted':True,'production_qualified':False})
 fixture=pair.fixture_gate(RUN/'result.json',data['freeze']);ok('same-code exact fixture pair prerequisite passes',fixture==before)
 ok('finite shared wall CPU caps and accounting',all(math.isfinite(data[k]) and 0<data[k]<=60 for k in ('wall_seconds','total_cpu_seconds')) and data['budget_seconds']==data['cpu_budget_seconds']==60 and abs(data['parent_cpu_seconds']+data['waited_child_cpu_seconds']-data['total_cpu_seconds'])<1e-8 and data['waited_child_cpu_seconds']>=sum(s['cpu_seconds'] for s in data['steps']))
 ok('review unchanged entire run original failed001 and source',p.tree_hash(RUN)==before and p.tree_hash(OLD)==old_before and p.tree_hash(source.parent)==source_before)
 result={'schema':1,'audit_passed':True,'check_count':len(checks),'checks':checks,'native_or_engine_executed_by_reviewer':False,'source_sha256':p.sha(source),'candidate_sha256':p.sha(candidate),'raw_final_report_sha256':p.sha(RUN/'final-drc.json'),'receipt_sha256':p.sha(RUN/'result.json'),'run_inventory':before,'same_code_pair_prerequisite_passed':True,'metrics':data['metrics'],'recorded_wall_seconds':data['wall_seconds'],'recorded_cpu_seconds':data['total_cpu_seconds'],'accounting_point':data['accounting_point'],'scope':'One owned diagnostic fixture, one unrestricted placement area, no copper-fill zones; genuine keepout enforcement and production/generalized/physical routing remain unqualified.'}
 with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks','run_inventory')},indent=2))
if __name__=='__main__':main()
