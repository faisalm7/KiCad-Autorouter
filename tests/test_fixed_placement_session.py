"""Authored SES transform controls; no Native import or routing acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import adapter, sexpr as sx, pipeline as p, floor_route as f, placement_clearance as pc


def fixture():
    """Own geometry with intentionally quantized placement, exact route atoms."""
    quote = json.dumps
    return ['session', quote('owned session "quoted".ses'),
            ['base_design', quote('/owned project/own.dsn')],
            ['placement', ['resolution', 'um', '10000'],
             ['component', quote('Owned footprint'),
              ['place', quote('U "1"'), '100000', '-809081', 'front', '0'],
              ['place', quote('J 2'), '120000', '-810000', 'back', '180']]],
            ['was_is'],
            ['routes', ['resolution', 'um', '10000'],
             ['parser', ['host_cad', quote("KiCad's Pcbnew")], ['host_version', quote('10.0.0')]],
             ['library_out',
              ['padstack', quote('Owned via 600:300'),
               ['shape', ['circle', 'F.Cu', '6000']],
               ['shape', ['circle', 'B.Cu', '6000']], ['attach', 'off']]],
             ['network_out',
              ['net', quote('owned signal "A"'),
               ['wire', ['path', 'F.Cu', '2000', '100000', '-809080.52',
                         '110000', '-809080.52', '120000', '-810000'], ['type', 'route']],
               ['via', quote('Owned via 600:300'), '120000', '-810000', ['type', 'route']]],
              ['net', quote('GND'),
               ['wire', ['path', 'B.Cu', '2000', '-0.001', '0', '1000', '0'],
                ['type', 'protect']]]]]]


def encode(tree):
    return (sx.dump(tree) + '\n').encode('utf-8')


class FixedPlacementSessionControls(unittest.TestCase):
    def test_removes_only_root_placement_preserving_quotes_routes_and_all_atoms(self):
        tree = fixture(); before = copy.deepcopy(tree)
        # Comments/spacing are syntax, whereas every remaining AST atom is exact.
        raw = b'; authored session, never imported\n' + encode(tree)
        original = bytes(raw)
        encoded, record = adapter.fixed_placement_session(raw)
        expected = copy.deepcopy(tree); expected.remove(sx.one(expected, 'placement'))
        parsed = sx.parse(encoded.decode('utf-8'))
        self.assertEqual(parsed, expected)
        self.assertEqual(sx.one(parsed, 'routes'), sx.one(tree, 'routes'))
        self.assertEqual(sx.one(parsed, 'base_design'), sx.one(tree, 'base_design'))
        self.assertIsNone(sx.one(parsed, 'placement'))
        self.assertEqual((raw, tree), (original, before))
        self.assertEqual(record['schema'], 1)
        self.assertEqual(record['policy'], 'fixed-placement-session-v1')
        self.assertEqual(record['input_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(record['output_sha256'], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(record['removed_root_placement_count'], 1)
        self.assertTrue(record['routing_ast_unchanged'])
        self.assertTrue(record['original_footprint_poses_preserved_by_omission'])
        self.assertFalse(record['routing_accepted'])

    def test_root_sections_must_be_unique_complete_and_well_formed(self):
        for section in ('base_design', 'placement', 'was_is', 'routes'):
            for mode in ('missing', 'duplicate'):
                with self.subTest(section=section, mode=mode):
                    tree = fixture(); row = sx.one(tree, section)
                    tree.remove(row) if mode == 'missing' else tree.append(copy.deepcopy(row))
                    with self.assertRaises(ValueError): adapter.fixed_placement_session(encode(tree))
        trees = []
        tree = fixture(); tree[0] = 'pcb'; trees.append(tree)
        tree = fixture(); tree[1] = '""'; trees.append(tree)
        tree = fixture(); tree.append(['unknown_root', 'value']); trees.append(tree)
        tree = fixture(); tree[3] = 'placement'; trees.append(tree)
        tree = fixture(); tree[3] = []; trees.append(tree)
        tree = fixture(); tree[4] = ['placement']; trees.append(tree)  # Same root arity, duplicate scope.
        tree = fixture(); row = sx.one(tree, 'placement'); tree.remove(row)
        sx.one(sx.one(tree, 'routes'), 'library_out').append(row); trees.append(tree)
        for tree in trees:
            with self.subTest(tree=tree), self.assertRaises(ValueError):
                adapter.fixed_placement_session(encode(tree))

    def test_renaming_and_malformed_base_design_are_rejected(self):
        for value in (['was_is', ['rename', 'U1', 'U2']], ['was_is', 'old', 'new']):
            tree = fixture(); tree[4] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                adapter.fixed_placement_session(encode(tree))
        for value in (['base_design'], ['base_design', '""'],
                      ['base_design', ['name', 'owned.dsn']], ['base_design', 'a.dsn', 'b.dsn']):
            tree = fixture(); tree[2] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                adapter.fixed_placement_session(encode(tree))

    def test_routing_units_and_resolution_are_explicit_bounded_integers(self):
        for unit, resolution in [('mm', '10'), ('inch', '10'),
                                 *[('um', value) for value in
                                   ('0', '-1', '1.5', '1.0', '1e1', 'NaN', 'Infinity',
                                    '+1', '01', '1000001', '999999999999999999999999')]]:
            tree = fixture(); sx.one(sx.one(tree, 'routes'), 'resolution')[:] = ['resolution', unit, resolution]
            with self.subTest(unit=unit, resolution=resolution), self.assertRaises(ValueError):
                adapter.fixed_placement_session(encode(tree))
        for value in ('1', '1000000'):
            tree = fixture(); sx.one(sx.one(tree, 'routes'), 'resolution')[2] = value
            encoded, _ = adapter.fixed_placement_session(encode(tree))
            self.assertEqual(sx.one(sx.parse(encoded.decode()), 'routes'), sx.one(tree, 'routes'))

    def test_required_routing_sections_cannot_be_missing_nested_or_duplicated(self):
        for key in ('resolution', 'library_out', 'network_out'):
            for mode in ('missing', 'duplicate', 'nested_only'):
                tree = fixture(); routes = sx.one(tree, 'routes'); row = sx.one(routes, key)
                if mode == 'duplicate': routes.append(copy.deepcopy(row))
                else:
                    routes.remove(row)
                    if mode == 'nested_only': routes.append(['wrapper', row])
                with self.subTest(key=key, mode=mode), self.assertRaises(ValueError):
                    adapter.fixed_placement_session(encode(tree))

    def test_type_utf8_syntax_nesting_and_byte_bounds(self):
        for raw in (None, '', bytearray(encode(fixture())), b'', b'\xff',
                    b'(session "unterminated)', b'(session own) (session extra)',
                    b'(' * 131 + b'x' + b')' * 131):
            with self.subTest(raw=repr(raw)[:80]), self.assertRaises(ValueError):
                adapter.fixed_placement_session(raw)
        raw = encode(fixture())
        with patch.object(sx, 'MAX_BYTES', len(raw) - 1), self.assertRaises(ValueError):
            adapter.fixed_placement_session(raw)
        with patch.object(sx, 'MAX_BYTES', len(raw)):
            encoded, _ = adapter.fixed_placement_session(raw)
            self.assertLessEqual(len(encoded), len(raw))


class FixedPlacementImportReadbackControls(unittest.TestCase):
    """Authored worker metadata only: no Native executable was launched."""
    def setUp(self):
        project = Path(__file__).resolve().parents[1]
        (project / '.cache').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='fixed-session-proof-', dir=project / '.cache')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        code = self.root / 'code'; code.mkdir()
        self.native = code / 'native.py'
        self.native.write_text('# Authored producer declaration, not executed Native code.\n'
                               'FIXED_PLACEMENT_SESSION_POLICY="fixed-placement-session-v1"\n')
        self.adapter = code / 'adapter.py'; self.adapter.write_bytes((project / 'autorouter/adapter.py').read_bytes())
        self.work = self.root / 'trial'; self.work.mkdir()
        inputs = self.work / 'task-input'; inputs.mkdir()
        self.board = inputs / 'owned.kicad_pcb'; self.board.write_text('(kicad_pcb)\n')
        self.output = self.work / 'imported.kicad_pcb'; self.output.write_text('(kicad_pcb)\n')
        self.raw = self.work / 'routes.ses'; self.raw.write_bytes(encode(fixture()))
        self.filtered = self.output.with_suffix('.routes-only.ses')
        encoded, metadata = adapter.fixed_placement_session(self.raw.read_bytes())
        self.filtered.write_bytes(encoded)
        metadata.update(source_session=str(self.raw), import_session=str(self.filtered),
                        imported_board_sha256=p.sha(self.output))
        self.metadata = self.filtered.with_suffix('.json'); p.save_json(self.metadata, metadata)
        self.process = self.work / 'import-process.json'
        worker = {'name': 'import', 'cwd': str(self.work), 'status': 'success', 'exit_code': 0,
                  'cleanup_complete': True, 'wall_seconds': 0, 'cpu_seconds': 0,
                  'argv': [*f.SANDBOX, str(p.c.PYTHON), str(p.c.ROOT / 'autorouter/native.py'),
                           'import', str(self.board), str(self.output), str(self.raw)]}
        p.save_json(self.process, worker)
        self.data = {'tools': {'implementation_sha256': {
            'autorouter/native.py': p.sha(self.native), 'autorouter/adapter.py': p.sha(self.adapter)}},
            'steps': [copy.deepcopy(worker)]}

    def check(self):
        retained = pc.inventory(self.root, max_bytes=2*1024**2, max_files=100, max_entries=200)
        return adapter.check_fixed_placement_import(self.root, self.data, retained)

    def rejected(self):
        with self.assertRaises((p.Rejected, ValueError, OSError)): self.check()

    def test_nested_authored_import_proof_replays_exactly(self):
        before = pc.inventory(self.root)
        self.check()
        self.assertEqual(pc.inventory(self.root), before)

    def test_missing_proofs_or_worker_census_cannot_hide_import(self):
        mutations = ('both_proofs', 'step', 'process', 'both_worker_rows', 'all_import_evidence', 'all_but_imported_board', 'duplicate_step')
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                proof = (self.filtered.read_bytes(), self.metadata.read_bytes(), self.process.read_bytes(), self.raw.read_bytes())
                data = copy.deepcopy(self.data)
                try:
                    if mutation == 'both_proofs': self.filtered.unlink(); self.metadata.unlink()
                    elif mutation == 'step': self.data['steps'] = []
                    elif mutation == 'process': self.process.unlink()
                    elif mutation == 'both_worker_rows': self.data['steps'] = []; self.process.unlink()
                    elif mutation in ('all_import_evidence', 'all_but_imported_board'):
                        self.data['steps'] = []; self.process.unlink(); self.filtered.unlink(); self.metadata.unlink()
                        if mutation == 'all_but_imported_board': self.raw.unlink()
                    else: self.data['steps'].append(copy.deepcopy(self.data['steps'][0]))
                    self.rejected()
                finally:
                    self.filtered.write_bytes(proof[0]); self.metadata.write_bytes(proof[1])
                    self.process.write_bytes(proof[2]); self.data = data
                    self.raw.write_bytes(proof[3])

    def test_original_board_name_in_project_copies_is_not_an_import(self):
        for role in ('snapshot','candidate','original','refill','final-drc-input','task-input'):
            directory=self.root/role;directory.mkdir()
            (directory/'imported.kicad_pcb').write_bytes(self.board.read_bytes())
        self.check()

    def test_filtered_bytes_hashes_and_metadata_are_not_self_authorizing(self):
        original = self.metadata.read_bytes(); filtered = self.filtered.read_bytes()
        for mutation in ('filtered', 'input_hash', 'output_hash', 'source_path', 'import_path', 'typed_schema', 'extra_field'):
            with self.subTest(mutation=mutation):
                record = json.loads(original)
                try:
                    if mutation == 'filtered': self.filtered.write_bytes(filtered.replace(b'809080.52', b'809080.53'))
                    elif mutation == 'input_hash': record['input_sha256'] = '0'*64
                    elif mutation == 'output_hash': record['output_sha256'] = '0'*64
                    elif mutation == 'source_path': record['source_session'] = str(self.board)
                    elif mutation == 'import_path': record['import_session'] = str(self.output)
                    elif mutation == 'typed_schema': record['schema'] = True
                    else: record['unqualified'] = True
                    if mutation != 'filtered': p.save_json(self.metadata, record)
                    self.rejected()
                finally: self.metadata.write_bytes(original); self.filtered.write_bytes(filtered)

    def test_captured_policy_and_adapter_provenance_are_mandatory(self):
        native = self.native.read_bytes(); source = self.adapter.read_bytes(); data = copy.deepcopy(self.data)
        for mutation in ('unknown_policy', 'native_capture', 'adapter_capture', 'adapter_pin_deleted', 'adapter_capture_and_pin_deleted'):
            with self.subTest(mutation=mutation):
                try:
                    if mutation == 'unknown_policy':
                        self.native.write_bytes(native.replace(b'fixed-placement-session-v1', b'unknown-policy'))
                        self.data['tools']['implementation_sha256']['autorouter/native.py'] = p.sha(self.native)
                    elif mutation == 'native_capture': self.native.write_bytes(native + b'# drift\n')
                    elif mutation == 'adapter_capture': self.adapter.write_bytes(source + b'# drift\n')
                    elif mutation == 'adapter_pin_deleted': self.data['tools']['implementation_sha256'].pop('autorouter/adapter.py')
                    else:
                        self.adapter.unlink(); self.data['tools']['implementation_sha256'].pop('autorouter/adapter.py')
                    self.rejected()
                finally: self.native.write_bytes(native); self.adapter.write_bytes(source); self.data = copy.deepcopy(data)

    def test_worker_status_identity_paths_and_cleanup_must_match(self):
        original = self.process.read_bytes(); data = copy.deepcopy(self.data)
        for mutation in ('nonzero', 'boolean_exit', 'cleanup', 'cwd', 'name', 'input_escape', 'session_alias'):
            with self.subTest(mutation=mutation):
                worker = json.loads(original)
                try:
                    if mutation == 'nonzero': worker.update(status='nonzero_exit', exit_code=1)
                    elif mutation == 'boolean_exit': worker['exit_code'] = False
                    elif mutation == 'cleanup': worker['cleanup_complete'] = False
                    elif mutation == 'cwd': worker['cwd'] = str(self.root)
                    elif mutation == 'name': worker['name'] = '../import'
                    elif mutation == 'input_escape': worker['argv'][-3] = str(self.root.parent / 'outside.kicad_pcb')
                    else: worker['argv'][-1] = str(self.raw.parent / '..' / 'trial' / self.raw.name)
                    p.save_json(self.process, worker); self.data['steps'] = [copy.deepcopy(worker)]
                    self.rejected()
                finally: self.process.write_bytes(original); self.data = copy.deepcopy(data)

    def test_incumbent_annotation_is_allowed_without_loosening_process_fields(self):
        self.data['steps'][0]['phase'] = 'incumbent'
        self.check()
        for mutation in ('unknown_phase', 'extra_annotation', 'process_field'):
            with self.subTest(mutation=mutation):
                saved = copy.deepcopy(self.data)
                try:
                    if mutation == 'unknown_phase': self.data['steps'][0]['phase'] = 'trial'
                    elif mutation == 'extra_annotation': self.data['steps'][0]['unqualified'] = True
                    else: self.data['steps'][0]['cpu_seconds'] = 1
                    self.rejected()
                finally: self.data = saved

    def test_import_input_output_presence_and_actual_output_hash_are_required(self):
        for path in (self.board, self.output):
            raw = path.read_bytes()
            with self.subTest(deleted=path.name):
                try: path.unlink(); self.rejected()
                finally: path.write_bytes(raw)
        raw = self.output.read_bytes()
        try:
            self.output.write_bytes(raw + b'; changed retained Native output\n')
            self.rejected()
        finally: self.output.write_bytes(raw)

    def test_symlink_proof_is_rejected_and_real_legacy_producer_stays_legacy(self):
        original = self.filtered.read_bytes(); target = self.work / 'authored-target.ses'
        target.write_bytes(original); self.filtered.unlink(); self.filtered.symlink_to(target)
        self.rejected()
        self.filtered.unlink(); target.unlink(); self.metadata.unlink()
        self.native.write_text('# Authored genuine pre-policy producer, no new proof claim.\n')
        self.data['tools']['implementation_sha256']['autorouter/native.py'] = p.sha(self.native)
        self.check()


if __name__ == '__main__':
    unittest.main()
