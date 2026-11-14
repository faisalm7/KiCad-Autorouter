"""Narrow experimental plane transport bound to the existing Native journal.

This does not validate a board or grant acceptance. Both existing adapter
readers reconstruct the same transport independently; the normal final Native,
source, protection and resource checks remain mandatory.
"""
from pathlib import Path
import hashlib

CHOICE_POLICY = 'native7-selected-plane-choice-v1'
VARIANT = 'selected-unselected-native-plane-v1'
BASELINE = 'suppress-all-v1'
FILE = 'selected-plane-transport.json'
HELPER = 'experiments/selected_unselected_plane_v1/policy.py'
POLICY_SNAPSHOT = 'selected-plane-policy.py'


def _reject(message):
    from .pipeline import Rejected
    raise Rejected('selected plane transport: ' + message)


def _names(data):
    # Producer capture precedes SES import/final selected-route audit. It may
    # bind the real captured request, but must not manufacture those later
    # proofs merely to call the stricter final readback helper.
    from . import preferences, routing_scope
    effective = preferences.validate(data.get('routing_preferences', {}).get('effective'))
    if data.get('schema') != 1 or effective['scope'] != 'selected_nets':
        _reject('captured selected preferences required')
    return routing_scope.validate_names(effective['nets'])


def snapshot_policy(directory):
    """Keep extra pure policy outside the exact autorouter code census."""
    from . import pipeline as p, provenance
    directory = provenance.canonical(Path(directory))
    raw = provenance.read_bytes(p.c.ROOT / HELPER)
    with (directory / POLICY_SNAPSHOT).open('xb') as stream:
        stream.write(raw)


def choice(directory, data):
    """A new producer must retain an explicit choice; old producers stay old."""
    from . import pipeline as p
    from .local_settings import policy_declaration
    from .placement_clearance import read_bytes
    directory = Path(directory)
    marker = directory / FILE
    marked = ('selected_plane_choice' in data or 'selected_plane_transport' in data
              or 'plane_transport' in data.get('adapter_transformations', {})
              or marker.exists() or marker.is_symlink())
    eligible = (data.get('input_policy', 'native') == 'native'
                and data.get('scope') == 'selected_nets' and data.get('adapter') == 'both'
                and data.get('strategy') is None and data.get('tools', {}).get('kicad') == '10.0.7')
    if not marked and not eligible:
        return None
    producer = directory / 'code/pipeline.py'
    if not producer.exists() and not producer.is_symlink():
        if marked: _reject('missing captured producer')
        return None
    raw = read_bytes(producer, 1024**2)
    if hashlib.sha256(raw).hexdigest() != data.get('tools', {}).get('implementation_sha256', {}).get('autorouter/pipeline.py'):
        _reject('captured producer differs')
    declared = policy_declaration(raw, name='SELECTED_PLANE_CHOICE_POLICY', expected=CHOICE_POLICY)
    if declared is None or not eligible:
        if marked: _reject('choice outside declared producer/scope')
        return None
    value = data.get('selected_plane_choice')
    if (type(value) is not dict or set(value) != {'policy', 'mode'}
            or value['policy'] != declared or type(value['mode']) is not str
            or value['mode'] not in (BASELINE, VARIANT)):
        _reject('missing or changed explicit producer choice')
    if value['mode'] == BASELINE:
        if ('selected_plane_transport' in data or 'plane_transport' in data.get('adapter_transformations', {})
                or marker.exists() or marker.is_symlink()):
            _reject('baseline contains variant evidence')
    _names(data)
    return value['mode']


def _derive(directory, data, base):
    from . import pipeline as p, floor_route as f, pour_rule_area as pour, sexpr as sx
    from .placement_clearance import read_bytes
    from experiments.selected_unselected_plane_v1 import policy
    directory = Path(directory)
    if choice(directory, data) != VARIANT: _reject('explicit variant required')
    if p.c.NATIVE_VERSION != '10.0.7': _reject('exact selected Native version required')
    source = directory / 'snapshot' / Path(data['source']).name
    source_raw = read_bytes(source, policy.MAX_BYTES)
    if p.tree_hash(source.parent) != data['source_hashes']: _reject('original snapshot changed')
    original = sx.parse(source_raw.decode())
    candidate = directory / 'candidate' / source.name
    names = _names(data)
    from . import routing_scope
    if f.canonical(data.get('selected_net_binding')) != f.canonical(routing_scope.bind(source_raw, names)):
        _reject('source selection binding differs')
    # Reuse the real export journal and pure Default transformer. Producer
    # capture is before import/final audits; it cannot call the final reader by
    # inventing its not-yet-produced selected-route evidence.
    from . import default_targets as targets
    from .local_settings import policy_declaration
    producer = read_bytes(directory / 'code/pipeline.py', 1024**2)
    for key in ('DEFAULT_TARGET_ADMISSION_POLICY', 'NATIVE7_SELECTED_DEFAULT_POLICY'):
        if policy_declaration(producer, name=key, expected=getattr(p, key)) != getattr(p, key):
            _reject('captured Native Default capability missing')
    if sx.one(original, 'version') == ['version', '20241229']:
        if policy_declaration(producer, name='NATIVE7_SELECTED_LEGACY_POLICY', expected=p.NATIVE7_SELECTED_LEGACY_POLICY) != p.NATIVE7_SELECTED_LEGACY_POLICY:
            _reject('captured legacy table capability missing')
    task_raw = (sx.dump(p.routing_task(original, 'selected_nets', names)) + '\n').encode()
    if hashlib.sha256(task_raw).hexdigest() != data.get('task_sha256'):
        _reject('actual Native routing task differs')
    mapping = directory / 'export-netclasses.json'
    guided, default = targets.transform(read_bytes(directory / 'native.dsn', policy.MAX_BYTES),
        f.read_json(mapping), read_bytes(source.with_suffix('.kicad_pro')), task_raw, source=str(candidate))
    default_proof = directory / 'default-targets.json'
    binding = dict(policy=p.DEFAULT_TARGET_ADMISSION_POLICY, file=default_proof.name, sha256=p.sha(default_proof))
    if (f.canonical(data.get('default_target_transport')) != f.canonical(binding)
            or f.canonical(f.read_json(default_proof)) != f.canonical(default)
            or read_bytes(directory / 'default-targets.dsn', policy.MAX_BYTES) != guided):
        _reject('lawful Native Default transport differs')
    f.process_check(directory, data, 'export', [*p.native_prefix(), 'export', str(candidate),
        str(directory / 'task.dsn'), str(mapping), '--task-copper-fixed'])
    if p.sha(directory / 'native.dsn') != data.get('native_dsn_sha256'):
        _reject('actual Native DSN hash differs')
    expected_base = read_bytes(directory / 'default-targets.dsn', policy.MAX_BYTES)
    if pour.qualify(original):
        expected_base, correction = pour.correct(source_raw, expected_base)
        if (f.canonical(data.get('pour_dsn_correction')) != f.canonical(correction)
                or f.canonical(f.read_json(directory / 'pour-dsn-correction.json')) != f.canonical(correction)
                or read_bytes(directory / 'pour-corrected.dsn', policy.MAX_BYTES) != expected_base):
            _reject('preceding pour correction differs')
    elif 'pour_dsn_correction' in data:
        _reject('pour correction without qualified source intent')
    if type(base) is not bytes or base != expected_base: _reject('adapter input differs from Native lineage')
    for name in ('adapter.py', 'selected_plane_transport.py'):
        expected = data['tools']['implementation_sha256'].get('autorouter/' + name)
        if p.sha(p.c.ROOT / 'autorouter' / name) != expected or p.sha(directory / 'code' / name) != expected:
            _reject('live or captured transport implementation differs')
    helper_sha = p.sha(p.c.ROOT / HELPER)
    if p.sha(directory / POLICY_SNAPSHOT) != helper_sha:
        _reject('captured pure policy differs')
    context = policy.capture(source_raw, base, names)
    record = dict(schema=1, policy=VARIANT, context=context, lineage=dict(
        source_hashes=data['source_hashes'], task_sha256=data['task_sha256'],
        native_dsn_sha256=p.sha(directory / 'native.dsn'),
        export_process_sha256=p.sha(directory / 'export-process.json'),
        export_mapping_sha256=p.sha(directory / 'export-netclasses.json'),
        default_target_transport=data['default_target_transport'],
        default_dsn_sha256=p.sha(directory / 'default-targets.dsn'),
        pour_correction=data.get('pour_dsn_correction'),
        adapter_base_sha256=hashlib.sha256(base).hexdigest(),
        producer_sha256=data['tools']['implementation_sha256']['autorouter/pipeline.py'],
        pure_policy_sha256=helper_sha),
        native_fill_equivalence=False, routing_accepted=False, approval_granted=False)
    return {'source_bytes': source_raw, 'selected_names': names, 'context': context}, record


def capture(directory, data, base):
    from . import pipeline as p
    payload, record = _derive(directory, data, base)
    proof = Path(directory) / FILE
    with proof.open('x') as stream:
        import json
        json.dump(record, stream, sort_keys=True, indent=2); stream.write('\n')
    return payload, dict(policy=VARIANT, file=FILE, sha256=p.sha(proof))


def replay(directory, data, base):
    """Fresh per-caller reconstruction, not reuse of a producer's assertion."""
    from . import pipeline as p, floor_route as f
    mode = choice(directory, data)
    if mode != VARIANT: return None
    p.selected_scope_names(data)  # Final replay additionally requires the completed selected-scope proofs.
    source = Path(directory) / 'snapshot' / Path(data['source']).name
    if p.check_default_target_transport(directory, data, p.sx.read(source),
            Path(directory) / 'candidate' / source.name) is None:
        _reject('final Native Default readback required')
    payload, expected = _derive(directory, data, base)
    proof = Path(directory) / FILE
    binding = dict(policy=VARIANT, file=FILE, sha256=p.sha(proof))
    if (f.canonical(data.get('selected_plane_transport')) != f.canonical(binding)
            or f.canonical(f.read_json(proof)) != f.canonical(expected)):
        _reject('missing, changed or downgraded transport record')
    return payload
