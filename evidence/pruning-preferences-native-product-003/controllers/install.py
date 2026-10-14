"""Prospective installation022 wrapper; not executed during maintenance."""
from pathlib import Path
import json, sys, time
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f
from autorouter.runner import run

outer = root / '.runs/installation-022-execution'
outer.mkdir()
argv = [str(root / '.venv/bin/python'), '-B',
        str(root / 'scripts/install_smoke.py'),
        '--output', str(root / '.runs/installation-022'),
        '--guidance', 'native', '--source-mode', 'distribution']
start = time.monotonic()
cpu = time.process_time() + f.child_cpu()
head = p.tool_manifest()['git_head']
result = run(argv, cwd=outer, log=outer / 'command.log', timeout=615,
             max_log_bytes=128 * 1024, max_workdir_bytes=32 * 1024**2,
             max_group_rss_bytes=4 * 1024**3)
record = {
    'schema': 1, 'process': result,
    'wall_seconds': time.monotonic() - start,
    'full_cpu_seconds': time.process_time() + f.child_cpu() - cpu,
    'wrapper_sha256': p.sha(Path(__file__)),
    'log_sha256': p.sha(outer / 'command.log'), 'git_head': head,
    'scope': 'Prospective current source-distribution fresh local Git checkout/venv; '
             'fixed installed subset includes pruning-scoring contract/journal controls; current saved native improvement preference modules copied exactly, additional new controls separate, '
             'then actual native fixture route/check under network denial. Complete original '
             'source inventory remains verified with 22000-file and unchanged 320 MiB caps; '
             '512 MiB installation and 600-second final wall caps remain. Existing Mac/tools/'
             'cache; not full clone, full installed suite, fresh OS or formal package qualification.'
}
p.save_json(outer / 'execution.json', record)
print(json.dumps({k: record[k] for k in ('wall_seconds', 'full_cpu_seconds')}))
raise SystemExit(0 if result['status'] == 'success' and result['exit_code'] == 0
                 and record['wall_seconds'] <= 600 else 2)

