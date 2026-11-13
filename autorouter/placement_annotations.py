"""Conservative source-bound annotation prefilter, never Native DRC authority.

Only translations of already captured movable footprints are considered. Saved
source geometry is independently witnessed before any Native bounding boxes are
read. A proxy conflict can refuse a proposal; passing cannot accept a board.
"""
import hashlib
import json
import re
import uuid

POLICY = 'placement-annotation-proxies-v1'
SCOPE = 'ordinary-fixed-context-v1'
THT_SCOPE = 'ordinary-tht-fixed-context-v1'
MAX_NM = 2_000_000_000
MAX_CLEARANCE_NM = 10_000_000
MAX_OWNERS = 16  # Match the admitted fixed-context footprint scope.
MAX_ROWS = 512
MAX_MOVES = 16
MAX_CONTEXT_BYTES = 512 * 1024


def _need(value, message):
    if not value: raise ValueError(message)


def _identity(value):
    _need(type(value) is str and len(value) == 36, 'Canonical annotation UUID required')
    try: parsed = uuid.UUID(value)
    except ValueError: raise ValueError('Canonical annotation UUID required') from None
    _need(str(parsed) == value, 'Canonical annotation UUID required')
    return value


def _vector(value, length):
    _need(type(value) is list and len(value) == length
          and all(type(n) is int and abs(n) <= MAX_NM for n in value),
          'Bounded exact integer-nanometre annotation coordinates required')
    return value


def _box(value, *, positive=False):
    _vector(value, 4)
    _need(value[0] < value[2] and value[1] < value[3] if positive
          else value[0] <= value[2] and value[1] <= value[3], 'Ordered annotation box required')
    return value


def validate(context):
    """Reject incomplete/ambiguous wire records without trusting their origin."""
    keys = {'schema', 'policy', 'scope', 'source_board_sha256', 'outline_nm', 'silk_clearance_nm',
            'footprint_anchors_nm', 'movable_owners', 'rows'}
    _need(type(context) is dict and set(context) == keys and type(context['schema']) is int
          and context['schema'] == 1 and context['policy'] == POLICY and context['scope'] in (SCOPE, THT_SCOPE),
          'Complete annotation context policy/schema required')
    _need(type(context['source_board_sha256']) is str
          and re.fullmatch('[0-9a-f]{64}', context['source_board_sha256']) is not None,
          'Source-bound annotation SHA256 required')
    _box(context['outline_nm'], positive=True)
    clearance = context['silk_clearance_nm']
    _need(type(clearance) is int and 0 <= clearance <= MAX_CLEARANCE_NM,
          'Bounded exact Native silk clearance required')
    anchors = context['footprint_anchors_nm']; movable = context['movable_owners']; rows = context['rows']
    _need(type(anchors) is dict and 1 <= len(anchors) <= MAX_OWNERS, 'Bounded annotation owner census required')
    for owner, anchor in anchors.items(): _identity(owner); _vector(anchor, 2)
    _need(type(movable) is list and len(movable) <= MAX_OWNERS
          and all(type(owner) is str and owner in anchors for owner in movable)
          and len(set(movable)) == len(movable), 'Unique bound movable annotation owners required')
    _need(type(rows) is list and len(rows) <= MAX_ROWS, 'Bounded complete annotation row census required')
    identities = set(anchors)
    for row in rows:
        _need(type(row) is dict and row.get('kind') in ('silk', 'mask'), 'Supported annotation row kind required')
        expected = {'uuid', 'owner', 'kind', 'bbox_nm'} | ({'mask_expansion_nm'} if row['kind'] == 'mask' else set())
        _need(set(row) == expected, 'Complete annotation row fields required')
        identity = _identity(row['uuid']); _need(identity not in identities, 'Duplicate annotation UUID')
        identities.add(identity); owner = row['owner']
        _need(owner is None and row['kind'] == 'silk' or type(owner) is str and owner in anchors,
              'Annotation row owner has no source anchor')
        _box(row['bbox_nm'])
        anchor = anchors[owner] if owner is not None else [0, 0]
        _box([value + anchor[index % 2] for index, value in enumerate(row['bbox_nm'])])
        if row['kind'] == 'mask':
            expansion = row['mask_expansion_nm']
            _need(type(expansion) is int and abs(expansion) <= MAX_CLEARANCE_NM,
                  'Bounded exact Native mask expansion required')
    _need(len(json.dumps(context, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= MAX_CONTEXT_BYTES,
          'Annotation context byte ceiling exceeded')
    return context


def capture(native, pcbnew, raw, *, scope=SCOPE):
    """Read a job-owned Native snapshot through already qualified source seams.

    Getter names are pinned-wrapper interfaces; actual version-specific bbox
    behavior still requires separate Native controls. No files are read/written.
    """
    from experiments.placement_native_proposal_v1 import contract, ordinary_native
    from . import floor_context
    _need(contract.fixed_context_scope(scope), 'Explicit fixed-context annotation scope required')
    observed, _ = ordinary_native.capture(native, pcbnew, raw, contract, floor_context, scope=scope)
    _need(observed['scope'] == scope and observed['source_board_sha256'] == hashlib.sha256(raw).hexdigest(),
          'Annotation source witness differs')
    anchors = {row['uuid']: list(row['position_nm']) for row in observed['footprints']}
    movable = sorted(row['uuid'] for row in observed['footprints'] if row['placement_eligible'] is True)
    context = dict(schema=1, policy=POLICY, scope=scope, source_board_sha256=observed['source_board_sha256'],
                   outline_nm=list(observed['outline']['bounds_nm']),
                   silk_clearance_nm=native.GetDesignSettings().m_SilkClearance,
                   footprint_anchors_nm=anchors, movable_owners=movable, rows=[])

    def uid(item): return _identity(str(item.m_Uuid.AsString()))
    def xy(point): return _vector([point.x, point.y], 2)
    def owner_of(item):
        owner = item.GetParentFootprint()
        return None if owner is None else uid(owner)
    def bounds(item, *args):
        box = item.GetBoundingBox(*args)
        return _box([box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom()])
    def append(item, owner, kind, box, **extra):
        _need(len(context['rows']) < MAX_ROWS, 'Annotation row ceiling exceeded')
        anchor = anchors[owner] if owner is not None else [0, 0]
        context['rows'].append(dict(uuid=uid(item), owner=owner, kind=kind,
            bbox_nm=[value - anchor[index % 2] for index, value in enumerate(box)], **extra))
    def silk(item, owner, source):
        _need(uid(item) == source['uuid'] and owner_of(item) == owner, 'Native annotation identity/owner differs')
        if item.GetLayer() != pcbnew.F_SilkS: return
        _need(source['layer'] == 'F.SilkS', 'Native annotation source layer differs')
        if isinstance(item, pcbnew.PCB_TEXT):
            _need(source['kind'] in ('property', 'fp_text', 'gr_text') and xy(item.GetPosition()) == source['position_nm'],
                  'Native annotation text position differs')
            visible = item.IsVisible(); _need(type(visible) is bool, 'Exact Native annotation visibility required')
            if not visible: return
        else:
            _need(isinstance(item, pcbnew.PCB_SHAPE), 'Unsupported Native annotation shape')
        append(item, owner, 'silk', bounds(item))

    drawings = {row['uuid']: row for row in observed['outline']['primitives'] + observed['graphics']}
    actual_drawings = list(native.GetDrawings())
    _need(len(actual_drawings) == len(drawings), 'Native annotation board graphic census differs')
    seen = set()
    for item in actual_drawings:
        identity = uid(item); _need(identity in drawings and identity not in seen, 'Native annotation board UUID census differs')
        seen.add(identity); silk(item, None, drawings[identity])
    native_fps = list(native.GetFootprints()); by_fp = {uid(fp): fp for fp in native_fps}
    _need(len(by_fp) == len(native_fps) == len(anchors) and set(by_fp) == set(anchors), 'Native annotation footprint census differs')
    source_pads = {}
    for source in observed['footprints']:
        owner = source['uuid']; fp = by_fp[owner]
        _need(xy(fp.GetPosition()) == anchors[owner], 'Native annotation source anchor differs')
        graphics = {row['uuid']: row for row in (source['courtyard']['primitives'] if source['courtyard'] else [])
                    + [row for row in source['graphics'] if row['kind'] != 'property']}
        items = list(fp.GraphicalItems()); _need(len(items) == len(graphics), 'Native annotation footprint graphic census differs')
        seen = set()
        for item in items:
            identity = uid(item); _need(identity in graphics and identity not in seen, 'Native annotation graphic UUID census differs')
            seen.add(identity); silk(item, owner, graphics[identity])
        fields = {row['uuid']: row for row in source['graphics'] if row['kind'] == 'property' and row['uuid'] is not None}
        seen = set()
        for item in fp.GetFields():
            if item.GetLayer() != pcbnew.F_SilkS: continue
            identity = uid(item); _need(identity in fields and identity not in seen, 'Native visible silk field has no exact source UUID')
            seen.add(identity); silk(item, owner, fields[identity])
        _need(seen == {row['uuid'] for row in source['graphics'] if row['kind'] == 'property' and row['layer'] == 'F.SilkS'},
              'Native annotation silk field census differs')
        for pad in source['pads']:
            _need(pad['uuid'] not in source_pads, 'Duplicate source annotation pad UUID')
            source_pads[pad['uuid']] = (owner, pad)
    actual_pads = list(native.GetPads()); seen = set()
    _need(len(actual_pads) == len(source_pads), 'Native annotation pad census differs')
    for pad in actual_pads:
        identity = uid(pad); _need(identity in source_pads and identity not in seen, 'Native annotation pad UUID census differs')
        seen.add(identity); owner, source = source_pads[identity]
        _need(owner_of(pad) == owner and xy(pad.GetPosition()) == source['position_nm'], 'Native annotation pad owner/position differs')
        has_mask = pcbnew.F_Mask in set(pad.GetLayerSet().Seq())
        _need(has_mask == bool({'F.Mask', '*.Mask'}.intersection(source['layers'])), 'Native annotation mask layer census differs')
        if not has_mask: continue
        expansion = pad.GetSolderMaskExpansion(pcbnew.F_Cu)
        _need(type(expansion) is int and abs(expansion) <= MAX_CLEARANCE_NM, 'Bounded exact Native mask expansion required')
        box = bounds(pad, pcbnew.F_Cu)
        box = _box([box[0]-expansion, box[1]-expansion, box[2]+expansion, box[3]+expansion])
        append(pad, owner, 'mask', box, mask_expansion_nm=expansion)
    _need(all(xy(by_fp[owner].GetPosition()) == anchor for owner, anchor in anchors.items()),
          'Native annotation anchors changed during capture')
    context['rows'].sort(key=lambda row: row['uuid'])
    return validate(context)


def check_moves(context, moves):
    """Refuse new conservative conflicts; this never grants design approval."""
    validate(context); anchors = context['footprint_anchors_nm']
    _need(type(moves) is dict and len(moves) <= MAX_MOVES
          and all(type(owner) is str and owner in context['movable_owners'] for owner in moves),
          'Moves must bind only captured movable annotation owners')
    deltas = {None: [0, 0]}
    for owner, anchor in anchors.items():
        target = _vector(moves[owner], 2) if owner in moves else anchor
        deltas[owner] = _vector([target[i] - anchor[i] for i in range(2)], 2)
    def translated(row, *, moved):
        owner = row['owner']; anchor = anchors[owner] if owner is not None else [0, 0]
        delta = deltas[owner] if moved else [0, 0]
        return _box([value + anchor[i % 2] + delta[i % 2] for i, value in enumerate(row['bbox_nm'])])
    clearance = context['silk_clearance_nm']; board = context['outline_nm']; rows = context['rows']
    old = [translated(row, moved=False) for row in rows]; new = [translated(row, moved=True) for row in rows]
    for row, box in zip(rows, new):
        if row['kind'] == 'silk' and deltas[row['owner']] != [0, 0]:
            _need(board[0]+clearance <= box[0] <= box[2] <= board[2]-clearance
                  and board[1]+clearance <= box[1] <= box[3] <= board[3]-clearance,
                  'Moving silkscreen proxy exceeds the original board and silk clearance')
    def overlap(a, b):
        return not (a[2]+clearance < b[0] or b[2]+clearance < a[0]
                    or a[3]+clearance < b[1] or b[3]+clearance < a[1])
    inherited = 0
    moving = {index for index, row in enumerate(rows) if deltas[row['owner']] != [0, 0]}
    for i in sorted(moving):
        a = rows[i]
        for j in range(len(rows)):
            if j == i or j in moving and j < i: continue
            b = rows[j]
            if a['kind'] == b['kind'] == 'mask': continue
            if not overlap(new[i], new[j]): continue
            _need(overlap(old[i], old[j]) and deltas[a['owner']] == deltas[b['owner']],
                  'Proposed placement creates a conservative annotation conflict: ' + a['uuid'] + ' / ' + b['uuid'])
            inherited += 1
    return dict(schema=1, policy=POLICY, prefilter_passed=True, native_validation_required=True,
                source_board_sha256=context['source_board_sha256'],
                moved_owners=sorted(owner for owner in moves if deltas[owner] != [0, 0]),
                inherited_proxy_overlaps_retained=inherited)
