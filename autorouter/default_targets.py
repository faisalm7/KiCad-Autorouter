"""Pure single-Default routing targets derived from unchanged hard board floors.

Raw Native class identity is preserved separately from lawful planning targets.
This transform proves only its exact DSN edit, never Native execution, routing
acceptance, electrical suitability or support for a project.
"""
from __future__ import annotations

import copy
from decimal import Context, Decimal, DecimalException, Inexact, InvalidOperation, Overflow, localcontext
import hashlib
import json
from pathlib import Path

from . import board_floor as floors, netclass as nc, sexpr as sx
from .adapter import _parse_dsn, _dump_dsn, _check_units

POLICY = 'single-default-global-floor-targets-v2'
NATIVE_VERSION = '10.0.7'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _json(raw):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate project JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def _bytes(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= sx.MAX_BYTES:
        raise ValueError('bounded nonempty input bytes required')


def _source(source):
    if not isinstance(source, (str, Path)):
        raise ValueError('absolute source identity required')
    path = Path(source)
    if (not path.is_absolute() or '..' in path.parts or path.suffix != '.kicad_pcb'
            or str(path) != str(source)):
        raise ValueError('canonical absolute PCB source identity required')
    return str(path)


def _parents(native, cls):
    """Only one class exists, so an omitted priority cannot resolve another class."""
    explicit_priority = 'priority' in cls
    if explicit_priority and (type(cls['priority']) is not int or not 0 <= cls['priority'] <= 2147483647):
        raise ValueError('bounded explicit Default priority required')
    observed = set()
    for row in native['nets']:
        parents = row.get('parameter_parents')
        if type(parents) is not dict or set(parents) != set(floors.DIMENSIONS):
            raise ValueError('complete Default parameter parents required')
        priorities = []
        for key, parent in parents.items():
            if (type(parent) is not dict or set(parent) != {'name', 'value_nm', 'specified', 'priority'}
                    or parent['name'] != 'Default' or parent['specified'] is not True
                    or type(parent['value_nm']) is not int or parent['value_nm'] != row[key]
                    or type(parent['priority']) is not int
                    or not (0 if explicit_priority else -1) <= parent['priority'] <= 2147483647):
                raise ValueError('Default parameter parent differs from raw source class')
            priorities.append(parent['priority'])
        if len(set(priorities)) != 1 or (explicit_priority and priorities[0] != cls['priority']):
            raise ValueError('Default parameter priorities differ')
        observed.update(priorities)
    if len(observed) != 1:
        raise ValueError('one Default priority must cover every Native net')


def _layers(task, native, structure):
    if sx.one(task, 'version') == ['version', '20260206'] and 'copper_layers' in native:
        names = nc.four_copper_source_layers(task)
        if names != nc.four_copper_native_layers(native):
            raise ValueError('four-copper source/Native identity differs')
    else:
        version = sx.one(task, 'version')
        if version not in (['version', '20241229'], ['version', '20260206']) or 'copper_layers' in native:
            raise ValueError('qualified two/four-copper task required')
        from .layer_policy import NONCOPPER, _two_copper_table
        # Same literal source-all table already used by hierarchy identity;
        # this does not alter the narrower explicit-layer selection policy.
        noncopper = {**NONCOPPER, '47': 'User.5', '49': 'User.6',
                     '51': 'User.7', '53': 'User.8', '55': 'User.9'}
        _two_copper_table(task, noncopper=noncopper)
        names = ['F.Cu', 'B.Cu']
    expected = [['layer', name, ['type', 'signal'], ['property', ['index', str(i)]]]
                for i, name in enumerate(names)]
    if sx.children(structure, 'layer') != expected:
        raise ValueError('DSN source-all copper order/identity differs')
    return names


def _grammar(tree):
    """Keep the pinned export grammar, adding only fixed protected wiring."""
    grammar = {key: set(value) for key, value in floors.GRAMMAR.items()}
    grammar.update(wiring={'wire', 'via'}, wire={'path', 'net', 'type'})
    leaves = floors.LEAVES - {'wiring'}
    arities = {'pcb': 1, 'parser': 0, 'structure': 0, 'layer': 1, 'property': 0,
               'boundary': 0, 'keepout': 1, 'plane': 1, 'rule': 0, 'clearance': 1,
               'placement': 0, 'component': 1, 'place': 5, 'library': 0, 'image': 1,
               'outline': 0, 'pin': 4, 'padstack': 1, 'shape': 0, 'circuit': 0,
               'wiring': 0, 'wire': 0}
    def walk(node, path=()):
        if type(node) is not list or not node or type(node[0]) is not str:
            raise ValueError('invalid DSN node')
        head = node[0]
        if head not in grammar and head not in leaves:
            raise ValueError('unknown DSN grammar: ' + head)
        if head in arities and sum(type(value) is str for value in node[1:]) != arities[head]:
            raise ValueError('unexpected DSN atoms')
        allowed = {'net', 'type'} if head == 'via' and path == ('pcb', 'wiring') else grammar.get(head, set())
        for child in node[1:]:
            if type(child) is list:
                if not child or child[0] not in allowed:
                    raise ValueError('unknown DSN child/routing override')
                walk(child, (*path, head))
            elif type(child) is not str:
                raise ValueError('invalid DSN atom')
    walk(tree)
    for key in floors.GRAMMAR['pcb']:
        if sx.one(tree, key) is None:
            raise ValueError('missing DSN section')
    if any(type(node) is not list for node in tree[2:]):
        raise ValueError('extra DSN root atom')


def _number(atom, *, positive=False):
    if type(atom) is not str or len(atom) > 64:
        raise ValueError('bounded wiring dimension required')
    try:
        with localcontext(Context(prec=100, traps=[Inexact, InvalidOperation, Overflow])):
            value = Decimal(atom) * 1000
    except DecimalException:
        raise ValueError('invalid wiring dimension') from None
    if (not value.is_finite() or value != value.to_integral_value() or abs(value) > 2147483647
            or positive and value <= 0):
        raise ValueError('exact bounded wiring nanometres required')


def _wiring(tree, names, native, via):
    referenced = False
    nets = {row['name'] for row in native['nets']}
    for node in sx.one(tree, 'wiring')[1:]:
        if type(node) is not list or not node or node[0] not in {'wire', 'via'}:
            raise ValueError('only fixed protected DSN wiring supported')
        if sx.one(node, 'type') != ['type', 'fix']:
            raise ValueError('protected wiring must remain fixed')
        net = sx.one(node, 'net')
        if net is None or len(net) != 2 or sx.unquote(net[1]) not in nets:
            raise ValueError('protected wiring net differs')
        if node[0] == 'wire':
            if len(node) != 4:
                raise ValueError('unknown protected wire override')
            path = sx.one(node, 'path')
            if (path is None or len(path) < 7 or len(path) % 2 != 1 or path[1] not in names):
                raise ValueError('qualified protected wire path required')
            for i, atom in enumerate(path[2:]):
                _number(atom, positive=i == 0)
        else:
            if len(node) != 6 or node[1] != via:
                raise ValueError('only the raw Default through-via is supported in wiring')
            _number(node[2]); _number(node[3]); referenced = True
    return referenced


def resolved_project(project, native):
    """Resolve absent defaults from bound Native observations, without saving.

    Explicit source values must agree exactly. Missing source fields never mean
    zero: only the pinned same-load floor/class map can supply them. The local
    resolved copy is for scalar comparisons, not a replacement source project.
    Process and original-byte bindings remain the caller's responsibility.
    """
    if (type(project) is not dict or type(native) is not dict
            or type(native.get('schema')) is not int or native.get('schema') != 1
            or native.get('native_version') != NATIVE_VERSION
            or native.get('units') != 'integer nanometres' or native.get('board_saved') is not False):
        raise ValueError('pinned unsaved Native Default/floor observation required')
    observed = native.get('effective_floors_nm')
    if (type(observed) is not dict or set(observed) != set(floors.FLOORS)
            or any(type(v) is not int or not 0 <= v <= 2147483647 for v in observed.values())):
        raise ValueError('complete bounded Native board floors required')
    result = copy.deepcopy(project)
    def object_at(parent, key):
        if key not in parent:
            parent[key] = {}
        if type(parent[key]) is not dict:
            raise ValueError('malformed source object: ' + key)
        return parent[key]
    settings = object_at(result, 'net_settings')
    if 'classes' not in settings:
        settings['classes'] = [{'name': 'Default'}]
    classes = settings['classes']
    if (type(classes) is not list or len(classes) != 1
            or type(classes[0]) is not dict or classes[0].get('name') != 'Default'):
        raise ValueError('only explicit or implicit sole Default is qualified')
    cls = classes[0]
    rows = native.get('nets')
    if type(rows) is not list or not 0 < len(rows) <= 10000:
        raise ValueError('bounded Native Default net inventory required')
    raw = None
    for row in rows:
        if type(row) is not dict or row.get('class') != 'Default':
            raise ValueError('every Native net must resolve solely to Default')
        values = {key: row.get(key) for key in floors.DIMENSIONS}
        if any(type(v) is not int or not 0 < v <= 2147483647 for v in values.values()):
            raise ValueError('bounded Native Default dimensions required')
        if raw is not None and values != raw:
            raise ValueError('Native Default dimensions differ across nets')
        raw = values
    _parents(native, cls)
    def scalar(parent, key, value, *, zero=False):
        if key in parent:
            if floors.millimetres(parent[key], zero=zero) != value:
                raise ValueError('explicit source/Native dimension differs: ' + key)
        else:
            parent[key] = value / 1000000
            if floors.millimetres(parent[key], zero=zero) != value:
                raise ValueError('Native dimension cannot be represented exactly')
    for key, field in floors.DIMENSIONS.items():
        scalar(cls, field, raw[key])
    rules = object_at(object_at(object_at(result, 'board'), 'design_settings'), 'rules')
    for key, value in observed.items():
        scalar(rules, key, value, zero=True)
    if nc.qualify_project(result)['mode'] != 'single_default':
        raise ValueError('sole Default without assignments/patterns required')
    return result


def source_dimensions(project_raw, native=None):
    """Derive targets from explicit source or verified effective Native values."""
    _bytes(project_raw)
    project = _json(project_raw)
    if native is not None:
        if type(native) is not dict or native.get('project_sha256') != _sha(project_raw):
            raise ValueError('Native Default/floors project binding differs')
        project = resolved_project(project, native)
    if nc.qualify_project(project)['mode'] != 'single_default':
        raise ValueError('one explicit Default without assignments/patterns required')
    settings = project['board']['design_settings']
    if project.get('custom_rules') or settings.get('custom_rules') or settings.get('drc_exclusions'):
        raise ValueError('custom rules/exclusions are outside Default-target scope')
    cls = project['net_settings']['classes'][0]
    if 'priority' in cls and (type(cls['priority']) is not int or not 0 <= cls['priority'] <= 2147483647):
        raise ValueError('bounded explicit Default priority required')
    raw = {key: floors.millimetres(cls[field]) for key, field in floors.DIMENSIONS.items()}
    hard = {key: floors.millimetres(settings['rules'][key], zero=True) for key in floors.FLOORS}
    return {'raw_nm': raw, 'original_floors_nm': hard, 'derived_nm': floors.derive(raw, hard)}


def resolution_fields(project_raw):
    """Disclose exactly which original fields require Native resolution."""
    project = _json(project_raw)
    settings = project.get('net_settings', {})
    classes = settings.get('classes', [{'name': 'Default'}])
    cls = classes[0]
    rules = project.get('board', {}).get('design_settings', {}).get('rules', {})
    return {'native_floor_observation_required': True,
            'implicit_class_fields': [field for field in floors.DIMENSIONS.values() if field not in cls],
            'implicit_floor_fields': [key for key in floors.FLOORS if key not in rules],
            'original_project_modified': False}


def transform(raw_dsn_bytes, native_map, project_raw, task_raw, *, source):
    """Return one exact lawful DSN edit and deterministic derivation receipt."""
    for raw in (raw_dsn_bytes, project_raw, task_raw):
        _bytes(raw)
    if type(native_map) is not dict:
        raise ValueError('Native map object required')
    native = json.loads(_canonical(native_map))  # caller cannot change parsed rows mid-derivation
    source = _source(source)
    if (native.get('source') != source or native.get('board_sha256') != _sha(task_raw)
            or native.get('project_sha256') != _sha(project_raw) or native.get('board_saved') is not False):
        raise ValueError('Native task/project/source binding differs')
    dimensions = source_dimensions(project_raw, native)
    project = resolved_project(_json(project_raw), native)
    cls = project['net_settings']['classes'][0]
    task = sx.parse(task_raw.decode('utf8'))
    if task[0] != 'kicad_pcb' or sx.children(task, 'net_class'):
        raise ValueError('ordinary task without legacy class overrides required')
    for fp in sx.children(task, 'footprint'):
        for node in [fp, *sx.children(fp, 'pad')]:
            if sx.one(node, 'clearance') not in (None, ['clearance', '0']):
                raise ValueError('local clearance overrides not qualified for Default targets')
    tree = _parse_dsn(raw_dsn_bytes.decode('utf8')); _check_units(tree); _grammar(tree)
    if (sx.one(tree, 'resolution') != ['resolution', 'um', '10']
            or sx.one(sx.one(tree, 'parser'), 'host_version') != ['host_version', '"10.0.7"']):
        raise ValueError('pinned Native10.0.7 DSN/grid required')
    raw_audit = nc.audit_mapping(tree, native, project, derive_default_targets=True)
    _parents(native, cls)
    structure, network, library = (sx.one(tree, name) for name in ('structure', 'network', 'library'))
    names = _layers(task, native, structure)
    raw, hard, target = (dimensions[key] for key in ('raw_nm', 'original_floors_nm', 'derived_nm'))
    global_rule = ['rule', ['width', floors.atom_um(raw['width_nm'])],
                   ['clearance', floors.atom_um(raw['clearance_nm'])],
                   ['clearance', floors.atom_um(raw['clearance_nm'] // 4), ['type', 'smd_smd']]]
    if sx.one(structure, 'rule') != global_rule:
        raise ValueError('raw global/typed routing rules differ from Default')
    if sx.one(sx.children(network, 'class')[0], 'rule') != global_rule[:3]:
        raise ValueError('raw Default rule order/values differ')
    old = 'Via[0-' + str(len(names) - 1) + ']_' + floors.atom_um(raw['via_diameter_nm']) + ':' + floors.atom_um(raw['via_drill_nm']) + '_um'
    new = 'Via[0-' + str(len(names) - 1) + ']_' + floors.atom_um(target['via_diameter_nm']) + ':' + floors.atom_um(target['via_drill_nm']) + '_um'
    if sx.one(structure, 'via') != ['via', '"' + old + '"']:
        raise ValueError('one explicit Default routing via required')
    fixed_via = _wiring(tree, names, native, '"' + old + '"')
    stacks = sx.children(library, 'padstack')
    old_stack = next(stack for stack in stacks if sx.unquote(stack[1]) == old)
    if new != old and any(sx.unquote(stack[1]) == new for stack in stacks):
        raise ValueError('derived via ID collides with existing padstack')
    guided = copy.deepcopy(tree)
    gs, gn, gl = (sx.one(guided, name) for name in ('structure', 'network', 'library'))
    gs_rule = sx.one(gs, 'rule')
    gs_rule[1][1] = floors.atom_um(target['width_nm'])
    gs_rule[2][1] = gs_rule[3][1] = floors.atom_um(target['clearance_nm'])
    class_rule = sx.one(sx.children(gn, 'class')[0], 'rule')
    class_rule[1][1] = floors.atom_um(target['width_nm'])
    class_rule[2][1] = floors.atom_um(target['clearance_nm'])
    if new != old:
        sx.one(gs, 'via')[1] = '"' + new + '"'
        sx.one(sx.one(sx.children(gn, 'class')[0], 'circuit'), 'use_via')[1] = '"' + new + '"'
        # A via stack can also be a library pin's shape, even with no wiring.
        # Never rename/remove/mutate it: add a distinct planning choice only.
        stack = copy.deepcopy(old_stack); gl.append(stack)
        stack[1] = '"' + new + '"'
        for shape in sx.children(stack, 'shape'):
            sx.one(shape, 'circle')[2] = floors.atom_um(target['via_diameter_nm'])
    encoded = _dump_dsn(guided).encode('utf8')
    if len(encoded) > sx.MAX_BYTES or _parse_dsn(encoded.decode('utf8')) != guided:
        raise ValueError('derived DSN size/roundtrip differs')
    receipt = {'schema': 1, 'policy': POLICY, 'source': source, 'native_version': NATIVE_VERSION,
               'input_sha256': _sha(raw_dsn_bytes), 'output_sha256': _sha(encoded),
               'project_sha256': _sha(project_raw), 'task_sha256': _sha(task_raw),
               'native_map_sha256': _sha(_canonical(native)), 'raw_nm': raw,
               'original_floors_nm': hard, 'derived_nm': target, 'raw_mapping_audit': raw_audit,
               'dimension_resolution': resolution_fields(project_raw),
               'copper_layers': names, 'original_via_id': old, 'derived_via_id': new,
               'original_via_stack_preserved': True, 'derived_via_stack_added': old != new,
               'protected_via_stack_preserved': bool(fixed_via and old != new),
               'wiring_sha256': _sha(sx.dump(sx.one(tree, 'wiring')).encode()),
               'engine_requirements': dict(floors.ENGINE_REQUIREMENTS),
               'routing_accepted': False, 'production_support_qualified': False,
               'native_execution_proven': False}
    return encoded, receipt


def check(raw_dsn_bytes, guided_bytes, receipt, native_map, project_raw, task_raw, *, source):
    """Reconstruct the sole allowed edit; a rehashed receipt grants no authority."""
    expected, recorded = transform(raw_dsn_bytes, native_map, project_raw, task_raw, source=source)
    if type(guided_bytes) is not bytes or guided_bytes != expected or _canonical(receipt) != _canonical(recorded):
        raise ValueError('Default-target exact edit/receipt differs')
    return recorded
