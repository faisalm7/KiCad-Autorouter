"""Finite PIC B1 adapter composition; no routing or native qualification.

The caller has already bound the original native context and unrouted derivation.
This wrapper changes only the disposable planning DSN. Native boxes are retained
verbatim; their planning copies expand outward onto the DSN's 0.1um grid. Input
pins below restrict the plane/body population to the already observed PIC case.
"""
import copy
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

from autorouter import adapter as a, sexpr as sx
from autorouter.placement_clearance import read_bytes
from experiments.custom_pad_area_probe_v1.derive import exact_one
from experiments.pic_mixed_transport_probe_v1.routing_input import (
    LAYERS, MAX_FACTS, MAX_INPUT, _raw, canonical,
)

GRID_MM = Decimal('0.0001')
# Canonical AST pins from evidence/pic-selective-routing-001/unrouted.dsn.
PLANE_AST_SHA256 = '8b02a28a7d3da2d76e25ac037df4ea0aaa5c3463b9d55e02eef41b5a80072859'
BODIES_AST_SHA256 = 'c4052eb7c5a1c68ccfa71f4994fe57cddd5a463f79db968859bec26a766ceba8'


def _facts(value):
    raw = canonical(value).encode()
    if len(raw) > MAX_FACTS:
        raise ValueError('adapter facts exceed bound')
    return raw


def _ast_sha(node):
    return a._digest(canonical(node).encode())


def _obstacles(context):
    _facts(context)
    if (type(context) is not dict or type(context.get('context_schema')) is not int
            or context['context_schema'] != 1 or context.get('native_version') != '10.0.0'
            or context.get('units') != 'integer nanometres' or context.get('mode') != 'export'
            or context.get('board_saved') is not False or context.get('routing_accepted') is not False):
        raise ValueError('captured native context scope differs')
    rows = context.get('obstacles')
    if type(rows) is not list or len(rows) != 19:
        raise ValueError('exactly 19 native PCB_TEXT obstacles required')
    ledger = []
    for index, row in enumerate(rows):
        if (type(row) is not dict or set(row) != {'layer', 'kind', 'bbox_mm'}
                or row['kind'] != 'PCB_TEXT'
                or row['layer'] != ('top_layer' if index < 17 else 'bottom_layer')
                or type(row['bbox_mm']) is not list or len(row['bbox_mm']) != 4):
            raise ValueError('original PCB_TEXT layer/kind/box census differs')
        coords = [a._number(value) for value in row['bbox_mm']]
        if (any(abs(value) > 1000000 or value * 1000000 != (value * 1000000).to_integral_value()
                for value in coords) or coords[0] >= coords[2] or coords[1] >= coords[3]):
            raise ValueError('finite native nanometre bounding box required')
        snapped = []
        for side, value in enumerate(coords):
            lower = side < 2
            result = value.quantize(GRID_MM, rounding=ROUND_FLOOR if lower else ROUND_CEILING)
            enlargement = value - result if lower else result - value
            if not 0 <= enlargement < GRID_MM:
                raise ValueError('outward planning enlargement differs')
            number = float(result)
            if a._number(number) != result:
                raise ValueError('planning coordinate JSON roundtrip differs')
            snapped.append(number)
        planning = copy.deepcopy(row)
        planning['bbox_mm'] = snapped
        ledger.append({'index': index, 'original': copy.deepcopy(row), 'snapped': planning})
    if len({canonical(row) for row in rows}) != 19:
        raise ValueError('duplicate native PCB_TEXT obstacle')
    return ledger


def _scope(raw):
    tree = a._parse_dsn(_raw(raw))
    a._check_units(tree)
    if exact_one(tree, 'resolution') != ['resolution', 'um', '10']:
        raise ValueError('observed 0.1um DSN resolution required')
    for key in ('placement', 'library', 'network'):
        exact_one(tree, key)
    structure = exact_one(tree, 'structure')
    layers = sx.children(structure, 'layer')
    if [sx.unquote(row[1]) for row in layers] != LAYERS:
        raise ValueError('original DSN layer order differs')
    planes = sx.children(structure, 'plane')
    if (len(planes) != 1 or planes[0][1] != 'GND'
            or _ast_sha(planes[0]) != PLANE_AST_SHA256):
        raise ValueError('exact original GND plane required')
    bodies = exact_one(tree, 'wiring')[1:]
    if len(bodies) != 2 or _ast_sha(bodies) != BODIES_AST_SHA256:
        raise ValueError('exact two protected bodies and zero ordinary routes required')
    for node in sx.children(structure, 'keepout'):
        if len(node) > 1 and sx.unquote(node[1]).startswith(a._KEEP_OUT_PREFIX):
            raise ValueError('adapter graphics already present')
    return tree, structure.index(planes[0]), planes[0], bodies


def _derive(raw, context):
    """Independent expected edit and full receipt, without writing or adapting."""
    original, plane_index, plane, bodies = _scope(raw)
    obstacles = _obstacles(context)
    tree = copy.deepcopy(original)
    structure = exact_one(tree, 'structure')
    structure.pop(plane_index)
    layers = {sx.unquote(n[1]): n[1] for n in sx.children(structure, 'layer')}
    transformations = [{'kind': 'suppress_dsn_plane', 'net': 'GND',
                        'semantic_sha256': a._digest(sx.dump(plane).encode())}]
    for entry in obstacles:
        index, obstacle = entry['index'], entry['snapped']
        xmin, ymin, xmax, ymax = map(a._number, obstacle['bbox_mm'])
        rect = [a._atom_number(value * 1000) for value in (xmin, -ymax, xmax, -ymin)]
        name = a._KEEP_OUT_PREFIX + a._digest(raw)[:12] + '_' + str(index)
        structure.append(['keepout', name, ['rect', layers[obstacle['layer']], *rect]])
        transformations.append({'kind': 'native_graphic_bbox_keepout', 'obstacle_index': index,
                                'native_layer': obstacle['layer'], 'dsn_layer': obstacle['layer'],
                                'bbox_mm': copy.deepcopy(obstacle['bbox_mm']), 'rect_um': rect,
                                'keepout': name})
    encoded = a._dump_dsn(tree).encode()
    _raw(encoded)
    adapter = {'classification': 'B1_adapter_only', 'mode': 'both',
               'input_sha256': a._digest(raw), 'output_sha256': a._digest(encoded),
               'input_bytes': len(raw), 'output_bytes': len(encoded),
               'planes_removed': 1, 'graphics_keepouts_added': 19,
               'net_pin_mapping': a._network_summary(original), 'net_pin_mapping_unchanged': True,
               'native_project_modified': False, 'transformations': transformations,
               'limitations': [
                   'Graphics use conservative bounding rectangles, not exact copper contours.',
                   'Plane suppression is an all-terminal over-routing surrogate; native zones must remain unchanged.']}
    receipt = {'schema': 1, 'classification': 'B1_adapter_only',
               'input_sha256': a._digest(raw), 'output_sha256': a._digest(encoded),
               'native_context_sha256': a._digest(_facts(context)),
               'planning_grid_mm': '0.0001', 'obstacles': obstacles, 'adapter': adapter,
               'original_ast_sha256': _ast_sha(original),
               'removed_plane': {'structure_index': plane_index, 'node': copy.deepcopy(plane)},
               'preserved_protected_bodies': copy.deepcopy(bodies), 'remaining_ordinary_routes': 0,
               'native_context_modified': False, 'native_rules_modified': False,
               'routing_executed': False, 'routing_accepted': False}
    return original, encoded, receipt


def verify(original_unrouted_bytes, adapted_bytes, context, receipt):
    """Recompute all facts, then reverse the allowed edit to the full input AST."""
    original, expected, wanted = _derive(original_unrouted_bytes, context)
    _raw(adapted_bytes)
    if expected != adapted_bytes or _facts(receipt) != _facts(wanted):
        raise ValueError('adapter output or receipt differs from captured input')
    restored = a._parse_dsn(adapted_bytes.decode())
    structure = exact_one(restored, 'structure')
    # Only the exact 19 append-only nodes from this input are reversible.
    expected_structure = exact_one(a._parse_dsn(expected.decode()), 'structure')
    if structure[-19:] != expected_structure[-19:]:
        raise ValueError('adapter keepout reversal differs')
    del structure[-19:]
    removed = wanted['removed_plane']
    structure.insert(removed['structure_index'], copy.deepcopy(removed['node']))
    if restored != original:
        raise ValueError('adapter reversal changed original unrouted AST')
    return True


def apply(path, context):
    """Apply the existing both-adapter to one disposable DSN; return its binding."""
    path = Path(path)
    original = read_bytes(path, MAX_INPUT)
    context_before = _facts(context)
    _, expected, receipt = _derive(original, context)
    if read_bytes(path, MAX_INPUT) != original:
        raise ValueError('unrouted DSN changed before adaptation')
    adapter = a.adapt_dsn(path, 'both', [copy.deepcopy(row['snapped']) for row in receipt['obstacles']])
    if _facts(context) != context_before or _facts(adapter) != _facts(receipt['adapter']):
        raise ValueError('context or existing adapter receipt changed')
    actual = read_bytes(path, MAX_INPUT)
    if actual != expected:
        raise ValueError('existing adapter produced an undeclared edit')
    # Retain the actual adapter return, not a replacement for its audit record.
    receipt['adapter'] = adapter
    verify(original, actual, context, receipt)
    return receipt
