"""Run new preference controls in the actual installed interpreter, offline."""
import time, resource
START = time.monotonic()
def cpu():
    u = resource.getrusage(resource.RUSAGE_SELF)
    c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u.ru_utime + u.ru_stime + c.ru_utime + c.ru_stime
CPU0 = cpu()
from pathlib import Path
import os, sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f
from autorouter.runner import run
out = ROOT / '.runs/installation022-preferences-followup-001'
out.mkdir()
installed = ROOT / '.runs/installation-022/checkout'
env = {k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
argv = [*f.SANDBOX, str(installed / '.venv/bin/python'), '-B', '-m', 'unittest',
        'tests.test_improve_preferences_cli', 'tests.test_pruning_preferences',
        'tests.test_pruning_preferences_freshness', '-v']
process = run(argv, cwd=installed, env=env, log=out/'tests.log', timeout=60,
              max_log_bytes=128*1024, max_workdir_bytes=512*1024**2,
              max_group_rss_bytes=4*1024**3)
record = dict(schema=1, process=process, log_sha256=p.sha(out/'tests.log'),
              controller_sha256=p.sha(Path(__file__)),
              installed_head='e6aacc8d8ff4bf2468bec1e448b262186936d102',
              wall_seconds=time.monotonic()-START, full_cpu_seconds=cpu()-CPU0,
              scope='Actual fresh installation022 venv and installed new preference, CLI and material-freshness regression tests under network denial. Software controls; no new Native execution or quality comparison.')
passed = process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']
record['passed']=passed
p.save_json(out/'execution.json', record)
print(json.dumps({k:record[k] for k in ('passed','wall_seconds','full_cpu_seconds')}))
raise SystemExit(0 if passed else 2)
