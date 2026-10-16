"""Finite installed class controls using existing product and validation helpers."""
import json,resource,sys,time,threading,shutil
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();runtime=Path(sys.argv[1]);setup_path=Path(sys.argv[2]);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,review_export as ex,gui,schematic_class_evidence as classes,sexpr as sx
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
setup=f.read_json(setup_path);tools=p.tool_manifest();assert tools['git_head']==setup['source_head']
out=runtime/'.runs/class-controls-001';out.mkdir();owner={};h.capture_destination(owner,out);pin=p.sha(Path(__file__))
extra_sources={}
record=dict(schema=1,accepted=False,controls_passed=False,status='failed',actual_GUI=False,human_review=False,tools=tools,controller_sha256=pin,checks=[],whole_wall_full_CPU_budget_seconds=240,
 scope='Plain no-class/no-preferences and clean-field direct API Route/review/test intent/fresh Native export; actual mismatched class refusal before engine; actual CLI engine cancellation via CliJob; stored-proof tampering controls against prior matching accepted Native output. Exposed owned one-family controls, not comparison or added completion.')
def check(name,**values):record['checks'].append(dict(name=name,passed=True,**values))
def remaining():return min(238-(time.monotonic()-START),238-(cpu()-CPU0))
def stable():
 assert remaining()>0 and p.sha(Path(__file__))==pin and p.tool_manifest()==tools
 assert h.owned_destination(owner)==out
 for item in setup['sources'].values():assert p.tree_hash(Path(item['board']).parent)==item['source_hashes']
 for folder,digest in extra_sources.items():assert p.tree_hash(folder)==digest
 for name,module in tuple(sys.modules.items()):
  if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(runtime),name
def refusal(name,receipt,mutator):
 before=receipt.read_bytes();data=f.read_json(receipt)
 try:
  mutator(data);p.save_json(receipt,data)
  try:p.check_result(receipt)
  except(Exception)as exc:check(name,exception=type(exc).__name__,reason=str(exc))
  else:raise AssertionError('invalid stored Native proof was accepted: '+name)
 finally:receipt.write_bytes(before)
 assert p.check_result(receipt)['current']is True
try:
 stable();board=Path(setup['sources']['clean-fields']['board'])
 route=p.route(board,out/'clean-route',seconds=90,adapter='both')
 assert route['accepted']is True,route.get('reason')
 assert route['native']['warnings']==0 and route['native']['blocking']==0 and route['native']['opens']==0
 assert len(route['protected_route_import']['matches'])==10
 names=[s['name']for s in route['steps']]
 assert names.index('task-classes-netlist')<names.index('engine')<names.index('final-classes-netlist')
 assert not any('fields-'in name for name in names)
 assert p.check_result(out/'clean-route/result.json')['current']is True
 review=h.review_copy(out/'clean-route/result.json',out/'clean-review',render=False)
 choice=h.review_choice(out/'clean-review/review.json',out/'clean-choice','accept')
 export=ex.export(out/'clean-choice/choice.json',out/'clean-export',min(120,remaining()))
 assert export['export_accepted']is True and export['native']['warnings']==0 and ex.check_export(out/'clean-export/export.json')['current']is True
 assert 'final-classes-netlist'in[s['name']for s in export['steps']]
 check('actual_clean_field_direct_route_and_fresh_export',route_sha256=p.sha(out/'clean-route/result.json'),export_sha256=p.sha(out/'clean-export/export.json'),native=route['native'],metrics=route['metrics'],route_steps=names,export_steps=[s['name']for s in export['steps']]);stable()
 # Completion control deliberately starts from the owned complete candidate:
 # every original route, including unlocked engine-added copper, is protected.
 partial_source=out/'partial-source';shutil.copytree(Path(route['candidate']).parent,partial_source)
 extra_sources[partial_source]=p.tree_hash(partial_source);partial_board=partial_source/board.name
 partial=p.route(partial_board,out/'partial-route',seconds=90,keep_existing=True,adapter='both')
 expected_protected=len(p.routes(sx.read(partial_board)))
 assert expected_protected>10 and partial['accepted']is True,partial.get('reason')
 assert partial['scope']=='partial_completion'and len(partial['protected_route_import']['matches'])==expected_protected
 assert p.check_result(out/'partial-route/result.json')['current']is True
 h.review_copy(out/'partial-route/result.json',out/'partial-review',render=False)
 h.review_choice(out/'partial-review/review.json',out/'partial-choice','accept')
 partial_export=ex.export(out/'partial-choice/choice.json',out/'partial-export',min(120,remaining()))
 assert partial_export['export_accepted']is True and ex.check_export(out/'partial-export/export.json')['current']is True
 check('actual_partial_completion_preserves_locked_and_unlocked_original_copper',protected_routes=expected_protected,source_sha256=extra_sources[partial_source],route_sha256=p.sha(out/'partial-route/result.json'),export_sha256=p.sha(out/'partial-export/export.json'),native=partial['native'],metrics=partial['metrics']);stable()

 # This ordinary API call has neither preferences nor class intent: the
 # formerly unguarded publication branch must complete actual Native delivery.
 plain_board=Path(setup['sources']['plain']['board'])
 plain=p.route(plain_board,out/'plain-route',seconds=90,adapter='both')
 assert plain['accepted']is True,plain.get('reason')
 assert plain['native']['opens']==plain['native']['blocking']==0
 assert not any('classes-netlist'in s['name']for s in plain['steps'])
 assert 'routing_preferences'not in plain and 'schematic_class_task'not in plain
 assert p.check_result(out/'plain-route/result.json')['current']is True
 h.review_copy(out/'plain-route/result.json',out/'plain-review',render=False)
 h.review_choice(out/'plain-review/review.json',out/'plain-choice','accept')
 plain_export=ex.export(out/'plain-choice/choice.json',out/'plain-export',min(120,remaining()))
 assert plain_export['export_accepted']is True and ex.check_export(out/'plain-export/export.json')['current']is True
 check('actual_plain_no_preferences_no_class_route_and_fresh_export',route_sha256=p.sha(out/'plain-route/result.json'),export_sha256=p.sha(out/'plain-export/export.json'),native=plain['native'],metrics=plain['metrics'],protected_routes=1);stable()

 bad=p.route(Path(setup['sources']['mismatch']['board']),out/'mismatch-route',seconds=min(90,remaining()),adapter='both')
 assert bad['accepted']is False and 'class_identity_mismatch'in bad.get('reason',''),bad.get('reason')
 assert not any(s['name']=='engine'for s in bad['steps'])and not(out/'mismatch-route/engine.log').exists()
 check('actual_class_mismatch_refuses_before_engine',reason=bad['reason'],receipt_sha256=p.sha(out/'mismatch-route/result.json'),steps=[s['name']for s in bad['steps']]);stable()
 prior=runtime/'.runs/qualification-matching/result.json';matching=f.read_json(prior)
 receipt=Path(matching['workspace'])/'route/result.json'
 assert p.check_result(receipt)['current']is True
 refusal('dropped_both_class_proofs',receipt,lambda d:(d.pop('schematic_class_task'),d.pop('schematic_class_final')))
 refusal('downgraded_final_proof',receipt,lambda d:d.__setitem__('schematic_class_final',None))
 proof=receipt.parent/'final-classes-proof.json';before=proof.read_bytes()
 try:
  proof.write_bytes(before+b'\n')
  try:p.check_result(receipt)
  except(Exception)as exc:check('changed_class_proof_bytes',reason=type(exc).__name__+': '+str(exc))
  else:raise AssertionError('stale class proof passed')
 finally:proof.write_bytes(before)
 assert p.check_result(receipt)['current']is True;stable()
 # Real bounded CLI cancellation; only this owned child is signalled by CliJob.
 job=gui.CliJob();cancel_out=out/'cancel-route';observed={};done=threading.Event()
 def cancel_engine():
  deadline=time.monotonic()+min(60,remaining()-3)
  while not done.is_set()and time.monotonic()<deadline:
   log=cancel_out/'engine.log'
   if log.is_file()and log.stat().st_size>0 and not(cancel_out/'engine-process.json').exists():
    observed.update(stage='engine',log_bytes=log.stat().st_size);job.cancel();return
   done.wait(.01)
 thread=threading.Thread(target=cancel_engine);thread.start()
 try:process=job.run([str(runtime/'.venv/bin/python'),'-B','-m','autorouter','route',str(board),'--seconds','90','--adapter','both','--output',str(cancel_out)],out/'cancel-cli.log',timeout=max(1,min(100,remaining())))
 finally:done.set();thread.join(3)
 assert not thread.is_alive()and observed.get('stage')=='engine'and process['cancel_requested']is True
 cancelled=f.read_json(cancel_out/'result.json')
 assert cancelled['accepted']is False and cancelled['status']=='cancelled'
 assert all(s.get('cleanup_complete')is True for s in cancelled['steps'])
 assert not any(s['name']=='final-classes-netlist'for s in cancelled['steps'])
 try:p.check_result(cancel_out/'result.json')
 except(Exception)as exc:cancel_reason=type(exc).__name__+': '+str(exc)
 else:raise AssertionError('cancelled output passed')
 check('actual_engine_cancel_no_fallback',observation=observed,process=process,receipt_sha256=p.sha(cancel_out/'result.json'),reason=cancel_reason,steps=cancelled['steps']);stable()
 record.update(controls_passed=True,status='completed')
except(Exception,KeyboardInterrupt)as exc:record.update(controls_passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
try:stable()
except BaseException as exc:record.update(controls_passed=False,status='freshness_failed',error=str(exc))
record.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,publication_allowance_seconds=2,external_exit_required=True)
if max(record['sampled_wall_seconds'],record['sampled_full_CPU_seconds'])+2>240:record.update(controls_passed=False,status='budget_exceeded')
p.save_json(out/'result.json',record);print(json.dumps(dict(controls_passed=record['controls_passed'],status=record['status'],error=record.get('error'),checks=[x['name']for x in record['checks']])))
raise SystemExit(0 if record['controls_passed']else 2)
