"""Freeze the existing seven-group installed reader plus fresh1007 evidence.
SPDX-License-Identifier: GPL-3.0-or-later
Preparation only: no tests/Native/JVM; lead runs the emitted bounded reader.
"""
from pathlib import Path
import argparse,ast,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
parser=argparse.ArgumentParser();parser.add_argument('--source-head',required=True)
parser.add_argument('--draft-dir',type=Path,default=ROOT/'.local-backups/installation040-packet-review-001')
args=parser.parse_args();draft=args.draft_dir
plan=f.read_json(ROOT/'.runs/installation040-preparation-001/protocol.json');head=plan['git_head']
assert head==args.source_head==p.tool_manifest()['git_head']
assert f.read_json(ROOT/'.runs/installation040-targeted-001/execution.json')['passed'] is True
ntouter=f.read_json(ROOT/'.runs/installation040-native-001/result.json')
assert ntouter['accepted'] is False and ntouter['passed'] is True and ntouter['status']=='invalidated' and ntouter['git_head']==head
assert ntouter.get('reason')=='Rejected: unqualified caller-pinned Native command prefix'
assert p.sha(ROOT/'.runs/installation040-native-001/result.json')=='4ed082c21f6b1dfa1d65e92566c1955d37c3f1bce3ad15c855e5a301c41af0fd'
ntplan=f.read_json(ROOT/'.runs/installation040-native-preparation-001/protocol.json')
assert ntouter['protocol_sha256']==p.sha(ROOT/'.runs/installation040-native-preparation-001/protocol.json')
out=ROOT/'.runs/current-installation040-review-002';out.mkdir()
audit=(draft/'audit-installation040.py').read_text()
assert "HEAD=='6bd0d57b596c1d55dd7df281d5d6904723cead10'" in audit
# Keep a source-head argument; the template's one source checkpoint is explicit.
audit=audit.replace('6bd0d57b596c1d55dd7df281d5d6904723cead10',head)
controller=(draft/'run-installation040-reader.py').read_text();ast.parse(audit);ast.parse(controller)
(out/'audit.py').write_text(audit);(out/'run.py').write_text(controller)
names=['.runs/installation-040/result.json','.runs/installation-040/source-tracked.json',
 '.runs/installation-040-execution/execution.json','.runs/installation-040-execution/command.log',
 '.runs/installation040-targeted-001/execution.json','.runs/installation040-targeted-001/population.json',
 '.runs/installation040-targeted-001/tests.log','.runs/installation040-preparation-001/protocol.json',
 '.runs/current-installation039-review-001/audit.py','.runs/prepare-installation040-readback-002.py',
 '.runs/installation040-native-preparation-001/protocol.json','.runs/installation040-native-001/result.json',
 '.runs/installation040-native-001/command.log','.runs/run-installation040-native-001.py',
 '.runs/kicad-1007-bundle-qualification-001/result.json']
pins={n:p.sha(ROOT/n) for n in names};pins.update(plan['controller_sha256']);pins.update(plan['source_sha256'])
work=Path(ntplan['native_output']).parent
pins.update({str((work/n).relative_to(ROOT)):pin for n,pin in p.tree_hash(work).items()})
pins.update({str(x.relative_to(ROOT)):p.sha(x) for x in (out/'audit.py',out/'run.py',draft/'audit-installation040.py',draft/'run-installation040-reader.py')})
p.save_json(out/'input-pins.json',dict(kind='installation040-reader-inputs-v1',git_head=head,files_sha256=pins,
 scope='Missing-only seven-group current retained qualification; original target pre-write-only receipt and exact Native outer prefix invalidation remain unchanged, no retroactive publication/timing claim; strict46 unique methods/zero CLI tail; unchanged22-command/82-test/60mm baseline; additional fresh explicit1007 API fullSCH/protected fixture shared readback. Complete384MiB source/distribution/tool/PRL/refill/process/late freshness retained; no full installed suite/freshOS/production promotion.'))
print(f.canonical(dict(prepared=True,files=len(pins),new_native_execution=False,new_test_execution=False)))
