from pathlib import Path
import sys,time,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/full-integration-037';out.mkdir()
extra=['tests/test_pruning_scoring.py','tests/test_inherited_trial_readback.py','tests/test_native_class_readback.py','tests/test_analog_filter_demo.py','experiments/original_project_native_v1/driver.py','scripts/fetch_led_demo.py','scripts/experiment_quality.py','scripts/install_smoke.py','experiments/placement_handoff_native_v1/driver.py','tests/test_arcdice_demo_fetch.py','tests/test_install_smoke.py','tests/test_netclass_parent_policy.py','experiments/native_paired_v1/readback.py'];frozen={n:p.sha(ROOT/n) for n in extra}
tools=p.tool_manifest();start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/full-suite-local-root-019.py')],cwd=out,log=out/'command.log',timeout=180,max_log_bytes=384*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'git_head':tools['git_head'],'tools':tools,'process':process,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'scope':'Full current original software suite at33c52d3b after fresh High C native/audit closure and actual installation020. Final installer finite22000file inspection and installed scoring controls are included. Current core/tool bytes and extra source pins checked before/after. All prior Native failures and suites retained. This is full software integration, not route-quality, generalization or freshOS evidence; original Native/installed smoke/GUI qualifications remain separate. Same root discover(tests) via existing adapter, unchanged process/resource caps.'}
assert p.tool_manifest()==tools and frozen=={n:p.sha(ROOT/n) for n in extra}
record['extra_source_sha256']=frozen
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('git_head','wall_seconds','full_cpu_seconds')}));print(json.dumps({k:process[k] for k in ('status','exit_code','cleanup_complete')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2)
