"""Current installed chain/strategy/paired software controls; lead execution."""
import time
import resource
START = time.monotonic()
def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
               (resource.getrusage(resource.RUSAGE_SELF),
                resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import sys
import json
import os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f
from autorouter.runner import run

protocol = ROOT / '.runs/installation037-preparation-001/protocol.json'
plan = f.read_json(protocol)
pin = p.sha(protocol)
assert plan['kind'] == 'installation037-targeted-preparation-v1'
assert plan['status'] == 'frozen_for_lead_execution'
assert plan['target_modules'] == ['tests.test_chain_proposals', 'tests.test_strategy', 'tests.test_paired', 'tests.test_storage_scan', 'tests.test_pruning_preferences_freshness']
assert plan['expected_target_method_count'] == 112 and plan['historical_test_supplement'] is None
installed = ROOT / '.runs/installation-037/checkout'
out = ROOT / '.runs/installation037-targeted-001'
out.mkdir()
tools = p.tool_manifest()
receipt_path = ROOT / '.runs/installation-037/result.json'
receipt = f.read_json(receipt_path)
receipt_pin = p.sha(receipt_path)
assert tools == plan['tools'] and tools['git_head'] == receipt['git_head'] == plan['git_head']
assert receipt['passed'] is True and receipt['status'] == 'passed'
assert receipt_pin == plan['installation_receipt_sha256']
assert receipt['source_inventory_sha256'] == plan['source_inventory_sha256']
assert all(p.sha(ROOT / name) == p.sha(installed / name) == digest
           for name, digest in plan['source_sha256'].items())
assert all(p.sha(ROOT / name) == digest for name, digest in plan['controller_sha256'].items())
env = {key: value for key, value in os.environ.items() if key not in {'PYTHONPATH', 'PYTHONHOME'}}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
process = run([*f.SANDBOX, str(installed / '.venv/bin/python'), '-B', '-c', plan['target_bootstrap']],
              cwd=out, env=env, log=out / 'tests.log',
              timeout=max(.001, plan['limits']['worker_timeout_seconds']-(time.monotonic()-START)),
              max_log_bytes=plan['limits']['log_bytes'],
              max_workdir_bytes=plan['limits']['scratch_bytes'],
              max_group_rss_bytes=plan['limits']['group_rss_bytes'])
population = f.read_json(out / 'population.json') if (out / 'population.json').is_file() else None
current = (p.tool_manifest() == tools and p.sha(protocol) == pin
           and p.sha(receipt_path) == receipt_pin
           and all(p.sha(ROOT / name) == p.sha(installed / name) == digest
                   for name, digest in plan['source_sha256'].items())
           and all(p.sha(ROOT / name) == digest for name, digest in plan['controller_sha256'].items()))
wall, full = time.monotonic()-START, cpu()-CPU0
within = max(wall, full)+plan['limits']['publication_allowance_seconds'] <= plan['limits']['targeted_whole_wall_full_cpu_seconds']
expected_shipped = {name: str(installed / (name.replace('.', '/') + '.py'))
                    for name in plan['new_shipped_modules']}
passed = (current and within and process['status'] == 'success' and process['exit_code'] == 0
          and process['cleanup_complete'] is True and process['log_truncated'] is False
          and population is not None and population['successful'] is True
          and population['modules'] == plan['target_modules'] and population['skipped'] == 0
          and population['planned'] == population['ran'] == plan['expected_target_method_count']
          and population['shipped_modules'] == expected_shipped)
record = dict(schema=1, passed=passed, process=process, source_current=current,
              git_head=tools['git_head'], modules=plan['target_modules'], population=population,
              population_sha256=p.sha(out / 'population.json') if population else None,
              protocol_sha256=pin, installation_receipt_sha256=receipt_pin,
              controller_sha256=p.sha(Path(__file__)), log_sha256=p.sha(out / 'tests.log'),
              wall_seconds=wall, full_cpu_seconds=full,
              publication_allowance_seconds=plan['limits']['publication_allowance_seconds'],
              whole_delivery_within_budget=within, historical_test_supplement=None,
              scope=plan['scope'])
p.save_json(out / 'execution.json', record)
print(json.dumps({key: record[key] for key in ('passed', 'source_current', 'wall_seconds', 'full_cpu_seconds', 'population')}))
raise SystemExit(0 if passed else 2)
