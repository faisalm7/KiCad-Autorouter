"""Bounded immutable footprint metadata census, never placement authority.

Project-owned implementation under the repository licence.  Field meanings and
formatter seams were checked against KiCad 10.0.7; no upstream code is copied.
The caller must still qualify all source geometry, Native identity/pose and the
complete original AST.  A formatted string is evidence supplied by the caller,
not proof here that Native ran.  Point-bearing owners stay fixed in this scope.
"""
import copy
import hashlib
import json
import uuid

from . import contract as c

POLICY = 'immutable-footprint-engineering-metadata-v1'
MAX_BYTES = 256 * 1024
MAX_NODES = 16384
MAX_PADS = 8
MAX_UNITS = 8
MAX_POINTS = 16
MAX_NM = 2_000_000_000
ROOT_FIELDS = {
    'layer', 'uuid', 'at', 'property', 'path', 'attr', 'fp_rect', 'fp_line',
    'fp_circle', 'fp_arc', 'fp_poly', 'fp_text', 'pad', 'embedded_fonts',
    'locked', 'descr', 'tags', 'sheetname', 'sheetfile', 'model', 'units',
    'duplicate_pad_numbers_are_jumpers', 'point',
}
REPEATED = {'property', 'fp_rect', 'fp_line', 'fp_circle', 'fp_arc', 'fp_poly',
            'fp_text', 'pad', 'model', 'point'}
ATTRIBUTES = {'smd', 'through_hole', 'board_only', 'exclude_from_pos_files',
              'exclude_from_bom'}


def _need(value, message):
    if not value:
        raise ValueError(message)


def _tree(value):
    """Bound caller ASTs before recursive syntax helpers; aliases are ambiguous."""
    pending, seen, count, size = [(value, 0)], set(), 0, 0
    while pending:
        node, depth = pending.pop()
        count += 1
        _need(count <= MAX_NODES and depth <= 32, 'Metadata syntax bound exceeded')
        if type(node) is str:
            _need(len(node) <= MAX_BYTES, 'Metadata atom bound exceeded')
            size += len(node.encode('utf-8'))
            _need(size <= MAX_BYTES, 'Metadata byte bound exceeded')
        else:
            _need(type(node) is list and node and id(node) not in seen,
                  'Unaliased metadata syntax lists/atoms required')
            seen.add(id(node))
            _need(len(node) <= MAX_NODES, 'Metadata syntax bound exceeded')
            pending.extend((item, depth + 1) for item in node)


def _fields(node, allowed, *, repeated=(), start=1):
    _need(all(type(row) is list and row and row[0] in allowed for row in node[start:]),
          'Unknown engineering metadata field')
    for key in allowed - set(repeated):
        c.sx.one(node, key)


def _name(atom):
    _need(type(atom) is str, 'Metadata string required')
    value = c.sx.unquote(atom)
    _need(0 < len(value) <= 128 and len(value.encode('utf-8')) <= 256
          and all(ord(char) >= 32 and ord(char) != 127 for char in value),
          'Bounded nonempty metadata name required')
    return value


def _identity(value):
    _need(type(value) is str and len(value) == 36, 'Canonical metadata UUID required')
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        raise ValueError('Canonical metadata UUID required') from None
    _need(str(parsed) == value, 'Canonical metadata UUID required')
    return value


def _uid(node):
    return _identity(c.atom(node, 'uuid'))


def _payload(record):
    return json.dumps(record, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _check_record(record):
    keys = {'schema', 'policy', 'owner_uuid', 'pads', 'units_present', 'units',
            'duplicate_pad_numbers_are_jumpers', 'points', 'points_fixed', 'point_owner_pose'}
    _need(type(record) is dict and set(record) == keys and type(record['schema']) is int
          and record['schema'] == 1 and record['policy'] == POLICY
          and record['duplicate_pad_numbers_are_jumpers'] is False
          and record['points_fixed'] is True and type(record['units_present']) is bool,
          'Complete immutable engineering metadata record required')
    identities = {_identity(record['owner_uuid'])}
    pads = record['pads']
    _need(type(pads) is list and len(pads) <= MAX_PADS, 'Bounded metadata pad census required')
    for row in pads:
        _need(type(row) is dict and set(row) == {'uuid', 'number'}, 'Exact metadata pad row required')
        identity = _identity(row['uuid'])
        _need(identity not in identities, 'Duplicate metadata item UUID')
        identities.add(identity)
        _need(_name(row['number']) == row['number'], 'Literal metadata pad number required')
    _need(pads == sorted(pads, key=lambda row: row['uuid']), 'Canonical metadata pad order required')
    numbers = {row['number'] for row in pads}
    units = record['units']
    _need(type(units) is list and len(units) <= MAX_UNITS
          and bool(units) == record['units_present'], 'Explicit nonempty unit mapping required')
    names, pins = set(), set()
    for row in units:
        _need(type(row) is dict and set(row) == {'name', 'pins'}, 'Exact unit mapping row required')
        name = _name(row['name'])
        _need(name == row['name'] and name not in names, 'Unique literal unit name required')
        names.add(name)
        _need(type(row['pins']) is list and 1 <= len(row['pins']) <= MAX_PADS,
              'Bounded nonempty unit pins required')
        for pin in row['pins']:
            _need(_name(pin) == pin and pin in numbers and pin not in pins,
                  'Unit pin must uniquely map an actual pad number')
            pins.add(pin)
    points = record['points']
    _need(type(points) is list and len(points) <= MAX_POINTS, 'Bounded fixed point census required')
    pose = record['point_owner_pose']
    if points:
        _need(type(pose) is dict and set(pose) == {'position_nm', 'angle', 'layer'},
              'Fixed point owner pose required')
        _need(type(pose['position_nm']) is list and len(pose['position_nm']) == 2
              and all(type(n) is int and abs(n) <= MAX_NM for n in pose['position_nm'])
              and type(pose['angle']) is int and pose['angle'] in (0, 90, 180, 270)
              and type(pose['layer']) is str and pose['layer'] in ('F.Cu', 'B.Cu'),
              'Exact fixed point owner pose required')
    else:
        _need(pose is None, 'Point-free metadata cannot carry a fixed point pose')
    # Import only when used, avoiding an ordinary -> metadata -> ordinary cycle.
    from .ordinary import PASSIVE_LAYERS
    for row in points:
        _need(type(row) is dict and set(row) == {'uuid', 'position_nm', 'size_nm', 'layer'},
              'Exact fixed point row required')
        identity = _identity(row['uuid'])
        _need(identity not in identities, 'Duplicate metadata item UUID')
        identities.add(identity)
        position = row['position_nm']
        _need(type(position) is list and len(position) == 2
              and all(type(n) is int and abs(n) <= MAX_NM for n in position),
              'Exact fixed point coordinates required')
        _need(type(row['size_nm']) is int and 0 < row['size_nm'] <= 100_000_000,
              'Bounded positive fixed point display size required')
        _need(type(row['layer']) is str and row['layer'] in PASSIVE_LAYERS,
              'Passive fixed point layer required')
    _need(points == sorted(points, key=lambda row: row['uuid']), 'Canonical fixed point order required')
    _need(len(_payload(record)) <= MAX_BYTES, 'Metadata record byte bound exceeded')


def validate(record):
    """Validate detached wire data; it grants no source/Native authority."""
    _check_record(record)
    return copy.deepcopy(record)


def digest(record):
    """Hash an exact validated census, without claiming who captured it."""
    return hashlib.sha256(_payload(validate(record))).hexdigest()


def capture(footprint):
    """Read a strict metadata census from one caller-owned footprint AST."""
    _tree(footprint)
    _need(len(footprint) >= 2 and footprint[0] == 'footprint'
          and type(footprint[1]) is str, 'Footprint AST required')
    _fields(footprint, ROOT_FIELDS, repeated=REPEATED, start=2)
    marker = c.sx.one(footprint, 'duplicate_pad_numbers_are_jumpers')
    _need(marker == ['duplicate_pad_numbers_are_jumpers', 'no'],
          'One explicit no duplicate-pad jumper marker required')
    attributes = c.sx.one(footprint, 'attr')
    if attributes is not None:
        _need(all(type(value) is str and value in ATTRIBUTES for value in attributes[1:])
              and len(attributes[1:]) == len(set(attributes[1:])),
              'Unsupported footprint metadata attribute')
    pads = c.sx.children(footprint, 'pad')
    _need(len(pads) <= MAX_PADS and all(len(pad) >= 4 for pad in pads),
          'Bounded metadata pad census required')
    record = dict(schema=1, policy=POLICY, owner_uuid=_uid(footprint),
                  pads=sorted((dict(uuid=_uid(pad), number=_name(pad[1])) for pad in pads),
                              key=lambda row: row['uuid']),
                  units_present=c.sx.one(footprint, 'units') is not None, units=[],
                  duplicate_pad_numbers_are_jumpers=False, points=[], points_fixed=True,
                  point_owner_pose=None)
    units = c.sx.one(footprint, 'units')
    if units is not None:
        _fields(units, {'unit'}, repeated={'unit'})
        _need(1 <= len(units) - 1 <= MAX_UNITS, 'Bounded nonempty units required')
        for unit in units[1:]:
            _fields(unit, {'name', 'pins'})
            pins = c.sx.one(unit, 'pins')
            _need(pins is not None and all(type(pin) is str for pin in pins[1:]),
                  'Flat unit pin list required')
            record['units'].append(dict(name=_name(c.atom(unit, 'name')),
                                        pins=[_name(pin) for pin in pins[1:]]))
    points = c.sx.children(footprint, 'point')
    _need(len(points) <= MAX_POINTS, 'Bounded fixed point census required')
    for point in points:
        _fields(point, {'at', 'size', 'layer', 'uuid'})
        record['points'].append(dict(uuid=_uid(point), position_nm=c.point(point, 'at'),
            size_nm=c.pt.nm(c.atom(point, 'size'), 1_000_000), layer=c.atom(point, 'layer')))
    record['points'].sort(key=lambda row: row['uuid'])
    if points:
        from .ordinary import at
        position, angle = at(footprint)
        record['point_owner_pose'] = dict(position_nm=position, angle=angle,
                                         layer=c.atom(footprint, 'layer'))
    # Point identities must not alias graphical/property UUIDs outside this census.
    direct_ids = [_uid(row) for row in footprint[2:] if c.sx.one(row, 'uuid') is not None]
    _need(len(direct_ids) == len(set(direct_ids)) and record['owner_uuid'] not in direct_ids,
          'Duplicate footprint child UUID')
    return validate(record)


def compare(expected, formatted_footprint, jumper_flag, *, owner_moved=False):
    """Compare supplied formatter evidence; never invoke Native or file I/O.

    The caller must supply the actual bool getter and reject a moved point owner.
    Source/candidate pose, complete geometry and final Native checks stay outside
    this metadata-only helper and are still mandatory.
    """
    source = validate(expected)
    _need(type(jumper_flag) is bool and jumper_flag is False,
          'Actual duplicate-pad jumper getter must be false')
    _need(type(owner_moved) is bool and not (owner_moved and source['points']),
          'Point-bearing footprint must remain fixed')
    _need(type(formatted_footprint) is str and 0 < len(formatted_footprint) <= MAX_BYTES
          and len(formatted_footprint.encode('utf-8')) <= MAX_BYTES,
          'Bounded formatted footprint text required')
    actual = capture(c.sx.parse(formatted_footprint))
    _need(actual == source, 'Native formatted immutable engineering metadata differs')
    return dict(policy=POLICY, owner_uuid=source['owner_uuid'], immutable_metadata_equal=True,
                metadata_sha256=digest(source),
                formatted_footprint_sha256=hashlib.sha256(formatted_footprint.encode('utf-8')).hexdigest(),
                supplied_jumper_getter=False, points_fixed=True, native_execution_proven=False)
