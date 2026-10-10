"""Read-only audit of completed original-format LiPo context/DRC diagnostic002."""
from pathlib import Path
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib,json,math,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
RUN=ROOT/'.runs/lipo-native-diagnostic-002';SOURCE=ROOT/'.data/expansion003/lipo-disconnector'
HEAD='dbea85e796a1024ade7346568369283719289d86'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,floor_route as f,placement_clearance as io,config as c
checks=[]
def ck(value,name):
 checks.append({'check':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def raw(path,limit=128*1024*1024):return io.read_bytes(path,limit)
def sha(path):return hashlib.sha256(raw(path)).hexdigest()
def read(path):return f.read_json(path)
def inv(path):return io.inventory(path,max_bytes=20*1024*1024,max_files=512,max_entries=1024)
def git(*args):return subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=ROOT,capture_output=True,check=True,timeout=3).stdout
def nm(value):return int((Decimal(str(value))*1000000).quantize(Decimal(1),rounding=ROUND_HALF_UP))
def main():
 if (HERE/'audit.json').exists():raise ValueError('refuse audit collision')
 start=time.monotonic();before=inv(RUN);source_before=inv(SOURCE);d=read(RUN/'summary.json');obs=read(RUN/'observation.json');board=SOURCE/'lipo_disconnector.kicad_pcb';tree=sx.read(board);project=read(board.with_suffix('.kicad_pro'))
 ck(d['status']=='observations_complete' and d['observations_complete'] is True and d['original_inputs_unchanged'] is True,'completed observations, not route acceptance')
 for field in ['routing_accepted','dependency_complete','format_support_qualified','semantic_migration_performed','board_saved','new_engine_execution','dsn_export_requested','dsn_export_succeeded']:ck(d[field] is False,field+' remains false')
 ck(d['observation']=='context-only' and d['native_observation_mode']=='final' and d['native_dsn_sha256'] is None and not (RUN/'native.dsn').exists(),'explicit context-only final mode, no DSN')
 ck(d['native_executed'] is True and [x['name'] for x in d['steps']]==['observe','original-drc'],'exact two actual native stage census')
 receipt=ROOT/'.runs/licensed-acquisition-003/lipo-disconnector-001/receipt.json';acq=read(receipt)
 ck(sha(receipt)==d['acquisition_receipt_sha256']=='b57bc2ce29d7c5e45939fbf917896d02536b357e8b5a08c04828dd8305107c27','exact original acquisition receipt')
 ck(acq['status']=='acquired_unqualified' and acq['split']=='development','source remains development unqualified')
 expected={};total=0
 for row in acq['files']:
  path=ROOT/row['local_path'];ck(path.is_relative_to(SOURCE),'acquisition path within source '+path.name);payload=raw(path);rel=str(path.relative_to(SOURCE))
  ck(rel not in expected and len(payload)==row['bytes'] and sha(path)==row['sha256'] and hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==row['git_blob_sha1'],'source original size/SHA/Git blob '+rel)
  expected[rel]=row['sha256'];total+=len(payload)
 ck(total==4194990 and len(expected)==26 and source_before==expected==d['source_hashes']==inv(RUN/'observe-input'),'all original26files and first complete copy exact')
 ck(d['planned_project_copy_bytes']==2*total,'two project payloads admitted within output cap')
 ck(sha(board)=='3ef2141230ce971115381107486892bdf06a724c5d31d9ef2103622e113cf4e0' and sha(board.with_suffix('.kicad_pro'))=='8bc2dc577fb98404f317730b10ba2945f213a14e212b7a0b3e7fba7943a8d95e','original board/project bytes exact')
 ck(sx.one(tree,'version')==['version','20220621'],'original version unchanged')
 try:p.preflight(board)
 except p.Rejected as exc:gate=str(exc)
 else:raise AssertionError('unexpected source admission')
 ck(gate==d['production_gate_rejection']=='unsupported: unqualified board format version','production still rejects original format')
 ck(d['tools']['git_head']==HEAD and git('rev-parse','HEAD').decode().strip()==HEAD,'exact current frozen HEAD')
 ck(d['runtime_sources']==d['code_inventory']==inv(RUN/'code'),'complete runtime snapshot exact')
 ck(set(d['runtime_sources'])==set(d['tools']['implementation_sha256'])|{'toolchain.lock.json','experiments/lipo_native_diagnostic_v1/driver.py','experiments/lipo_native_diagnostic_v1/test_driver.py'},'exact source population')
 for path,digest in d['runtime_sources'].items():ck(sha(ROOT/path)==sha(RUN/'code'/path)==digest and hashlib.sha256(git('show',HEAD+':'+path)).hexdigest()==digest,'committed/helper/copied bytes '+path)
 for path,digest in d['tools']['files'].items():ck(sha(Path(path))==digest,'actual pinned tool '+Path(path).name)
 ck(obs['context_schema']==1 and obs['native_version']=='10.0.0' and obs['units']=='integer nanometres' and obs['mode']=='final' and obs['board_saved'] is False and obs['routing_accepted'] is False and obs['dsn_sha256'] is None,'exact native observation schema and no-save/no-DSN')
 f.context_binding(obs,RUN/'observe-input'/board.name,expected,'final',None);ck(True,'same-load input/project/source hashes bind original complete project')
 ck(obs['input_hashes_before']==obs['input_hashes_after']==expected,'native load left complete input unchanged')
 nets={int(x[1]):sx.unquote(x[2]) for x in sx.children(tree,'net')};pads={};netpad=Counter()
 for fp in sx.children(tree,'footprint'):
  refs=[sx.unquote(x[2]) for x in sx.children(fp,'fp_text') if x[1]=='reference'];ck(len(refs)==1,'single original footprint reference')
  for pad in sx.children(fp,'pad'):
   uid=sx.unquote(sx.one(pad,'tstamp')[1]);code=int(sx.one(pad,'net')[1]) if sx.one(pad,'net') else 0;ck(uid not in pads,'unique source pad UUID')
   pads[uid]={'uuid':uid,'reference':refs[0],'number':sx.unquote(pad[1]),'net':nets.get(code,''),'netcode':code}
   if code:netpad[nets[code]]+=1
 ck(len(pads)==len(obs['pads'])==10 and len({x['uuid'] for x in obs['pads']})==10,'all ten pad identities unique')
 for row in obs['pads']:ck({k:row[k] for k in pads[row['uuid']]}==pads[row['uuid']],'native source terminal UUID/reference/number/net '+row['uuid'])
 ck(sorted(({k:v for k,v in row.items() if k!='netcode'} for row in pads.values()),key=lambda x:x['uuid'])==sorted(d['source_notes']['source_pads_identity'],key=lambda x:x['uuid']),'static summary pad identities independently derived')
 classes=project['net_settings']['classes'];ck(len(classes)==1 and classes[0]['name']=='Default','one original Default preference class')
 pref=classes[0];dims={'width_nm':nm(pref['track_width']),'clearance_nm':nm(pref['clearance']),'via_diameter_nm':nm(pref['via_diameter']),'via_drill_nm':nm(pref['via_drill'])}
 ck(obs['nets']==d['native_effective_nets'] and len(obs['nets'])==3 and {x['name'] for x in obs['nets']}==set(netpad),'all three native/source nonempty nets exact')
 for row in obs['nets']:ck(row['class']=='Default' and row['copper_pad_count']==netpad[row['name']]==2 and row['name']==nets[row['netcode']] and all(row[k]==v for k,v in dims.items()),'native class target and terminal count '+row['name'])
 floor_comparison=[]
 for key,value in obs['floors_nm'].items():
  orig=project['board']['design_settings']['rules'][key];ck(value==nm(orig),'loaded original global floor '+key);floor_comparison.append({'name':key,'original_json_value':orig,'native_nm':value,'nearest_nm_from_original':nm(orig)})
 ck(obs['floors_nm']==d['native_effective_floors_nm'],'summary native floors exact')
 original_routes={sx.unquote(sx.one(x,'tstamp')[1]):x for x in p.routes(tree)}
 ck(len(original_routes)==len(obs['routes'])==8 and set(original_routes)=={x['uuid'] for x in obs['routes']},'all eight route identities exact')
 for row in obs['routes']:
  route=original_routes[row['uuid']];ck(row['net']==nets[int(sx.one(route,'net')[1])],'native route net '+row['uuid'])
  if route[0]=='segment':
   ck(row['kind']=='segment' and row['width_nm']==nm(sx.one(route,'width')[1]) and row['start_nm']==[nm(x) for x in sx.one(route,'start')[1:]] and row['end_nm']==[nm(x) for x in sx.one(route,'end')[1:]] and row['layer']==sx.unquote(sx.one(route,'layer')[1]),'native original segment geometry '+row['uuid'])
  else:
   ck(route[0]=='via' and row['kind']=='via' and row['width_nm']==nm(sx.one(route,'size')[1]) and row['drill_nm']==nm(sx.one(route,'drill')[1]) and row['position_nm']==[nm(x) for x in sx.one(route,'at')[1:]] and row['layers']==[sx.unquote(x) for x in sx.one(route,'layers')[1:]],'reported original via values match source; per-layer API remains unqualified '+row['uuid'])
 zones=[[x for x in z if not isinstance(x,list) or not x or x[0] not in p.DERIVED_ZONE] for z in sx.children(tree,'zone')]
 ck(zones==d['source_notes']['source_zone_intent_ast'],'summary zone intent remains static original AST only')
 ck(d['source_notes']['source_design_settings']==project['board']['design_settings'] and d['source_notes']['source_net_settings']==project['net_settings'] and d['source_notes']['source_meta']==project['meta'],'original settings and metadata unchanged in summary')
 observation_argv=f.context_argv('final',RUN/'observe-input'/board.name,RUN/'observation.json')
 drc_argv=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(RUN/'original-drc.json'),str(RUN/'original-drc-input'/board.name)]
 for step,wanted,exitcode in zip(d['steps'],[observation_argv,drc_argv],[0,5]):
  process=read(RUN/(step['name']+'-process.json'));ck(all(step[k]==v for k,v in process.items()) and step['argv']==wanted and step['cwd']==str(RUN),'exact retained process '+step['name'])
  ck(step['exit_code']==exitcode and step['status']==('success' if exitcode==0 else 'nonzero_exit') and step['cleanup_complete'] is True and step['log_truncated'] is False,'expected native exit/cleanup '+step['name'])
  ck(step['log']==str(RUN/(step['name']+'.log')) and len(raw(Path(step['log'])))==step['log_bytes']<=256*1024,'bounded raw log '+step['name'])
  ck(step['resource_guards']['max_group_rss_bytes']==2*1024**3 and step['resource_guards']['max_workdir_bytes']==20*1024**2,'actual native polling bounds '+step['name'])
  f.process_check(RUN,{'steps':d['steps']},step['name'],wanted,allowed=(exitcode,))
 for stage,names in [('stage_one_evidence',{'observation.json','observe-process.json','observe.log'}),('stage_two_evidence',{'original-drc.json','original-drc-process.json','original-drc.log'})]:
  ck(set(d[stage])==names and all(sha(RUN/name)==digest for name,digest in d[stage].items()),'early frozen stage evidence '+stage)
 binding=read(RUN/'original-drc-binding.json');target=RUN/'original-drc-input'/board.name
 ck(binding['source']==str(RUN/'observe-input'/board.name) and binding['input']==str(target) and binding['saved'] is False and binding['before']==expected,'separate original-rule nonsaving DRC input binding')
 ck(inv(target.parent)==binding['after'] and all(binding['after'].get(k)==v for k,v in expected.items()) and set(binding['after'])-set(expected)<= {board.with_suffix('.kicad_prl').name},'second complete project source/rules unchanged; only PRL allowed')
 ck(d['native_binding']=={'board_sha256':sha(target),'project_sha256':sha(target.with_suffix('.kicad_pro')),'report_sha256':sha(RUN/'original-drc.json'),'binding_sha256':sha(RUN/'original-drc-binding.json')},'native report and binding exact hashes')
 native=p.parse_report(RUN/'original-drc.json',board.name);ck(native==d['native'],'independent original parser raw report exact')
 ck({k:native[k] for k in ['opens','blocking','warnings','exclusions']}=={'opens':0,'blocking':0,'warnings':7,'exclusions':0},'raw zero opens/blocking, seven warnings, zero exclusions')
 types=Counter(x['type'] for x in native['findings']);ck(types=={'lib_footprint_issues':3,'silk_overlap':4} and all(x['severity']=='warning' for x in native['findings']),'all seven warning identities/types retained')
 ck(d['central_native_policy_accepted']==p.native_accepted(native) is True and d['central_native_rejection_reasons']==p.native_rejection_reasons(native)==[],'central raw-report predicate passes, not routing/support admission')
 settings=project['board']['design_settings'];source_ignored=sorted(k for k,v in settings['rule_severities'].items() if v=='ignore');native_ignored=sorted(x['key'] for x in native['ignored_checks']);added=sorted(set(native_ignored)-set(source_ignored))
 ck(source_ignored==d['settings_observation']['source_ignored_keys'] and native_ignored==d['settings_observation']['native_ignored_keys'] and set(source_ignored)<=set(native_ignored),'all four explicit ignored source keys retained among seven native keys')
 ck(added==['footprint_filters_mismatch','track_not_centered_on_via','tuning_profile_track_geometries'] and all(k not in settings['rule_severities'] for k in added),'three absent legacy keys obtain native ignored defaults; semantic qualification gap')
 ck(d['settings_observation']['source_exclusions']==settings['drc_exclusions']==[] and d['settings_observation']['native_exclusions']==0 and d['settings_observation']['saved_fill_or_full_semantic_equivalence_observed'] is False,'original exclusions preserved; no saved-fill equivalence claim')
 log=raw(RUN/'observe.log').decode();ck(log.count('PCB_VIA::GetWidth called without a layer argument')==2,'both native no-layer via warnings retained despite successful collector')
 ck(d['budget_seconds']==d['cpu_budget_seconds']==30 and d['within_budget'] is True and 0<d['wall_seconds']<30 and 0<d['total_cpu_seconds']<30,'actual sampled whole-run wall/CPU within thirty seconds')
 ck(abs(d['child_step_cpu_seconds']-sum(x['cpu_seconds'] for x in d['steps']))<1e-9 and d['monitor_cpu_seconds']==sum(x['monitor_cpu_seconds'] for x in d['steps']) and d['total_cpu_seconds']>=d['child_step_cpu_seconds'],'both native step CPU costs included, not double-counted as total')
 completed={name:digest for name,digest in before.items() if name!='summary.json' and not name.startswith('invalidated-')}
 ck(completed==d['completed_evidence'],'whole completed evidence inventory exact')
 size=sum((RUN/name).stat().st_size for name in before);ck(size<d['output_ceiling_bytes']==20*1024**2 and sum((RUN/name).stat().st_size for name in completed)==d['output_bytes_before_summary'],'recorded complete output bytes exact at pre-summary sampling')
 prior=read(ROOT/'.runs/review-lipo-native-001/run-inventory.json');ck(inv(ROOT/'.runs/lipo-native-diagnostic-001')==prior,'prior failed export001 remains immutable')
 ck(inv(RUN)==before and inv(SOURCE)==source_before and inv(RUN/'observe-input')==expected and inv(target.parent)==binding['after'],'all originals/copies/actual002 unchanged during audit')
 ck(git('rev-parse','HEAD').decode().strip()==HEAD and all(sha(ROOT/name)==digest for name,digest in d['runtime_sources'].items()),'final HEAD and all trusted code unchanged')
 result={'schema':1,'audit_passed':True,'actual_status':d['status'],'routing_accepted':False,'format_support_qualified':False,'dependency_complete':False,'checks':checks,'git_head':HEAD,'summary_sha256':sha(RUN/'summary.json'),'observation_sha256':sha(RUN/'observation.json'),'native_report_sha256':sha(RUN/'original-drc.json'),'source_files':26,'source_bytes':total,'run_files':len(before),'run_bytes':size,'source_and_runs_unchanged':True,'native_counts':{k:native[k] for k in ['opens','blocking','warnings','exclusions']},'warning_types':dict(types),'source_ignored_keys':source_ignored,'native_ignored_keys':native_ignored,'additional_native_default_ignored_keys':added,'floor_comparison':floor_comparison,'effective_class_dimensions_nm':dims,'actual_native_stages':['final context observer, no DSN','original-rule DRC, memory refill, no board save'],'native_via_width_assertions':2,'qualification_gaps':['Native absent-key defaults differ from explicit legacy JSON; no rule-file rewrite occurred.','No full pad/footprint shape, zone/legacy-teardrop/stackup semantic witness or save/reload test.','No DSN export/import/routing; failed001 remains failed.','No full native padless footprint reference census; duplicate-reference export-cause inference remains limited.','Missing stock libraries remain unresolved; DRC warning-only is not dependency closure or physical approval.'],'stored_wall_seconds':d['wall_seconds'],'stored_total_cpu_seconds':d['total_cpu_seconds'],'child_step_cpu_seconds':d['child_step_cpu_seconds'],'accounting_limit':'Stored totals before final publication; actual final cap gate exists, but no independent outer elapsed/post-final CPU sample is invented. Polling is not a hard quota.','audit_wall_seconds':time.monotonic()-start,'reviewer_native_jobs':0,'reviewer_engine_jobs':0}
 (HERE/'run-inventory.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n');(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['audit_passed','actual_status','source_and_runs_unchanged','native_counts','additional_native_default_ignored_keys','run_files','run_bytes','audit_wall_seconds']},indent=2))
if __name__=='__main__':main()
