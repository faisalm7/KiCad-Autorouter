"""Thin existing-runner enclosure records the COMPLETE dual-Native command cost.
SPDX-License-Identifier: GPL-3.0-or-later
Driver sampled costs+2 are partial; this outer actual sample includes its tail.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as original
HEAD='087f4f79858fd3ff7b0711fba03adfccc335a4b1'
PROTO=ROOT/'.runs/four-cu-class-native-preparation-001/protocol.json';PIN='716e17b5159858eaa277429e1e15600ef63813af8b93d157140ddf901102db68'
DRIVER=ROOT/'.runs/run-four-cu-class-native-001.py';DPIN='91e18222634a2f3cc862052ccca7ba70f379f30da6fdabd4d13eae42d276e25d'
OUT=ROOT/'.runs/four-cu-class-native-enclosure-001';CHILD=ROOT/'.runs/four-cu-class-native-001'
original.clean(HEAD)
if p.sha(PROTO)!=PIN or p.sha(DRIVER)!=DPIN:raise p.Rejected('exact frozen protocol/driver required')
plan=f.read_json(PROTO);prior=plan['preparation_costs'];prewall=prior['wall_seconds']+2;precpu=prior['full_cpu_seconds']+2
if plan['git_head']!=HEAD or CHILD.exists():raise p.Rejected('fixed source/fresh Native destination required')
OUT.mkdir();owner={};h.capture_destination(owner,OUT);selfpin=p.sha(Path(__file__))
argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(DRIVER),'--mode','run','--source-head',HEAD,'--protocol-sha256',PIN]
process=run(argv,cwd=OUT,log=OUT/'command.log',timeout=max(.001,498-prewall-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
path=CHILD/'result.json';child=None;childpin=None;literal=None;bound=False
if path.is_file():
 childpin=p.sha(path);child=f.read_json(path);literal=f.canonical(child)
 bound=p.sha(path)==childpin and child.get('completed_evidence')==original.material(CHILD) and f.canonical(f.read_json(path))==literal
material=p.tree_hash(CHILD) if CHILD.is_dir() else None;logpin=p.sha(OUT/'command.log')
passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False
 and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
record=dict(schema=1,kind='actual-complete-dual-four-copper-Native-enclosure',accepted=False,passed=passed,status='completed' if passed else 'failed',git_head=HEAD,protocol_sha256=PIN,driver_sha256=DPIN,controller_sha256=selfpin,process=process,child_receipt_sha256=childpin,child_literal=literal,child_completed_evidence_bound=bound,child_material_sha256=material,log_sha256=logpin,preparation_costs=prior,whole_wall_full_cpu_cap_seconds=500,scope='Complete fresh dual-version Native driver process, including all tail checks and actual invalid controls if reached. Source/reader/core acceptances unchanged. Child costs are partial samples+2; use actual outer totals. No comparative quality, family, GUI, manufacturing, installation or release claim.')
h.owned_destination(owner);original.clean(HEAD)
if p.sha(PROTO)!=PIN or p.sha(DRIVER)!=DPIN or p.sha(Path(__file__))!=selfpin or p.sha(OUT/'command.log')!=logpin or CHILD.is_dir() and p.tree_hash(CHILD)!=material:raise p.Rejected('final enclosure material/source changed')
for label,ntrecord in plan['native_toolchains'].items():
 nt=p.ExperimentalNativeToolchain.from_record(ntrecord) if ntrecord is not None else None
 if p.tool_manifest(native_toolchain=nt)!=plan['tools'][label]:raise p.Rejected('final dual-Native tool/implementation changed')
record.update(wall_seconds=prewall+time.monotonic()-START,full_cpu_seconds=precpu+cpu()-CPU0,publication_allowance_seconds=2)
if max(record['wall_seconds'],record['full_cpu_seconds'])+2>500:record.update(passed=False,status='budget_exceeded')
p.save_json(OUT/'result.json',record)
print(f.canonical({k:record[k] for k in ['passed','status','wall_seconds','full_cpu_seconds','child_completed_evidence_bound']}));raise SystemExit(0 if record['passed'] else 2)
