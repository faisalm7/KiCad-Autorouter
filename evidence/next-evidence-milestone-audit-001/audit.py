"""Read-only targeted planning evidence; no native, solver or network operations."""
from pathlib import Path
import collections
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from autorouter import sexpr as sx

def read(path):
    path = ROOT / path
    if path.is_symlink() or not path.is_file():
        raise ValueError('not a regular input: ' + str(path))
    with path.open('rb') as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('planning input too large')
    return raw

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

manifest = json.loads(read('data/sources.json'))
target_ids = ('kicad-pic-programmer', 'kicad-complex-hierarchy')
bound = {}
projects = {}
for project_id in target_ids:
    entry = next(x for x in manifest['projects'] if x['project_id'] == project_id)
    files = [x for x in manifest['files'] if x.get('project_id') == project_id]
    inventory = {}
    for item in files:
        relative = '.data/' + item['destination']
        raw = read(relative)
        if digest(raw) != item['sha256'] or len(raw) != item['bytes']:
            raise ValueError('source differs from acquisition: ' + relative)
        bound[relative] = digest(raw)
        inventory[item['destination']] = {'bytes': len(raw), 'sha256': digest(raw)}
    board_path = '.data/' + entry['boards'][0]['board']
    board = sx.parse(read(board_path).decode())
    project_path = '.data/' + entry['boards'][0]['project_file']
    project = json.loads(read(project_path))
    custom = []
    for footprint in sx.children(board, 'footprint'):
        ref = next((sx.unquote(x[2]) for x in sx.children(footprint, 'property')
                    if sx.unquote(x[1]) == 'Reference'), None)
        for pad in sx.children(footprint, 'pad'):
            if len(pad) > 3 and pad[3] == 'custom':
                custom.append({'reference': ref, 'pad_sexpr': sx.dump(pad)})
    zones = sx.children(board, 'zone')
    projects[project_id] = {
        'source_manifest_entry': entry, 'verified_complete_manifest_inventory': inventory,
        'files': len(files), 'bytes': sum(v['bytes'] for v in inventory.values()),
        'board': board_path, 'board_sha256': digest(read(board_path)),
        'project': project_path, 'project_sha256': digest(read(project_path)),
        'version': sx.one(board, 'version'), 'footprints': len(sx.children(board, 'footprint')),
        'pads': sum(len(sx.children(f, 'pad')) for f in sx.children(board, 'footprint')),
        'zone_attributes': dict(collections.Counter(sx.dump(sx.one(z, 'attr', [])) for z in zones)),
        'custom_pads': custom,
        'class_configuration': project['net_settings'],
        'severities': project['board']['design_settings']['rule_severities'],
    }

references = [
    'MASTER_PROMPT.md', 'STATUS.md', 'SOURCE_LEDGER.md', 'data/sources.json',
    'autorouter/pipeline.py', 'autorouter/netclass.py', 'autorouter/sexpr.py',
    'docs/netclass-and-corpus-next.md',
    'evidence/placement-production-qualification-001/summary.json',
    'evidence/licensed-expansion-research-003/REPORT.md',
    'evidence/licensed-closure-audit-003/REPORT.md',
    'evidence/placement-search-three-arm-001/arm-2/result.json',
    'evidence/lipo-native-diagnostic-002/summary.json',
    '.runs/support-scope-review-001/source-receipt.json',
    '.runs/support-scope-review-001/source/pcbnew/drc/drc_item.cpp',
    '.runs/support-scope-review-001/source/pcbnew/specctra_import_export/specctra_export.cpp',
]
for relative in references:
    bound[relative] = digest(read(relative))
items = read('.runs/support-scope-review-001/source/pcbnew/drc/drc_item.cpp').decode()
severity_keys = ('footprint_symbol_field_mismatch', 'missing_tuning_profile',
                 'text_on_edge_cuts', 'track_on_post_machined_layer')
if not all('wxT( "' + key + '" )' in items for key in severity_keys):
    raise ValueError('cached native report-key classification absent')
unchanged = all(digest(read(path)) == expected for path, expected in bound.items())
if not unchanged:
    raise ValueError('planning evidence changed while reading')
result = {
    'kind': 'targeted_local_static_planning_audit', 'native_executed': False,
    'network_used': False, 'routing_accepted': False, 'eligibility_changed': False,
    'recommendation': 'narrow pic_programmer custom-polygon transport and original-rule qualification',
    'population_reference': {'acquired': 16, 'static_eligible': 3, 'unsupported': 13,
                             'independent_families': None, 'holdout_boards': 0},
    'upstream_repository': manifest['repository'], 'upstream_commit': manifest['commit'],
    'projects': projects, 'newly_classified_native_keys': list(severity_keys),
    'input_sha256': bound, 'all_sampled_inputs_unchanged': unchanged,
    'scope': 'Complete manifested source files verified for two existing projects only. '
             'This is not independent stock-library parity, family ancestry or fresh native validation.',
}
with (OUT/'audit.json').open('x') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'projects': {k:{n:v[n] for n in ('files','bytes','board_sha256','project_sha256','footprints','pads','zone_attributes')} for k,v in projects.items()}, 'unchanged': unchanged}, indent=2))
