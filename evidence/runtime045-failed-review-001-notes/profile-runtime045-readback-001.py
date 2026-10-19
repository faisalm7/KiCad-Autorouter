"""One bounded real readback profile; no product monkeypatch or Native routing."""
from pathlib import Path
import os,sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,gui
from autorouter.runner import run
runtime=R/'.runs/runtime-directory-045/runtime';positive=runtime/'.runs/improve-fractional-001';child=f.read_json(positive/'result.json');receipt=Path(child['workspace'])/'route/result.json';assert child['workflow_delivered'] is False
out=R/'.runs/runtime045-readback-profile-001';out.mkdir(mode=0o700)
code='''import cProfile,pstats,io,json,sys,time,resource
from pathlib import Path
sys.path.insert(0,sys.argv[1]);sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
runtime,receipt,out=map(Path,sys.argv[1:]);before=f.evidence_inventory(receipt.parent);data=f.read_json(receipt);source=Path(data['source']);hashes=p.tree_hash(source.parent);tools=p.tool_manifest();start=time.monotonic();prof=cProfile.Profile();prof.enable();checked=p.check_result(receipt);prof.disable();elapsed=time.monotonic()-start
assert checked['current'] and f.evidence_inventory(receipt.parent)==before and p.tree_hash(source.parent)==hashes and p.tool_manifest()==tools
prof.dump_stats(str(out/'readback.prof'));stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(65);(out/'cumulative.txt').write_text(stream.getvalue());stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('tottime').print_stats(35);(out/'self.txt').write_text(stream.getvalue());(out/'result.json').write_text(json.dumps(dict(current=True,receipt_sha256=p.sha(receipt),readback_wall_seconds=elapsed,evidence_unchanged=True,source_unchanged=True,scope='cProfile instrumentation cost is included; readback-only diagnostic, no delivered workflow')))
'''
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-c',code,str(runtime),str(receipt),str(out)],cwd=out,env=gui.child_environment(),log=out/'command.log',timeout=90,max_log_bytes=128*1024,max_group_rss_bytes=2*1024**3,max_workdir_bytes=16*1024**2);p.save_json(out/'process.json',process);print(json.dumps({key:process[key] for key in ('status','exit_code','wall_seconds','cpu_seconds','cleanup_complete','log_truncated')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] else 2)
