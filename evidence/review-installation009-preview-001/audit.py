"""Finite offline adaptation of review-installation-006 audit; no native execution."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
RUN=ROOT/'.runs/installation-009'; CLONE=RUN/'checkout'; REVIEW=CLONE/'.runs/install-review-preview-001'
HEAD='339e539600798a221f423a7e70b53242f17a062f'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as pc, floor_route as f, sexpr as sx, review_view as rv
spec=importlib.util.spec_from_file_location('installer_audit',ROOT/'scripts/install_smoke.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def ck(value,label):
 checks.append({'check':label,'passed':bool(value)})
 if not value:raise AssertionError(label)
def read(path):return m.read_json(path)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def entry(path):return {'bytes':path.stat().st_size,'sha256':sha(path)}
def inventory():
 # Existing installation006 bounded traversal, enlarged only to match source cap.
 result={};total=0;count=0
 for parent,dirs,files in os.walk(RUN,followlinks=False):
  for name in list(dirs)+files:
   count+=1
   if count>40000:raise ValueError('audit entry ceiling')
   path=Path(parent)/name;rel=str(path.relative_to(RUN))
   if path.is_symlink():
    result[rel]={'symlink':os.readlink(path)}
    if name in dirs:dirs.remove(name)
   elif path.is_file():
    total+=path.stat().st_size
    if total>512*1024**2 or len(result)>=20000:raise ValueError('audit payload ceiling')
    result[rel]=entry(path)
 return result,total

def main():
 started=time.monotonic();before,total=inventory()
 failed_paths=[ROOT/'.runs/installation-008/result.json',ROOT/'.runs/installation-008/13-tests.log']
 failed_before={str(path):entry(path) for path in failed_paths}
 r=read(RUN/'result.json');v=read(REVIEW/'review.json');inv=read(RUN/'source-tracked.json');commands=r['commands'];steps={s['name']:s for s in commands};npath=Path(r['native_receipt']['path']);nd=npath.parent;n=read(npath);source=Path(n['source']);candidate=Path(n['candidate'])
 ck(r['passed'] is True and r['status']=='passed' and r['git_head']==HEAD and len(commands)==len(steps)==20,'canonical installation pass, exact HEAD, 20 distinct commands')
 ck(r['limits']['source_bytes']==256*1024**2 and r['limits']['source_files']==16000 and r['limits']['scratch_bytes']==512*1024**2 and r['limits']['wall_seconds']==600,'bounded capacity and unchanged scratch/wall')
 listing=Path(steps['source-files']['log']).read_text();ck(listing==Path(steps['clone-files']['log']).read_text(),'identical complete source and clone tracked lists')
 ck(m.tracked_inventory(ROOT,listing)==m.tracked_inventory(CLONE,listing)==inv,'source and clone complete tracked-byte inventories still exact')
 ck(sha(RUN/'source-tracked.json')==r['source_inventory_sha256'],'source inventory hash matches receipt')
 tracked_bytes=sum((CLONE/name).stat().st_size for name in inv);ck(len(inv)<=16000 and tracked_bytes<=256*1024**2,'actual tracked source inside caps')
 for root in (ROOT,CLONE):
  branch=r['source_branch'] if root==ROOT else None
  ck(m.git_identity(root,HEAD,branch)==r['git_identity_witnesses'][str(root)],'read-only HEAD/ref/index witness '+str(root))
 network=m.NETWORK_DENIAL
 for s in commands:
  ck(s['argv'][:3]==network and s['status']=='success' and s['exit_code']==0 and s['cleanup_complete'] is True and not s['log_truncated'],s['name']+' successful bounded network-denied command')
  log=Path(s['log']);ck(log.parent==RUN and sha(log)==s['log_sha256'] and log.stat().st_size==s['log_bytes'],s['name']+' raw log bound')
  ck(s['resource_guards']['max_group_rss_bytes']==4*1024**3 and s['resource_guards']['max_workdir_bytes']==512*1024**2,s['name']+' unchanged polling guards')
 ck(all(flag in steps['clone']['argv'] for flag in ['--no-local','--no-hardlinks','--no-checkout','--no-tags','--single-branch']) and steps['clone']['argv'][-2:]==[str(ROOT),str(CLONE)],'local clone independent files and selected source')
 ck(steps['checkout-pinned-head']['argv'][-4:]==['checkout','--quiet','--detach',HEAD],'exact detached clone commit')
 ck(steps['venv']['argv'][-5:]==['-m','venv','--copies','--without-pip',str(CLONE/'.venv')],'fresh copied venv without pip')
 ck(r['venv']['prefix']==str(CLONE/'.venv') and r['venv']['base_prefix']!=r['venv']['prefix'],'separate actual venv')
 for name,digest in r['venv_files_sha256'].items():ck(sha(Path(name))==digest,'venv executable/config '+Path(name).name)
 py=Path(r['python']['path']);ck(str(py.resolve())==r['python']['resolved_path'] and sha(py.resolve())==r['python']['sha256'],'original supervisor Python exact')
 jar=CLONE/'.tools/freerouting-2.5.0.jar';originaljar=Path(r['cached_dependency']['path']);ck(sha(jar)==sha(originaljar)==r['cached_dependency']['sha256'] and jar.stat().st_ino!=originaljar.stat().st_ino,'verified independent cached JAR copy')
 ck(r['doctor']==read(Path(steps['doctor']['log'])) and r['doctor']['ready'] is True,'doctor raw output matches')
 testlog=Path(steps['tests']['log']).read_text();ck(bool(re.search(r'Ran 643 tests in [0-9.]+s\n\nOK\s*$',testlog)),'actual 643-test clone suite passed')
 selected=m.qualification('placement-clearance-v1');ck(r['selected_qualification']==selected,'fixed native qualification selector')
 ck(steps['route']['argv']==[*network,str(CLONE/'.venv/bin/python'),'-m','autorouter','route',str(CLONE/selected['fixture']),'--output',str(nd),*selected['argv']] and steps['route']['cwd']==str(CLONE),'exact actual native route argv/cwd')
 ck(sha(npath)==r['native_receipt']['sha256'],'bound final native receipt')
 m.verify_native_contract(n,selected,source,HEAD)
 ck(n['tools']['git_head']==HEAD and all(sha(CLONE/name)==digest for name,digest in n['tools']['implementation_sha256'].items()),'native code belongs to exact installed clone')
 for name,digest in n['tools']['files'].items():ck(sha(Path(name))==digest,'native tool still pinned '+Path(name).name)
 ck(p.tree_hash(source.parent)==n['source_hashes']==p.tree_hash(nd/'snapshot'),'complete source and snapshot unchanged')
 expected=dict(n['source_hashes']);expected[candidate.name]=n['candidate_sha256'];ck(p.tree_hash(candidate.parent)==expected and sha(candidate)==n['candidate_sha256'],'candidate complete original project with only authorized board replacement')
 ck(p.immutable(sx.read(source))==p.immutable(sx.read(candidate)),'source immutable geometry/zone/rules preserved')
 parsed=p.parse_report(nd/'final-drc.json',candidate.name)
 ck(parsed==n['native'] and p.native_accepted(parsed) and all(parsed[k]==0 for k in ('opens','blocking','warnings','exclusions')),'raw final DRC counts and central acceptance')
 ck(sha(nd/'final-drc.json')==n['native_report_sha256'] and read(nd/'metrics.json')==n['metrics'],'final raw native report and metrics hash bindings')
 ignored=[x['key'] for x in parsed['ignored_checks']];original_settings=read(source.with_suffix('.kicad_pro'))['board']['design_settings']['rule_severities']
 explicit_ignored={k for k,value in original_settings.items() if value=='ignore'}
 ck(len(ignored)==7 and len(explicit_ignored)==5 and set(ignored)-explicit_ignored=={'track_not_centered_on_via','tuning_profile_track_geometries'} and parsed['ignored_checks']==n['source_drc']['ignored_checks'],'five explicit ignored settings plus two native defaults unchanged from source DRC')
 ck(f.evidence_inventory(nd)==n['floor_evidence_hashes'],'full routing evidence inventory')
 for s in n['steps']:
  process=read(nd/(s['name']+'-process.json'));ck(all(s[k]==value for k,value in process.items()),'native retained process '+s['name'])
 argv=[*network,str(CLONE/'.venv/bin/python'),'-B','-m','autorouter','check-result',str(npath)]
 t=time.monotonic();fresh=subprocess.run(argv,cwd=CLONE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=30)
 (HERE/'fresh-readback.log').write_text(fresh.stdout);(HERE/'fresh-readback.stderr').write_text(fresh.stderr)
 (HERE/'fresh-readback-process.json').write_text(json.dumps({'argv':argv,'cwd':str(CLONE),'exit_code':fresh.returncode,'wall_seconds':time.monotonic()-t,'native_or_engine_executed':False},indent=2)+'\n')
 ck(fresh.returncode==0 and json.loads(fresh.stdout)['current'] is True and json.loads(fresh.stdout)['candidate_sha256']==n['candidate_sha256'],'fresh clone-cwd central readback')
 for i in range(8):
  s=read(RUN/f'freshness-{i}.json');log=RUN/f'freshness-{i}.log';repo=ROOT if i%4<2 else CLONE;tail=['status','--porcelain=v1','--untracked-files=all'] if i%2==0 else ['rev-parse','HEAD']
  ck(s['argv']==[*network,'git','-C',str(repo),'-c','core.hooksPath=/dev/null',*tail] and s['cwd']==str(RUN) and s['exit_code']==0 and s['status']=='success' and s['cleanup_complete'] is True and sha(log)==s['log_sha256'] and log.read_text().strip()==('' if i%2==0 else HEAD),'saved final source/clone Git observation '+str(i))
 ck(abs(r['command_cpu_seconds']-sum(s['cpu_seconds']+s['monitor_cpu_seconds'] for s in commands))<1e-9,'command CPU arithmetic')
 ck(v['status']=='ready_for_manual_review' and v['within_budget'] is True and v['native_validation_performed'] is False and v['input_policy']=='placement-clearance-v1' and v['source_receipt_schema']==3,'preview readiness is separate from native acceptance')
 ck(v['receipt']==str(npath) and v['receipt_sha256']==sha(npath) and v['candidate_sha256']==v['verified_candidate_sha256']==n['candidate_sha256'],'preview receipt/candidate exact')
 ck(pc.inventory(Path(v['project']))==v['initial_project_hashes']==expected and pc.inventory(REVIEW/'before')==v['source_project_hashes']==n['source_hashes'],'advertised before/after complete copies unchanged')
 ck(pc.inventory(nd,max_bytes=100*1024**2,max_files=4000,max_entries=8000)==v['routing_evidence_hashes'],'handoff captured full routing evidence remains exact')
 for name,digest in v['runtime_source_sha256'].items():
  file=Path(name);rel=str(file.relative_to(CLONE));ck(sha(file)==digest==inv[rel],'preview same installed runtime '+rel)
 preview=v['preview'];ck(preview['layers']==['F.Cu','B.Cu'] and len(preview['steps'])==4 and preview['native_validation_performed'] is False and preview['zone_refill_performed'] is False,'four front/back native plots; no fresh refill/DRC')
 ck(preview['plotter_sha256']==sha(p.c.CLI),'actual pinned plotter byte hash')
 for name,digest in preview['files'].items():ck(sha(REVIEW/name)==digest,'preview output binding '+name)
 observations=[]
 for s in preview['steps']:
  name=s['name'];label,layer=name.split('-',1);work=REVIEW/'plot-work'/(name+'-input');native=REVIEW/'plot-work/native-plots'/(name+'.svg');display=REVIEW/'plot-work/plots'/native.name
  advertised=REVIEW/('before' if label=='before' else 'project')/source.name
  ck(s['argv']==[*network,str(p.c.CLI),'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--output',str(native),str(work/source.name)],'exact plot argv '+name)
  ck(s['status']=='success' and s['exit_code']==0 and s['cleanup_complete'] is True and not s['log_truncated'],'actual successful plot '+name)
  process=read(REVIEW/'plot-work'/(name+'-process.json'));ck(all(s[k]==value for k,value in process.items()),'plot process raw '+name)
  binding=read(REVIEW/'plot-work'/(name+'-input-binding.json'));expected_source=v['source_project_hashes'] if label=='before' else v['initial_project_hashes']
  ck(binding['source']==str(advertised) and binding['input']==str(work/source.name) and binding['before']==expected_source and binding['after']==pc.inventory(work)==preview['input_trees'][str(work.relative_to(REVIEW))],'complete plot-copy binding '+name)
  p.check_drc_project(binding['before'],binding['after'],source.name)
  added=set(binding['after'])-set(binding['before']);ck(added=={source.with_suffix('.kicad_prl').name} and all(binding['after'][k]==value for k,value in binding['before'].items()),'only disposable plot PRL addition '+name)
  raw=rv.svg_bytes(native);ck(display.read_bytes()==rv.display_svg(raw) and b'<!DOCTYPE' in raw and b'<!DOCTYPE' not in display.read_bytes(),'native SVG retained and exact display declaration removal '+name)
  ck((REVIEW/'plot-work'/(name+'.log')).read_text()=="Plotted to '"+str(native)+"'.\nDone.\n",'native plot success log '+name)
  observations.append({'name':name,'raw_svg':entry(native),'display_svg':entry(display),'added_plot_copy_files':sorted(added),'wall_seconds':s['wall_seconds'],'cpu_seconds':s['cpu_seconds']})
 html=(REVIEW/'preview.html').read_text();ck(all(x in html for x in ('default-src','Saved validation','does not refill zones or perform DRC')) and all(key in html for key in ignored),'HTML includes scope, CSP and original ignored checks')
 for label,outer_path,wrapper,log in [('installation',ROOT/'.runs/installation-009-execution.json',ROOT/'.runs/run-installation-009.py',ROOT/'.runs/installation-009-command.log'),('preview',ROOT/'.runs/installed-review-preview-001-execution.json',ROOT/'.runs/run-installed-review-preview-001.py',ROOT/'.runs/installed-review-preview-001-command.log')]:
  outer=read(outer_path);ck(outer['git_head']==HEAD and outer['exit_code']==0 and outer['cleanup_signals']==[] and outer['wrapper_sha256']==sha(wrapper) and outer['log_sha256']==sha(log) and outer['log_bytes']==log.stat().st_size,label+' outer wrapper/log execution bindings')
  inner=r if label=='installation' else v;limit=600 if label=='installation' else 30
  ck(0<inner['wall_seconds']<outer['wall_seconds']<limit and 0<inner['total_cpu_seconds']<outer['waited_child_cpu_seconds'],label+' outer accounting includes final work')
  if label=='preview':
   ck(outer['installation_sha256']==sha(RUN/'result.json') and outer['cwd']==str(CLONE) and outer['argv']==[*network,str(CLONE/'.venv/bin/python'),'-B','-m','autorouter','review-copy',str(npath),'--render','--output','.runs/install-review-preview-001'],'exact installed preview wrapper argv')
   ck(read(log)==v,'preview stdout exact canonical review record')
 failed=read(failed_paths[0]);failedlog=failed_paths[1].read_text();ck(failed['passed'] is False and failed['status']=='failed' and failed['reason']=='RuntimeError: tests: nonzero_exit exit=1' and '120000 != 100000' in failedlog and 'FAILED (failures=1)' in failedlog,'installation008 prior stale backup-capacity expectation failure retained')
 after,total_after=inventory();ck(after==before and total_after==total,'entire installation/clone/venv/preview unchanged during audit')
 ck({str(path):entry(path) for path in failed_paths}==failed_before,'failed008 evidence unchanged')
 ck(m.tracked_inventory(ROOT,listing)==m.tracked_inventory(CLONE,listing)==inv,'final source and clone inventories unchanged')
 summary={'schema':1,'passed':True,'checks':checks,'head':HEAD,'tracked_files':len(inv),'tracked_bytes':tracked_bytes,'current_full_installation_bytes':total,'full_inventory_count':len(before),'full_inventory_digest':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'installation_stored_seconds':{'wall':r['wall_seconds'],'cpu':r['total_cpu_seconds'],'scratch_bytes':r['scratch_bytes']},'installation_outer':read(ROOT/'.runs/installation-009-execution.json'),'native':{'candidate_sha256':n['candidate_sha256'],'report_sha256':n['native_report_sha256'],'counts':{k:parsed[k] for k in ('opens','blocking','warnings','exclusions')},'ignored_checks':ignored,'explicit_original_ignored_checks':sorted(explicit_ignored),'effective_native_defaults':sorted(set(ignored)-explicit_ignored),'metrics':n['metrics'],'wall_seconds':n['wall_seconds'],'cpu_seconds':n['total_cpu_seconds']},'preview_stored_seconds':{'wall':v['wall_seconds'],'cpu':v['total_cpu_seconds']},'preview_outer':read(ROOT/'.runs/installed-review-preview-001-execution.json'),'plots':observations,'failed008':failed_before,'audit_wall_seconds':time.monotonic()-started,'native_jobs_started':0,'engine_jobs_started':0}
 (HERE/'audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['passed','tracked_files','tracked_bytes','current_full_installation_bytes','full_inventory_count','audit_wall_seconds']}))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  (HERE/'audit-failure.json').write_text(json.dumps({'error':type(exc).__name__+': '+str(exc),'checks':checks},indent=2)+'\n');raise
