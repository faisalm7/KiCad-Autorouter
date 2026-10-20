import time,resource,fcntl,os,stat
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
HEAD='a03b5e8b6ae523d9f099cf211815900053629fe3'
lane=open(ROOT/'.runs/quality-experiment.lock','r+')
info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
tools=p.tool_manifest();assert tools['git_head']==HEAD
out=ROOT/'.runs/full-integration-206';out.mkdir()
sources=[*sorted((ROOT/'autorouter').glob('*.py')),*sorted((ROOT/'tests').glob('*.py')),*sorted((ROOT/'scripts/windows_native_slice').glob('*.ps1')),*sorted((ROOT/'scripts/windows_native_slice').glob('*.py')),*sorted((ROOT/'scripts/windows_native_slice').glob('*.c')),*sorted((ROOT/'experiments/legacy_via_import_v1').glob('*.py')),*sorted((ROOT/'experiments/task_copper_fixed_v1').glob('*.py')),*sorted((ROOT/'experiments/qfn_escape_seed_v1').glob('*.py')),ROOT/'scripts/experiment_portfolio.py',ROOT/'scripts/experiment_quality.py',ROOT/'scripts/qualify_comparison_portfolio.py',ROOT/'scripts/qualify_review_export.py',ROOT/'scripts/qualify_installed_workflow.py',ROOT/'scripts/prepare_runtime.py',ROOT/'scripts/freeze_current_comparison.py',ROOT/'scripts/enclose_current_comparison.py',ROOT/'scripts/qualify_current_method.py',ROOT/'scripts/report_current_comparison.py',ROOT/'scripts/native_edge_controls.py',ROOT/'scripts/qualify_runtime_workflow.py',ROOT/'scripts/install_smoke.py',ROOT/'scripts/install_gui.py',ROOT/'scripts/prepare_gui_plugin.py',ROOT/'toolchain.lock.json',ROOT/'experiments/schematic_hierarchy_fixture.py',ROOT/'experiments/schematic_hierarchy_native_v1/fixture.py',ROOT/'experiments/native_schematic_transport_v1/fixture.py']
pins={str(path.relative_to(ROOT)):p.sha(path) for path in sources}
p.save_json(out/'protocol.json',{'tools':tools,'source_sha256':pins,'discovery':'.runs/full-suite-local-root-019.py','discovery_sha256':p.sha(ROOT/'.runs/full-suite-local-root-019.py'),'bounds_seconds':480,'scope':'Full current integration after explicit selected7 standard ordinary via_high preference; only search costs change, default None unchanged. Original Native/refill/protection/freshness/rules/PRL and budget guards unchanged. Six constructed controls plus broader regression; tests alone establish no new Native/GUI/install/quality/Windows/release support.'})
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/full-suite-local-root-019.py')],cwd=out,log=out/'command.log',timeout=max(.001,480-(time.monotonic()-START)),max_log_bytes=512*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
stable=p.tool_manifest()==tools and all(p.sha(ROOT/name)==pin for name,pin in pins.items())
record={'schema':1,'process':process,'wall_seconds':time.monotonic()-START,'full_cpu_seconds':cpu()-CPU0,'sources_unchanged':stable,'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'passed':stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True}
p.save_json(out/'execution.json',record);print(json.dumps(record));raise SystemExit(0 if record['passed'] else 2)
