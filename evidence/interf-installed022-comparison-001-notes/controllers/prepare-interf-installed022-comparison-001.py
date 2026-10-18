"""Freeze existing complete source/runtime/admin for one finite development study."""
import datetime, hashlib, json, os, resource, subprocess, sys, time
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as pc
from scripts.qualify_installed_workflow import THERMAL_ARMS, RESERVED_KIND, RESERVED_POLICY
base=ROOT/'.runs/interf-installed022-comparison-001';base.mkdir()
runtime=ROOT/'.runs/runtime-directory-022/runtime';source=ROOT/'.data/boards/kicad-interf-u/interf_u.kicad_pcb'
pins=pc.inventory(source.parent)
manifest=json.loads((ROOT/'data/sources.json').read_text())
expected={str(Path(x['destination']).relative_to('boards/kicad-interf-u')):x['sha256'] for x in manifest['files'] if x.get('project_id')=='kicad-interf-u'}
assert pins==expected and len(pins)==25 and sum((source.parent/name).stat().st_size for name in pins)==1490971
assert pins[source.name]=='a740ce7fde77ab6af191e23ece21e57d36bb3c29325879248520dcd9ab47b57e'
inventory_sha=hashlib.sha256((json.dumps(pins,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest();assert inventory_sha=='dd56688583bae72930102d31e3252d6308e348a240cd16dc06b01bfa2c9696f3'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
names=['scripts/qualify_installed_workflow.py','scripts/experiment_portfolio.py','scripts/experiment_quality.py','scripts/experiment_paired.py']
assert subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all','--',*names],cwd=ROOT)==b''
tools=json.loads(subprocess.run([str(runtime/'.venv/bin/python'),'-B','-c','import json;from autorouter.pipeline import tool_manifest;print(json.dumps(tool_manifest()))'],cwd=runtime,check=True,capture_output=True,timeout=20).stdout)
plan=dict(schema=1,kind=RESERVED_KIND,runtime=str(runtime),arms=list(THERMAL_ARMS),routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,allocation='balanced',installed_trial_accounting_policy=RESERVED_POLICY,
 source=str(source),family='kicad-interf-u',source_hashes=pins,source_inventory_sha256=inventory_sha,tools=tools,administration_head=head,administration_files_sha256={name:p.sha(ROOT/name) for name in names},
 data_source=dict(manifest='data/sources.json',manifest_sha256=p.sha(ROOT/'data/sources.json'),revision='69cafb907ebc09e7722a2a464b1d466fc2e3608d',license='CC-BY-SA-4.0',attribution='KiCad contributors; Tux artwork by Larry Ewing and The GIMP',family_independence='unverified; exposed development, not untouched confirmation'),
 failure='Fresh installed021 v2 deliverednone: standard/tuned/completion solethermal, portfolioinvalidated on diagnosticCPU, CthermalNative0/0/22but workerprefixpublicationrefused. Canonical launcher now passes fresh development Native/export and full162;022whole/partial installchecks pass. No source/class/rule change. Original0opens/2thermalerrors/22warnings retained; expected taskopens are not invaliddesigns.',
 hypothesis='Existing geometry-derived sole-thermal repair may improve full validated completion beyond corrected/tuned/restart baselines without changing zones or spoke rules. C_thermal remains experimental, not default or GUIoptimizer. Shippeddefault aliasesB1 without anotherattempt.',
 decision='Keep all7freshoutcomes; no source, code or board-specific parameter change during run. Integrate/revise/defer after current fullSCH/Native/original/delivery outcomes. No broad superiority from1exposedfamily.',
 accounting='All startup, protocol/context reads, preview, conversion, attempts, selection, validation, review/render, software intent, fresh export, final proof/publication and complete exit count to each full600wall/fullCPU cap. Method has separate450cap and420allocation. No450endtoendclaim or pooled-best baseline. Research/authoring/AIreview/preparation separate, notzero.',
 unsupported='Preserve every source conflict, warning, ignored check, exclusion, refusal, failed candidate, skipped portfolio trial and overrun. Expected unrouted connections are not invaliddesigns. Any unexecuted arm remains unexecuted.',
 portfolio_reserve_planning='Balanced existing3variants; first (420-15)/3-30~105route before setup; later attempts actualremaining, no all3guarantee.30seconds is internal planning not a runtime guarantee; allactual diagnostic/globalcaps and finalfences retained.',outer_controller_sha256=p.sha(ROOT/'.runs/run-interf-installed022-arm-001.py'),recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_preparation_wall_seconds=time.monotonic()-START,protocol_preparation_full_cpu_seconds=cpu()-CPU0,actual_GUI=False,human_review=False)
p.save_json(base/'protocol.json',plan);print(json.dumps(dict(protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),administration_head=head,source_files=len(pins),free_bytes=os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize)))
