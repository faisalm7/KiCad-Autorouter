"""Complete process enclosure for one existing installed042 case; no extra Native.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,json,sys
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R)];sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as original
parser=argparse.ArgumentParser();parser.add_argument('--version',choices=['default1000_partial','explicit1007_whole'],required=True);parser.add_argument('--protocol-sha256',required=True);a=parser.parse_args();v=a.version
HEAD='6e68702bd335a0314e9d5dd32eeb39448811f859';CLONE=R/'.runs/installation-042/checkout';D=R/'.runs/run-installation042-native-001.py'
DPIN='64baf2ca3fb85c7dca7eed05940c63bc0de8883be013db2e3dd47769a074bda2';PROTO=R/('.runs/installation042-'+v+'-preparation-001/protocol.json');CHILD=R/('.runs/installation042-'+v+'-001');OUT=R/('.runs/installation042-'+v+'-complete-001')
original.clean(HEAD)
if p.sha(PROTO)!=a.protocol_sha256 or p.sha(D)!=DPIN or CHILD.exists():raise p.Rejected('fixed fresh case/protocol/controller required')
plan=f.read_json(PROTO);prior=plan['preparation_costs'];pw=prior['wall_seconds']+2;pc=prior['full_cpu_seconds']+2
if plan['git_head']!=HEAD or plan['version']!=v:raise p.Rejected('fixed intended case source required')
OUT.mkdir();owner={};h.capture_destination(owner,OUT);selfpin=p.sha(Path(__file__))
argv=[*f.SANDBOX,str(CLONE/'.venv/bin/python'),'-B',str(D),'--source-head',HEAD,'--version',v]
proc=run(argv,cwd=OUT,log=OUT/'command.log',timeout=max(.001,178-pw-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
path=CHILD/'result.json';child=None;pin=None;literal=None;bound=False;work=Path(plan['native_output']).parent
if path.is_file():
 pin=p.sha(path);child=f.read_json(path);literal=f.canonical(child)
 bound=p.sha(path)==pin and f.canonical(f.read_json(path))==literal and child.get('child_material')==p.tree_hash(work)
material=p.tree_hash(CHILD) if CHILD.is_dir() else None;wp=p.tree_hash(work);lp=p.sha(OUT/'command.log')
ok=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc['log_truncated'] is False)
rec=dict(schema=1,kind='actual-complete-installed042-native-case',accepted=False,passed=ok,status='completed' if ok else 'failed',git_head=HEAD,version=v,protocol_sha256=a.protocol_sha256,controller_sha256=selfpin,native_controller_sha256=DPIN,process=proc,child_receipt_sha256=pin,child_literal=literal,child_material_bound=bound,child_material=material,installed_work_material=wp,log_sha256=lp,preparation_costs=prior,whole_wall_full_cpu_cap_seconds=180,scope='Complete existing installed042 case process including all controller/child/shared-check publication tails. Child sampled costs+2 are partial. Exact original Native/source/PRL/protected/SCH/class/SES/refill/metrics checks unchanged; same180cap, no new Native worker or comparative claim.')
h.owned_destination(owner);original.clean(HEAD)
if p.sha(PROTO)!=a.protocol_sha256 or p.sha(D)!=DPIN or p.sha(Path(__file__))!=selfpin or p.sha(OUT/'command.log')!=lp or CHILD.is_dir() and p.tree_hash(CHILD)!=material or p.tree_hash(work)!=wp:raise p.Rejected('complete installed Native case material changed')
nt=None if v=='default1000_partial' else p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
if p.tool_manifest(native_toolchain=nt)!=plan['source_native_tools']:raise p.Rejected('complete installed source tool context changed')
rec.update(wall_seconds=pw+time.monotonic()-START,full_cpu_seconds=pc+cpu()-CPU0,publication_allowance_seconds=2)
if max(rec['wall_seconds'],rec['full_cpu_seconds'])+2>180:rec.update(passed=False,status='budget_exceeded')
p.save_json(OUT/'result.json',rec)
if f.canonical(f.read_json(OUT/'result.json'))!=f.canonical(rec):raise p.Rejected('complete case result readback differs')
print(f.canonical({k:rec[k] for k in ['passed','status','version','wall_seconds','full_cpu_seconds','child_material_bound']}));raise SystemExit(0 if rec['passed'] else 2)
