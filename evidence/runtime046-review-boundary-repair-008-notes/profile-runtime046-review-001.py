"""One bounded actual failed review profile; no source/receipt edit or pass claim."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,gui
from autorouter.runner import run
runtime=R/'.runs/runtime-directory-046/runtime';child=f.read_json(runtime/'.runs/improve-fractional-001/result.json');receipt=Path(child['workspace'])/'route/result.json';assert child['workflow_delivered'] is False
out=R/'.runs/runtime046-review-profile-001';out.mkdir(mode=0o700);target=runtime/'.runs/native7-review-profile-001';assert not target.exists()
code='''import cProfile,pstats,io,json,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1]);sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,local_settings as local
runtime,receipt,out,target=map(Path,sys.argv[1:]);before=f.evidence_inventory(receipt.parent);data=f.read_json(receipt);source=Path(data['source']);hashes=p.tree_hash(source.parent);tools=p.tool_manifest();start=time.monotonic();prof=cProfile.Profile();prof.enable();error=None
try:h.review_copy(receipt,target,render=True)
except p.Rejected as exc:error=str(exc)
finally:prof.disable()
assert error and '30-second' in error and f.evidence_inventory(receipt.parent)==before and p.tree_hash(source.parent)==hashes and p.tool_manifest()==tools
prof.dump_stats(str(out/'review.prof'));stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(65);(out/'cumulative.txt').write_text(stream.getvalue());(out/'result.json').write_text(json.dumps(dict(accepted=False,error=error,receipt_sha256=p.sha(receipt),profiled_review_wall_seconds=time.monotonic()-start,evidence_unchanged=True,source_unchanged=True,memo=dict(local._cached_policy_declarations.cache_info()._asdict()),scope='Actual installed046 review diagnostic under cProfile, including any plot workers. Existing30s refusal mandatory; not GUI/delivery qualification.')))
'''
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-c',code,str(runtime),str(receipt),str(out),str(target)],cwd=out,env=gui.child_environment(),log=out/'command.log',timeout=75,max_log_bytes=128*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=16*1024**2);p.save_json(out/'process.json',process);print({key:process[key] for key in ('status','exit_code','wall_seconds','cpu_seconds','cleanup_complete','log_truncated')});raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] else 2)
