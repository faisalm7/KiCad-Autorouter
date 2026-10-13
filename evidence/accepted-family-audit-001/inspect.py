"""Offline, narrow pedigree inspection of the three already accepted inputs."""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import hashlib, json, sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, sexpr as sx

IDS = ('kicad-sonde-xilinx', 'kicad-interf-u', 'kicad-multichannel')
bindings = {}


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    if path.is_symlink() or not path.is_file():
        raise ValueError('regular bound file required: ' + str(path))
    content = path.read_bytes()
    bindings[str(path.relative_to(ROOT))] = hashlib.sha256(content).hexdigest()
    return content


def load(path):
    return json.loads(read(path))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def walk(node):
    if isinstance(node, list):
        yield node
        for child in node:
            yield from walk(child)


manifest = load('data/sources.json')
old = load('.runs/corpus-support-priority-001/facts.json')
old_manifest = load('.runs/corpus-support-priority-001/MANIFEST.json')
for filename in ('facts.json', 'inspect.py'):
    content = read('.runs/corpus-support-priority-001/' + filename)
    recorded = old_manifest['files'][filename]
    if len(content) != recorded['bytes'] or hashlib.sha256(content).hexdigest() != recorded['sha256']:
        raise ValueError('frozen structural screen mismatch')
read('autorouter/sexpr.py')
read('autorouter/pipeline.py')
coverage = load('evidence/coverage.json')
history_inventory = load('.runs/coldfire-audit-001/predecessor-demo-inventory.json')
history_commit = load('.runs/coldfire-audit-001/oldest-path-commit.json')
assert history_commit['parents'][0]['sha'] == 'a3ca8095665a10d01b02555417a7a273d2332fb1'
assert len(old['boards']) == 20 and old['counts']['current_statically_eligible'] == 3
prior_rows = {row['board']: row for row in old['boards']}
projects = []
symbols, uuids, parsed_boards = {}, {}, {}
file_groups = defaultdict(list)

for project in manifest['projects']:
    pid = project['project_id']
    if pid not in IDS:
        continue
    directory = ROOT / '.data' / project['destination']
    files = [row for row in manifest['files'] if row['project_id'] == pid]
    expected = {str(Path(row['destination']).relative_to(project['destination'])): row['sha256'] for row in files}
    assert p.tree_hash(directory) == expected
    observations, board_rows, symbol_index = [], [], {}
    for entry in files:
        path = Path('.data') / entry['destination']
        content = read(path)
        blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        assert len(content) == entry['bytes'] and hashlib.sha256(content).hexdigest() == entry['sha256']
        assert blob == entry['git_blob_sha1'] and entry['mode'] == '100644'
        file_groups[entry['sha256']].append({'project': pid, 'path': str(path), 'bytes': len(content)})
        if path.suffix not in {'.kicad_sch', '.kicad_pcb', '.kicad_sym', '.kicad_mod'} and path.name not in {'fp-lib-table', 'sym-lib-table'}:
            continue
        tree = sx.parse(content.decode())
        credits = sorted({tuple(sx.unquote(value) for value in node[1:3]) for node in walk(tree)
                          if len(node) > 2 and node[0] == 'property' and sx.unquote(node[1]).lower() in {'author', 'copyright'}})
        models = sorted({sx.unquote(node[1]) for node in walk(tree) if len(node) > 1 and node[0] == 'model'})
        item = {'path': str(path), 'title_block': sx.children(tree, 'title_block'),
                'embedded_library_property_credits': credits, 'model_references': models}
        if path.name.endswith('lib-table'):
            item['exact_table_ast'] = tree
        if path.suffix == '.kicad_sch':
            item['top_level_text'] = [sx.unquote(node[1]) for node in sx.children(tree, 'text')]
            item['repeated_sheet_files'] = dict(Counter(sx.unquote(prop[2]) for sheet in sx.children(tree, 'sheet')
                                                       for prop in sx.children(sheet, 'property') if sx.unquote(prop[1]) == 'Sheetfile'))
        if path.suffix == '.kicad_sym':
            symbol_index.update({sx.unquote(node[1]): hashlib.sha256(canonical(node).encode()).hexdigest()
                                 for node in sx.children(tree, 'symbol')})
        if path.suffix == '.kicad_pcb':
            prior = prior_rows[str(path)]
            assert prior['source_sha256'] == entry['sha256']
            fps = sx.children(tree, 'footprint')
            assert len(fps) == prior['footprints']
            assert sum(len(sx.children(fp, 'pad')) for fp in fps) == prior['pads']
            item['top_level_graphic_text'] = [sx.unquote(node[1]) for node in sx.children(tree, 'gr_text')]
            item['component_values'] = dict(sorted(Counter(sx.unquote(prop[2]) for fp in fps for prop in sx.children(fp, 'property')
                                                            if sx.unquote(prop[1]) == 'Value').items()))
            parsed_boards[str(path)] = tree
            keys = ('board', 'source_sha256', 'footprints', 'pads', 'connected_pad_terminals', 'named_nets_used_by_pads',
                    'terminal_geometry_multiset_sha256', 'footprint_local_pad_geometry_multiset_sha256', 'connectivity_wl3_screen_sha256')
            board_rows.append({key: prior[key] for key in keys})
            if 'unrouted' not in path.name:
                uuids[pid] = {sx.unquote(sx.one(fp, 'uuid')[1]) for fp in fps}
        observations.append(item)
    symbols[pid] = symbol_index
    predecessor = [row for row in history_inventory if row['path'] == project['source_directory']]
    projects.append({'project_id': pid, 'source_directory': project['source_directory'], 'source_revision': manifest['commit'],
                     'original_files': project['source_files'], 'original_bytes': project['source_bytes'],
                     'verified_files_including_notices': len(files), 'verified_bytes_including_notices': sum(row['bytes'] for row in files),
                     'license': project['license'], 'license_notice_paths': project['license_notice_paths'],
                     'additional_rights_evidence': project.get('additional_rights_evidence'),
                     'pedigree_independence': 'unverified; distinct circuitry is not documented independent authorship/ancestry',
                     'cached_2009_predecessor_directory_entry': predecessor, 'boards': board_rows, 'source_observations': observations})

cross = []
for a, b in combinations(IDS, 2):
    common_names = set(symbols[a]) & set(symbols[b])
    cross.append({'projects': [a, b], 'shared_board_footprint_uuids': sorted(uuids[a] & uuids[b]),
                  'shared_local_symbol_names': sorted(common_names),
                  'identical_full_local_symbol_asts': sorted(name for name in common_names if symbols[a][name] == symbols[b][name])})
multichannel = [row for project in projects for row in project['boards'] if project['project_id'] == 'kicad-multichannel']
for key in ('terminal_geometry_multiset_sha256', 'footprint_local_pad_geometry_multiset_sha256', 'connectivity_wl3_screen_sha256'):
    assert multichannel[0][key] == multichannel[1][key]
assert len(projects) == 3 and sum(project['verified_files_including_notices'] for project in projects) == 58

measured = []
for board, path, strategy in (
    ('sonde', 'evidence/portfolio-paired-001/paired-summary.json', 'native-input tuned-incumbent feedback pruning'),
    ('interf_u', 'evidence/thermal-paired-001/paired-summary.json', 'native-input completion plus thermal bridge recovery'),
    ('multichannel', 'evidence/placement-paired-003/run/paired-summary.json', 'placement standard-85-v1 individual-first pruning'),
):
    pair = load(path)
    measured.append({'board': board, 'strategy': strategy, 'summary': path, 'summary_sha256': bindings[path],
                     'comparisons': pair['comparisons'],
                     'arms': [{key: row[key] for key in ('id', 'accepted', 'status', 'length_mm', 'vias', 'opens', 'blocking',
                                                         'warnings', 'charged_wall_seconds', 'charged_cpu_seconds') if key in row}
                              for row in pair['results']],
                     'this_audit_reperformed_native_or_full_receipt_validation': False})

outer = load('evidence/placement-paired-003/execution.json')
pair = load('evidence/placement-paired-003/run/paired-summary.json')
extra_cpu = outer['full_cpu_seconds'] - sum(row['invocation_cpu_seconds'] for row in pair['results'])
extra_wall = outer['wall_seconds'] - sum(row['invocation_wall_seconds'] for row in pair['results'])
measured[-1]['conservative_complete_outer_charging'] = {
    'outer_wall_seconds': outer['wall_seconds'], 'outer_full_cpu_seconds': outer['full_cpu_seconds'],
    'method': 'Assign the full outer cost beyond the sum of arm invocations to every arm, separately',
    'arms': [{'id': row['id'], 'wall_seconds': row['invocation_wall_seconds'] + extra_wall,
              'full_cpu_seconds': row['invocation_cpu_seconds'] + extra_cpu} for row in pair['results']]}
for path in ('evidence/review-portfolio-001/review.json', 'evidence/review-thermal-paired-001/audit.json',
             'evidence/review-placement-paired-003/REPORT.md', 'docs/data-provenance.md'):
    read(path)

for path, expected_hash in bindings.items():
    if p.sha(ROOT / path) != expected_hash:
        raise ValueError('read-only audit input changed: ' + path)
result = {'schema': 1, 'scope': 'Three accepted original KiCad development projects plus multichannel sibling; offline pedigree audit only',
          'native_processes': 0, 'engine_processes': 0, 'network_requests': 0, 'git_subprocesses': 0,
          'population_unchanged': {'acquired_logical_boards': 20, 'statically_eligible': 3, 'unsupported': 17,
                                   'proven_independent_families': 0, 'holdout': False},
          'structural_screen_reuse': {'facts': '.runs/corpus-support-priority-001/facts.json',
                                     'normalizer': '.runs/corpus-support-priority-001/inspect.py',
                                     'native_or_full_population_experiments_repeated': False,
                                     'method_limits': old['normalization'],
                                     'interpretation': 'Three different whole-design screens, not an independence/ancestry/isomorphism proof'},
          'common_origin': {'repository': manifest['repository'], 'canonical_repository': manifest['canonical_repository'],
                            'revision': manifest['commit'], 'tag': manifest['tag'], 'source_scope': 'demos/*',
                            'license': manifest['license'], 'license_scope_evidence': manifest['license_scope_evidence']},
          'historical_observation': {'parent_revision': history_commit['parents'][0]['sha'],
                                     'child_commit_date': history_commit['commit']['author']['date'],
                                     'child_committer_name': history_commit['commit']['committer']['name'],
                                     'limit': 'Directory entries for sonde/interf_u already existed in parent of 2009 commit; neither original circuit author nor continuous file ancestry is established. This is cached coldfire-query metadata, not a path-history query for these three designs.'},
          'projects': projects, 'cross_project_reuse': cross,
          'identical_cross_project_files': [{'sha256': sha, 'files': entries} for sha, entries in sorted(file_groups.items())
                                           if len({entry['project'] for entry in entries}) > 1],
          'existing_measured_results': measured, 'source_bindings': bindings}
(OUT / 'facts.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'projects': len(projects), 'original_files': sum(row['original_files'] for row in projects),
                  'verified_files_including_notices': 58, 'unchanged_bound_inputs': len(bindings),
                  'population': result['population_unchanged'], 'cross_project_reuse': cross}, indent=2))
