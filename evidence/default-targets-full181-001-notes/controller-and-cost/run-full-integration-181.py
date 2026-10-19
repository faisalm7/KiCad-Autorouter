import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/full-integration-181';out.mkdir()
sources=[*sorted((ROOT/'autorouter').glob('*.py')),*sorted((ROOT/'tests').glob('*.py')),*sorted((ROOT/'scripts/windows_native_slice').glob('*.ps1')),*sorted((ROOT/'scripts/windows_native_slice').glob('*.py')),*sorted((ROOT/'scripts/windows_native_slice').glob('*.c')),*sorted((ROOT/'experiments/legacy_via_import_v1').glob('*.py')),*sorted((ROOT/'experiments/task_copper_fixed_v1').glob('*.py')),ROOT/'scripts/experiment_portfolio.py',ROOT/'scripts/experiment_quality.py',ROOT/'scripts/qualify_comparison_portfolio.py',ROOT/'scripts/qualify_review_export.py',ROOT/'scripts/qualify_installed_workflow.py',ROOT/'scripts/prepare_runtime.py',ROOT/'scripts/install_smoke.py',ROOT/'scripts/install_gui.py',ROOT/'scripts/prepare_gui_plugin.py',ROOT/'toolchain.lock.json',ROOT/'experiments/schematic_hierarchy_fixture.py',ROOT/'experiments/schematic_hierarchy_native_v1/fixture.py',ROOT/'experiments/native_schematic_transport_v1/fixture.py']
pins={str(path.relative_to(ROOT)):p.sha(path) for path in sources};tools=p.tool_manifest()
p.save_json(out/'protocol.json',{'tools':tools,'source_sha256':pins,'discovery':'.runs/full-suite-local-root-019.py','discovery_sha256':p.sha(ROOT/'.runs/full-suite-local-root-019.py'),'bounds_seconds':480,'scope':'Full integration after source-derived singleDefault hard-floor target correction, preserved old via padstacks/library pins, required direct/rejected-incumbent guidance readback, shared final raw-class/derived-geometry process audit and fresh export plumbing. Includes targeted regressions plus existing hierarchy/flat/layer/protected/cancel/stale controls. Raw source Default/rules remain unchanged; stock and composite paths retain separate contracts. This suite is not installed Native/GUI/Windows/breadth or release qualification.'})
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/full-suite-local-root-019.py')],cwd=out,log=out/'command.log',timeout=max(.001,480-(time.monotonic()-START)),max_log_bytes=512*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
stable=p.tool_manifest()==tools and all(p.sha(ROOT/name)==pin for name,pin in pins.items())
record={'schema':1,'process':process,'wall_seconds':time.monotonic()-START,'full_cpu_seconds':cpu()-CPU0,'sources_unchanged':stable,'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'passed':stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True}
p.save_json(out/'execution.json',record);print(json.dumps(record));raise SystemExit(0 if record['passed'] else 2)
