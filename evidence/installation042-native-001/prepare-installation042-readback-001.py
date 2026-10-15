"""Freeze the existing seven-group installed reader plus fresh1007 evidence.
SPDX-License-Identifier: GPL-3.0-or-later
Preparation only: no tests/Native/JVM; lead runs the emitted bounded reader.
"""
from pathlib import Path
import argparse,ast,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
parser=argparse.ArgumentParser();parser.add_argument('--source-head',required=True)
parser.add_argument('--draft-dir',type=Path,default=ROOT/'.local-backups/installation042-draft-001')
args=parser.parse_args();draft=args.draft_dir
plan=f.read_json(ROOT/'.runs/installation042-preparation-001/protocol.json');head=plan['git_head']
assert head==args.source_head==p.tool_manifest()['git_head']
target=f.read_json(ROOT/'.runs/installation042-targeted-001/result.json')
assert target['passed'] is True and target['status']=='completed'
native_plans=[]
for version in ('default1000_partial','explicit1007_whole'):
 ntouter=f.read_json(ROOT/('.runs/installation042-'+version+'-001/result.json'))
 assert ntouter['accepted'] is False and ntouter['passed'] is True and ntouter['status']=='completed' and ntouter['git_head']==head and ntouter['version']==version
 assert ntouter['child_completed_evidence_bound'] is True
 path=ROOT/('.runs/installation042-'+version+'-preparation-001/protocol.json');ntplan=f.read_json(path)
 assert ntouter['protocol_sha256']==p.sha(path) and ntplan['version']==version
 native_plans.append(ntplan)
out=ROOT/'.runs/current-installation042-review-001';out.mkdir()
audit=(draft/'audit-installation042.py').read_text()
controller=(draft/'run-installation042-reader.py').read_text();ast.parse(audit);ast.parse(controller)
(out/'audit.py').write_text(audit);(out/'run.py').write_text(controller)
names=['.runs/installation-042/result.json','.runs/installation-042/source-tracked.json',
 '.runs/installation-042-execution/result.json','.runs/installation-042-execution/command.log',
 '.runs/installation042-targeted-001/result.json','.runs/installation042-targeted-001/population.json',
 '.runs/installation042-targeted-001/tests.log','.runs/installation042-preparation-001/protocol.json',
 '.runs/current-installation041-review-001/audit.py','.runs/prepare-installation042-readback-001.py',
 '.runs/run-installation042-native-001.py','.runs/installation042-installed-fourcu.py',
 '.runs/kicad-1007-bundle-qualification-001/result.json']
pins={n:p.sha(ROOT/n) for n in names};pins.update(plan['controller_sha256']);pins.update(plan['source_sha256'])
for ntplan in native_plans:
 version=ntplan['version'];work=Path(ntplan['native_output']).parent
 pins.update({str((work/n).relative_to(ROOT)):pin for n,pin in p.tree_hash(work).items()})
 for name in ('.runs/installation042-'+version+'-preparation-001/protocol.json','.runs/installation042-'+version+'-001/result.json','.runs/installation042-'+version+'-001/command.log'):
  pins[name]=p.sha(ROOT/name)
pins.update({str(x.relative_to(ROOT)):p.sha(x) for x in (out/'audit.py',out/'run.py',draft/'audit-installation042.py',draft/'run-installation042-reader.py')})
p.save_json(out/'input-pins.json',dict(kind='installation042-reader-inputs-v1',git_head=head,files_sha256=pins,
 scope='Fresh042 seven-group current qualification: strict117 unique methods/zero CLI tail; unchanged22-command/82-test/60mm baseline; fresh installed1000 partial + explicit1007 whole4Cu fullSCH/protected/inner/via fixtures shared readback. Sourcehead argument and complete22500file/384MiB source/distribution/tool/PRL/refill/process/child-witness/late freshness remain; 1GiB reader unchanged. No full installed suite/freshOS/production promotion or040 record repair.'))
print(f.canonical(dict(prepared=True,files=len(pins),new_native_execution=False,new_test_execution=False)))
