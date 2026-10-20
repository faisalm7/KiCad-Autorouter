"""One frozen current-build check through the existing cancellation controller."""
from pathlib import Path
import datetime, json, os, resource, sys, time
START = time.monotonic()
def cpu():
    return sum(r.ru_utime + r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
from autorouter.runner import run
runtime = ROOT / '.runs/runtime-directory-056/runtime'
prior_path = ROOT / '.runs/runtime056-native-qualification-001/improve-floor2Cu/protocol.json'
prior = f.read_json(prior_path)
assert prior['runtime'] == str(runtime)
assert p.sha(runtime / 'runtime-distribution.json') == prior['runtime_manifest_sha256'] == 'b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded'
source = Path(prior['source'])
assert io.inventory(source.parent) == prior['source_hashes']
controller = ROOT / '.runs/qualify-runtime049-cancel-002.py'
assert p.sha(controller) == '9af30b08f2bb31b12ee6a68cde253bb465880b1bcc2bee6f3a08a67ebf4cb7fb'
p.check_storage()
base = ROOT / '.runs/runtime056-cancellation-001'
out = runtime / '.runs/native7-control-runtime056-cancel-001'
assert not base.exists() and not out.exists()
base.mkdir(mode=0o700)
protocol = base / 'protocol.json'
plan = dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), runtime=str(runtime), source=str(source), output=str(out), administration=str(ROOT), runtime_manifest_sha256=prior['runtime_manifest_sha256'], controller_sha256=p.sha(controller), source_hashes=prior['source_hashes'], source_protocol_sha256=p.sha(prior_path), enclosure_sha256=p.sha(Path(__file__)), scope='One current056 Improve incumbent-engine SIGINT check through unchanged production CliJob; no actual GUI, all-phase cancellation, final-route acceptance, electrical or release claim.')
p.save_json(protocol, plan); pin = p.sha(protocol)
env = {k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
process = run([*f.SANDBOX, str(runtime/'.venv/bin/python'), '-B', str(controller), '--protocol', str(protocol), '--protocol-sha256', pin], cwd=base, log=base/'command.log', env=env, timeout=130, max_log_bytes=512*1024, max_group_rss_bytes=4*1024**3, max_workdir_bytes=512*1024**2)
p.save_json(base/'process.json', process)
child = out/'result.json'
record = f.read_json(child) if child.is_file() else None
wall, cost = time.monotonic()-START, cpu()-CPU0
stable = p.sha(protocol)==pin and p.sha(controller)==plan['controller_sha256'] and p.sha(Path(__file__))==plan['enclosure_sha256'] and io.inventory(source.parent)==prior['source_hashes'] and p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
passed = bool(record and record['control_passed'] is True and record['status']=='completed' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated'] and stable and max(wall,cost)<=120)
p.save_json(base/'execution.json', dict(schema=1, control_passed=passed, accepted=False, project_complete=False, actual_GUI=False, human_review=False, protocol_sha256=pin, child=str(child), child_sha256=p.sha(child) if record else None, process=process, complete_wall_seconds=wall, complete_full_CPU_seconds=cost, stable=stable, scope=plan['scope']))
print(json.dumps(dict(control_passed=passed, wall_seconds=wall, CPU_seconds=cost, child_status=record.get('status') if record else None)))
raise SystemExit(0 if passed else 2)
