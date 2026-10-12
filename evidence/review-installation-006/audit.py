"""Offline audit of completed installation006. No native/engine/network execution.
Reads the original run and both checkouts; writes only this review directory.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,math,os,re,sys,time,subprocess
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/installation-006';CLONE=RUN/'checkout'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,placement_clearance as pc,board_floor as g,floor_route as f
spec=importlib.util.spec_from_file_location('install_audit_source',ROOT/'scripts/install_smoke.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='eae1f398f5769851247acc01c6d0566d216563d5';checks=[]
def ck(condition,label):
 checks.append({'check':label,'passed':bool(condition)})
 if not condition:raise AssertionError(label)
def read(path):return m.read_json(path)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run_inventory():
 rows={};total=0;entries=0
 for parent,dirs,files in os.walk(RUN,followlinks=False):
  for name in list(dirs)+files:
   path=Path(parent)/name;entries+=1
   if entries>25000:raise ValueError('audit entry bound')
   rel=str(path.relative_to(RUN))
   if path.is_symlink():
    rows[rel]={'symlink':os.readlink(path)}
    if name in dirs:dirs.remove(name)
   elif path.is_file():
    size=path.stat().st_size;total+=size
    if total>512*1024*1024 or len(rows)>=16000:raise ValueError('audit inventory bound')
    rows[rel]={'bytes':size,'sha256':sha(path)}
 return rows,total

def main():
 if (HERE/'audit.json').exists():raise ValueError('refuse audit collision')
 started=time.monotonic();before,total_before=run_inventory();receipt=read(RUN/'result.json');inv=read(RUN/'source-tracked.json');commands=receipt['commands'];byname={s['name']:s for s in commands};nativepath=Path(receipt['native_receipt']['path']);ndir=nativepath.parent;n=read(nativepath);source=Path(n['source']);candidate=Path(n['candidate'])
 readback_argv=[*m.NETWORK_DENIAL,str(CLONE/'.venv/bin/python'),'-B','-m','autorouter','check-result',str(nativepath)]
 readback_started=time.monotonic();readback=subprocess.run(readback_argv,cwd=CLONE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=30)
 (HERE/'fresh-readback-001.log').write_text(readback.stdout);(HERE/'fresh-readback-001.stderr').write_text(readback.stderr)
 (HERE/'fresh-readback-process-001.json').write_text(json.dumps({'argv':readback_argv,'cwd':str(CLONE),'exit_code':readback.returncode,'wall_seconds':time.monotonic()-readback_started,'native_or_engine_started':False},indent=2)+'\n')
 ck(readback.returncode==0,'fresh clone-cwd shared check-result exit0')
 ck(receipt['passed'] is True and receipt['status']=='passed' and receipt['schema']==2,'completed installation canonical success')
 ck(receipt['git_head']==HEAD and len(commands)==20 and len(byname)==20,'exact frozen HEAD and20 distinct commands')
 ck(sha(ROOT/'scripts/install_smoke.py')==sha(CLONE/'scripts/install_smoke.py')=='573bff0244a9a08cb51a743be6004cb70ef33c9be8b0aeaa1ff678f87a02b663','reviewed installer exact bytes in source and clone')
 ck(sha(CLONE/'tests/test_install_smoke.py')==sha(ROOT/'tests/test_install_smoke.py')=='87d276c7c60b0cb5b4031a16a2d58b3edf6f0d73c578ef4f2a0d3f9187377d18','reviewed capacity test exact bytes in source and clone')
 ck(receipt['limits']['source_bytes']==192*1024**2 and receipt['limits']['source_files']==12000 and receipt['limits']['scratch_bytes']==512*1024**2,'reviewed source and unchanged scratch limits explicit')
 listing=Path(byname['source-files']['log']).read_text();clone_listing=Path(byname['clone-files']['log']).read_text();ck(listing==clone_listing and len(inv)==10699,'identical source/clone10699 tracked path lists')
 allowed_docs={'PLANS.md','REQUIREMENTS.md','STATUS.md','docs/install-test.md','evidence/claims.json'}
 current_source=m.tracked_inventory(ROOT,listing);source_differences={k:{'installation_sha256':inv[k],'current_sha256':current_source[k]}for k in inv if current_source[k]!=inv[k]}
 ck(set(source_differences)<=allowed_docs and m.tracked_inventory(CLONE,clone_listing)==inv,'complete frozen clone exact; current root differences restricted to documented post-run reporting')
 ck(sha(RUN/'source-tracked.json')==receipt['source_inventory_sha256'],'source inventory receipt hash exact')
 tracked_bytes=sum((CLONE/path).stat().st_size for path in inv);ck(tracked_bytes==154825605 and tracked_bytes<192*1024*1024,'tracked bytes under192MiB')
 network=m.NETWORK_DENIAL
 for s in commands:
  ck(s['argv'][:3]==network,s['name']+' network-denial argv')
  ck(s['status']=='success' and s['exit_code']==0 and s['cleanup_complete'] is True and not s['log_truncated'],s['name']+' success/cleanup/untruncated')
  log=Path(s['log']);ck(log.parent==RUN and log.is_file() and sha(log)==s['log_sha256'] and log.stat().st_size<=2000000,s['name']+' raw log path/hash/bound')
  ck(s['resource_guards']['max_workdir_bytes']==512*1024*1024 and s['resource_guards']['max_group_rss_bytes']==4*1024**3,s['name']+' unchanged polling resource bounds')
  for field in ['wall_seconds','cpu_seconds','monitor_cpu_seconds']:ck(isinstance(s[field],(int,float)) and math.isfinite(s[field]) and s[field]>=0,s['name']+' finite '+field)
 cloneargs=byname['clone']['argv'];ck(all(flag in cloneargs for flag in ['--no-local','--no-hardlinks','--no-checkout','--no-tags','--single-branch']) and cloneargs[-2:]==[str(ROOT),str(CLONE)],'actual local clone isolation argv')
 ck(byname['checkout-pinned-head']['argv'][-4:]==['checkout','--quiet','--detach',HEAD],'actual clone detach frozen HEAD')
 ck(byname['venv']['argv'][-5:]==['-m','venv','--copies','--without-pip',str(CLONE/'.venv')],'new venv copies and no pip')
 ck(receipt['venv']['prefix']==str(CLONE/'.venv') and receipt['venv']['base_prefix']!=receipt['venv']['prefix'],'actual separate venv identity')
 for path,digest in receipt['venv_files_sha256'].items():ck(sha(Path(path))==digest,'venv executable/config hash '+Path(path).name)
 originalpy=Path(receipt['python']['path']);ck(str(originalpy.resolve())==receipt['python']['resolved_path'] and sha(originalpy.resolve())==receipt['python']['sha256'],'original invoking Python still bound')
 jar=CLONE/'.tools/freerouting-2.5.0.jar';oldjar=Path(receipt['cached_dependency']['path']);ck(sha(jar)==sha(oldjar)==receipt['cached_dependency']['sha256'] and jar.stat().st_ino!=oldjar.stat().st_ino,'JAR actual independent verified copy')
 ck(any(a.get('action')=='bootstrap_clone_scratch' and a['path']==str(CLONE/'.runs') and a['created'] is True for a in receipt['actions']),'explicit new clone scratch bootstrap')
 selected=m.qualification('placement-clearance-v1');ck(receipt['selected_qualification']==selected,'explicit fixed placement selector')
 expected=[*network,str(CLONE/'.venv/bin/python'),'-m','autorouter','route',str(CLONE/selected['fixture']),'--output',str(ndir),*selected['argv']]
 ck(byname['route']['argv']==expected and byname['route']['cwd']==str(CLONE),'actual selected route argv/cwd')
 testlog=Path(byname['tests']['log']).read_text();ck(re.search(r'Ran 608 tests in [0-9.]+s',testlog) is not None and testlog.rstrip().endswith('OK'),'actual clean-venv608suite completed OK')
 ck(receipt['doctor']==json.loads(Path(byname['doctor']['log']).read_text()) and receipt['doctor']['ready'] is True,'raw doctor matches summary and ready')
 ck(sha(nativepath)==receipt['native_receipt']['sha256'],'native receipt exact binding')
 m.verify_native_contract(n,selected,source,HEAD);ck(True,'fresh native schema3 contract fixed parameters')
 ck(n['candidate_sha256']==sha(candidate)=='6f3b180c431773fed2d7308bf562b2d3f3f40094418cf650a22e50b633a62597','exact emitted candidate SHA')
 ck(n['tools']['git_head']==HEAD and all(sha(CLONE/name)==digest for name,digest in n['tools']['implementation_sha256'].items()),'native receipt implementation/head belongs to clone')
 for path,digest in n['tools']['files'].items():ck(sha(Path(path))==digest,'actual pinned native tool '+Path(path).name)
 ck(p.tree_hash(source.parent)==n['source_hashes']==p.tree_hash(ndir/'snapshot'),'complete native source/snapshot unchanged')
 ck(p.immutable(sx.read(source))==p.immutable(sx.read(candidate)),'candidate immutable geometry/zone/rules semantics')
 expected=dict(n['source_hashes']);expected[candidate.name]=n['candidate_sha256'];ck(p.tree_hash(candidate.parent)==expected,'candidate complete project files unchanged except board')
 parsed=p.parse_report(ndir/'final-drc.json',candidate.name);ck(parsed==n['native'] and p.native_accepted(parsed),'raw final native parse and central acceptance')
 ck(all(parsed[k]==0 for k in ['opens','blocking','warnings','exclusions']) and parsed['findings']==[],'all required native counters/findings zero')
 ck(sha(ndir/'final-drc.json')==n['native_report_sha256'],'raw final DRC hash')
 ck(read(ndir/'metrics.json')==n['metrics'] and n['metrics']['vias']==1 and abs(n['metrics']['track_length_mm']-67.93373808491306)<1e-10,'raw metrics1via67.933738mm')
 ck(f.evidence_inventory(ndir)==n['floor_evidence_hashes'],'whole native evidence inventory still exact')
 outputs,policy=pc.derive_chain(ndir,source.name,n['source_hashes']);ck(policy==read(ndir/'placement-policy.json'),'same-load placement/floor/planning policy rederivation')
 for name,raw in outputs.items():ck((ndir/name).read_bytes()==raw,'exact derived '+name)
 ck(policy['removal']['removed_count']==2 and policy['removal']['unmatched_entries_ast_identical'] is True and policy['native_rules_changed'] is False,'only two all-allowed placement export obstacles removed')
 task=g.task_from_source(sx.read(source));context=g.qualify(read(candidate.with_suffix('.kicad_pro')),read(ndir/'floor-final-context.json'),task);generated=g.audit_generated_routes(sx.read(candidate),context);native_routes=g.audit_native_routes(sx.read(candidate),read(ndir/'floor-final-context.json'));ck(True,'independent pure generated widths/vias + native geometry match original derived floors')
 for step in n['steps']:
  raw=read(ndir/(step['name']+'-process.json'));ck(all(step[k]==v for k,v in raw.items()),'native retained process '+step['name'])
 ck(n['engine_budget']['argv']==['--router.autorouter.max_passes=30','--router.job_timeout=00:00:18','--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0','--router.optimizer.enabled=false','--router.scoring.via_costs=50','--router.scoring.plane_via_costs=5'],'actual strict width/fanout/default scoring/internal18s settings')
 fresh=[]
 for i in range(8):
  st=read(RUN/f'freshness-{i}.json');repo=ROOT if i%4<2 else CLONE;tail=['status','--porcelain=v1','--untracked-files=all'] if i%2==0 else ['rev-parse','HEAD'];expected=[*network,'git','-C',str(repo),'-c','core.hooksPath=/dev/null',*tail];log=RUN/f'freshness-{i}.log'
  ck(st['argv']==expected and st['cwd']==str(RUN) and st['status']=='success' and st['exit_code']==0 and st['cleanup_complete'] is True,'final Git observation '+str(i))
  ck(st['log']==str(log) and st['log_sha256']==sha(log) and log.read_text().strip()==('' if i%2==0 else HEAD),'final Git raw output/hash '+str(i));fresh.append(st)
 ck(m.git_identity(CLONE,HEAD,None)==receipt['git_identity_witnesses'][str(CLONE)],'current clone Git HEAD/ref/index witness exact; root clean witness historical')
 ck(abs(receipt['command_cpu_seconds']-sum(s['cpu_seconds']+s['monitor_cpu_seconds'] for s in commands))<1e-9,'command CPU arithmetic exact')
 ck(0<receipt['wall_seconds']<600 and receipt['total_cpu_seconds']>=receipt['command_cpu_seconds'],'installation sampled wall and CPU sane; CPU not a600s cap')
 ck(0<n['wall_seconds']<=n['budget_seconds']==60 and 0<n['total_cpu_seconds']<=n['cpu_budget_seconds']==60,'native60s wall/CPU acceptance caps')
 ck(read(HERE/'fresh-readback-001.log')['current'] is True and read(HERE/'fresh-readback-001.log')['candidate_sha256']==sha(candidate),'independent fresh clone-cwd pure readback passed')
 current_after=m.tracked_inventory(ROOT,listing)
 ck(all(current_after[k]==inv[k] for k in inv if k not in allowed_docs) and m.tracked_inventory(CLONE,clone_listing)==inv,'runtime/source except declared reporting changes and clone exact after audit')
 public=ROOT/'evidence/installation-006';public_files=read(public/'files.json');public_bytes=0
 for name,entry in public_files.items():
  original=ndir/name[7:] if name.startswith('native/') else RUN/name
  ck(sha(public/name)==sha(original)==entry['sha256'] and (public/name).stat().st_size==entry['bytes'],'selected public bytes '+name);public_bytes+=entry['bytes']
 ck(len(public_files)==162 and public_bytes==1013799,'complete compact public selection count/bytes')
 for name,entry in read(public/'omissions.json').items():ck(sha(RUN/name)==entry['sha256'] and (RUN/name).stat().st_size==entry['bytes'] and not (public/name).exists(),'honest full inventory/NUL log omission '+name)
 outer=read(ROOT/'.runs/installation-006-execution.json');outerlog=ROOT/'.runs/installation-006-command.log';wrapper=ROOT/'.runs/run-installation-006.py'
 ck(outer['git_head']==HEAD and outer['cwd']==str(ROOT) and outer['exit_code']==0 and outer['cleanup_signals']==[],'complete external installer wrapper exit0 without cleanup signal')
 ck(outer['argv']==['python3','-B','scripts/install_smoke.py','--output','.runs/installation-006','--guidance','placement-clearance-v1'],'outer exact installation selector')
 ck(sha(outerlog)==outer['log_sha256'] and outerlog.stat().st_size==outer['log_bytes'] and sha(wrapper)==outer['wrapper_sha256'],'outer wrapper and process log bindings')
 ck(receipt['wall_seconds']<outer['wall_seconds']<600 and receipt['total_cpu_seconds']<outer['waited_child_cpu_seconds'],'full external elapsed and waited CPU include later publication work')
 wrong=read(ROOT/'.runs/installation-006-root-readback.json');ck(wrong=={'current':False,'reason':'floor process provenance differs: floor-export'},'wrong root-cwd checker invocation retained as provenance rejection')
 after,total_after=run_inventory();ck(after==before and total_after==total_before,'entire completed installation including clone/venv/native unchanged during audit')
 result={'schema':1,'passed':all(x['passed'] for x in checks),'scope':'Independent completed actual installation readback; this audit performs no native/engine/install/network work','checks':checks,'run':str(RUN),'receipt_sha256':sha(RUN/'result.json'),'git_head':HEAD,'tracked_files':len(inv),'tracked_bytes':tracked_bytes,'complete_run_files':len(before),'current_complete_run_bytes':total_after,'recorded_scratch_bytes_pre_final_publication':receipt['scratch_bytes'],'installation_stored_wall_seconds':receipt['wall_seconds'],'installation_stored_total_cpu_seconds':receipt['total_cpu_seconds'],'installation_stored_command_cpu_seconds':receipt['command_cpu_seconds'],'final_git_cpu_seconds_additional_observations':sum(s['cpu_seconds']+s['monitor_cpu_seconds'] for s in fresh),'accounting_scope':receipt['accounting_point'],'native_candidate_sha256':sha(candidate),'native_wall_seconds':n['wall_seconds'],'native_total_cpu_seconds':n['total_cpu_seconds'],'native_metrics':n['metrics'],'native_counts':{k:parsed[k] for k in ['opens','blocking','warnings','exclusions']},'generated_dimensions':generated,'native_route_geometry':native_routes,'frozen_clone_and_run_unchanged':True,'postrun_source_reporting_differences':source_differences,'selected_public_files':len(public_files),'selected_public_bytes':public_bytes,'root_wrong_cwd_readback':read(ROOT/'.runs/installation-006-root-readback.json'),'outer_execution':outer,'limitations':['One owned placement fixture, no ordinary copper zone, not a large-board comparison or all native negatives/cancellation repeated.','Fresh local clone/venv on existing Mac with installed KiCad/Java/basePython and cached pinned engine reused; no download, package, freshOS or GUI qualification.','Stored installation timing precedes final publication/freshness. Exact external wrapper separately measured full installer elapsed and waited-child CPU; no installation CPU ceiling is claimed.','Mutable local evidence consistency, not authentication or physical/electrical validation.'],'audit_wall_seconds':time.monotonic()-started,'native_jobs_in_this_audit':0,'engine_jobs_in_this_audit':0}
 (HERE/'input-inventory-summary.json').write_text(json.dumps({'files':len(before),'bytes':total_before,'canonical_inventory_sha256':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'same_after':before==after},indent=2,sort_keys=True)+'\n');(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key] for key in ['passed','tracked_files','tracked_bytes','complete_run_files','current_complete_run_bytes','native_candidate_sha256','native_counts','audit_wall_seconds']},indent=2))
if __name__=='__main__':main()
