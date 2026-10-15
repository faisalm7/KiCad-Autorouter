"""Freeze the existing seven-group installed reader plus fresh1007 evidence.
SPDX-License-Identifier: GPL-3.0-or-later
Preparation only: no tests/Native/JVM; lead runs the emitted bounded reader.
"""
from pathlib import Path
import argparse,ast,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
parser=argparse.ArgumentParser();parser.add_argument('--source-head',required=True)
parser.add_argument('--draft-dir',type=Path,default=ROOT/'.local-backups/installation041-preparation-001')
args=parser.parse_args();draft=args.draft_dir
plan=f.read_json(ROOT/'.runs/installation041-preparation-001/protocol.json');head=plan['git_head']
assert head==args.source_head==p.tool_manifest()['git_head']
target=f.read_json(ROOT/'.runs/installation041-targeted-001/result.json')
assert target['passed'] is True and target['status']=='completed'
ntouter=f.read_json(ROOT/'.runs/installation041-native-001/result.json')
assert ntouter['accepted'] is False and ntouter['passed'] is True and ntouter['status']=='completed' and ntouter['git_head']==head
assert ntouter['child_completed_evidence_bound'] is True
ntplan=f.read_json(ROOT/'.runs/installation041-native-preparation-001/protocol.json')
assert ntouter['protocol_sha256']==p.sha(ROOT/'.runs/installation041-native-preparation-001/protocol.json')
out=ROOT/'.runs/current-installation041-review-001';out.mkdir()
audit=(draft/'audit-installation041.py').read_text()
controller=(draft/'run-installation041-reader.py').read_text();ast.parse(audit);ast.parse(controller)
(out/'audit.py').write_text(audit);(out/'run.py').write_text(controller)
names=['.runs/installation-041/result.json','.runs/installation-041/source-tracked.json',
 '.runs/installation-041-execution/result.json','.runs/installation-041-execution/command.log',
 '.runs/installation041-targeted-001/result.json','.runs/installation041-targeted-001/population.json',
 '.runs/installation041-targeted-001/tests.log','.runs/installation041-preparation-001/protocol.json',
 '.runs/current-installation039-review-001/audit.py','.runs/prepare-installation041-readback-001.py',
 '.runs/installation041-native-preparation-001/protocol.json','.runs/installation041-native-001/result.json',
 '.runs/installation041-native-001/command.log','.runs/run-installation041-native-001.py',
 '.runs/kicad-1007-bundle-qualification-001/result.json']
pins={n:p.sha(ROOT/n) for n in names};pins.update(plan['controller_sha256']);pins.update(plan['source_sha256'])
work=Path(ntplan['native_output']).parent
pins.update({str((work/n).relative_to(ROOT)):pin for n,pin in p.tree_hash(work).items()})
pins.update({str(x.relative_to(ROOT)):p.sha(x) for x in (out/'audit.py',out/'run.py',draft/'audit-installation041.py',draft/'run-installation041-reader.py')})
p.save_json(out/'input-pins.json',dict(kind='installation041-reader-inputs-v1',git_head=head,files_sha256=pins,
 scope='Fresh041 seven-group current qualification: strict56 unique methods/zero CLI tail; unchanged22-command/82-test/60mm baseline; fresh required explicit1007 API fullSCH/protected fixture shared readback. Sourcehead argument and complete384MiB source/distribution/tool/PRL/refill/process/child-witness/late freshness remain; 1GiB reader unchanged. No full installed suite/freshOS/production promotion or040 record repair.'))
print(f.canonical(dict(prepared=True,files=len(pins),new_native_execution=False,new_test_execution=False)))
