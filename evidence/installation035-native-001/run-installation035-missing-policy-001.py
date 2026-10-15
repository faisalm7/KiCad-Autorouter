"""Current installed Native session controls only; no historical supplement."""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
protocol=ROOT/'.runs/installation035-missing-policy-followup-001/protocol.json';plan=f.read_json(protocol);pin=p.sha(protocol)
installed=ROOT/'.runs/installation-035/checkout';out=ROOT/'.runs/installation035-missing-policy-followup-001';tools=p.tool_manifest();receipt=f.read_json(ROOT/'.runs/installation-035/result.json');rp=p.sha(ROOT/'.runs/installation-035/result.json')
assert tools==plan['tools'] and tools['git_head']==receipt['git_head']==plan['git_head'] and receipt['passed'] is True
assert plan['historical_test_supplement']==f.read_json(out/'fixture-preparation.json')['fixture_files']
assert all(p.sha(ROOT/n)==p.sha(installed/n)==h for n,h in plan['source_sha256'].items())
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(installed/'.venv/bin/python'),'-B','-c',plan['target_bootstrap']],cwd=out,env=env,log=out/'tests.log',timeout=max(.001,90-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3)
population=f.read_json(out/'population.json') if (out/'population.json').is_file() else None
current=p.tool_manifest()==tools and p.sha(protocol)==pin and p.sha(ROOT/'.runs/installation-035/result.json')==rp and all(p.sha(ROOT/n)==p.sha(installed/n)==h for n,h in plan['source_sha256'].items()) and all(p.sha(ROOT/n)==h for n,h in plan['controller_sha256'].items())
wall=time.monotonic()-START;full=cpu()-CPU0
record=dict(schema=1,process=process,source_current=current,git_head=tools['git_head'],modules=plan['target_modules'],population=population,population_sha256=p.sha(out/'population.json') if population else None,protocol_sha256=pin,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'tests.log'),wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_delivery_within_budget=max(wall,full)+2<=92,historical_test_supplement=plan['historical_test_supplement'],scope='Only two previously missing historical-policy installed controls; previous244attempts/242successes/twoerrors retained. One exact committed owned source fixture supplemented after initial distribution. Exact installed source/independentinterpreter, authorednormalPRLfixture, offline andonly exactreadonlyGitHEAD permitted. One declared historical source test supplement; no fullsuite/noNative/JVM/fullinstalledsuite orroutingquality claim; One declared historical source test supplement; no fullsuite/oldinstalledtargets repeated; these changedmodules require currentinstalled qualification.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('source_current','wall_seconds','full_cpu_seconds','population')}));raise SystemExit(0 if current and record['whole_delivery_within_budget'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and population and population['successful'] and population['planned']==population['ran']==plan['expected_target_method_count'] else 2)
