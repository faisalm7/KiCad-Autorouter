"""Bounded candidate proposer using the pinned upstream annealer, never a writer.

Rectangular selected placement normally requires a feasible start. An explicit
bounded region-only initializer may first supply a fully checked target pose.
The host adds constraint rejection/rollback and cooperative resource checks; the
upstream move generation, random sequence, cooling and objective remain reused.
No KiCad, shell, network, model, subprocess or filesystem operations occur here.
"""
import copy
import dataclasses
import itertools
from decimal import Context, Decimal, localcontext
import threading
import time

from .constraints import (Refused, digest, encoded, immovable, original_alternative,
                          prepare, validate_alternative, _alternative_validator)
from .vendor.anneal import Annealer
from .vendor.model import Board, Component, Pad

UPSTREAM_COMMIT = '12bb5556fc5c1db287285425aea49a1d79dc8ffa'
MAX_STEPS = 1000
MAX_ALTERNATIVES = 3
MAX_SECONDS = 5.0
REGION_INITIALIZATION_POLICY = 'selected-target-region-initialization-v1'
MAX_REGION_SEED_CANDIDATES = 256


class _Stopped(Exception):
    pass


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise Refused(name + ': bounded exact integer required')


def source_context(source, *, region_initialization=None):
    """Check source context and return its original pose, never target authority.

    Only an explicit policy may treat the selected target region as distinct
    from source legality. The returned pose still binds the ORIGINAL facts and
    can remain outside that target region; callers must validate actual targets.
    """
    facts = prepare(source)
    original = original_alternative(facts)
    if region_initialization is None:
        return validate_alternative(facts, original)
    if type(region_initialization) is not str or region_initialization != REGION_INITIALIZATION_POLICY:
        raise Refused('Unsupported region initialization policy')
    if len(facts['selected']) > 2 or facts['groups']:
        raise Refused('Region initialization requires at most two independent selected components')
    if set(facts['selected']) & immovable(facts):
        raise Refused('Region initialization cannot move fixed/locked/tracked components')
    context = copy.deepcopy(facts)
    for component in context['components']:
        if component['id'] in facts['selected']:
            component['allowed_region_mm'] = list(facts['board']['bounds_mm'])
    # Keep every other source constraint, including schema3's existing exact
    # selected-copper exception. This is NOT a validated final target pose.
    validate_alternative(context, original_alternative(context))
    return original


def _region_seed(facts, initial, validate, check, record):
    """First valid finite joint target; no score-based choice or source repair."""
    components = {row['id']: row for row in facts['components']}
    options = []
    board = facts['board']['bounds_mm']; gap = facts['clearance_mm']
    for identity in facts['selected']:
        check(); row = components[identity]; width, height = row['size_mm']
        if row['rotation_deg'] in (90, 270): width, height = height, width
        axes = []
        for axis, extent in enumerate((width, height)):
            low = max(row['allowed_region_mm'][axis], board[axis] + gap) + extent/2
            high = min(row['allowed_region_mm'][axis+2], board[axis+2] - gap) - extent/2
            if low > high: return None
            values = [min(high, max(low, row['position_mm'][axis])), (low+high)/2, low, high]
            axes.append(list(dict.fromkeys(values)))
        options.append(list(itertools.product(*axes)))
    for positions in itertools.product(*options):
        check(); record['candidates_checked'] += 1
        assert record['candidates_checked'] <= MAX_REGION_SEED_CANDIDATES
        candidate = copy.deepcopy(initial)
        targets = dict(zip(facts['selected'], positions))
        for row in candidate['transforms']:
            if row['component_id'] in targets:
                row['x_mm'], row['y_mm'] = targets[row['component_id']]
        try:
            validate(candidate)
        except Refused:
            check(); continue
        check()
        candidate = validate_alternative(facts, candidate)  # Independent chosen-seed fence.
        check()
        record['seed_publicly_validated'] = True
        record['seed'] = copy.deepcopy(candidate)
        return candidate
    return None


def _model(facts):
    # Opaque tokens prevent upstream power-name/decoupling heuristics from
    # assigning electrical meaning or dropping a supplied net from the objective.
    nets = sorted({p['net'] for c in facts['components'] for p in c['pads'] if p['net'] is not None})
    tokens = {net: 'n' + str(i).zfill(5) for i, net in enumerate(nets)}
    fixed = immovable(facts)
    board = Board(*facts['board']['bounds_mm'])
    for c in sorted(facts['components'], key=lambda c: c['id']):
        pads = [Pad(p['id'], '' if p['net'] is None else tokens[p['net']], *p['offset_mm'])
                for p in sorted(c['pads'], key=lambda p: p['id'])]
        board.components[c['id']] = Component(c['id'], *c['size_mm'], pads=pads,
            x=c['position_mm'][0], y=c['position_mm'][1], rot=c['rotation_deg'],
            locked=c['id'] in fixed, height=0.0)
    return board


def _engine_facts(board):
    # All identity/connectivity/geometry/model fields except permitted transforms.
    value = dataclasses.asdict(board)
    for c in value['components'].values():
        for key in ('x', 'y', 'rot'):
            del c[key]
    return value


def _candidate(facts, board, *, source_sha256=None):
    return dict(schema=1, source_sha256=digest(facts) if source_sha256 is None else source_sha256, transforms=[
        dict(component_id=c['id'], x_mm=board.components[c['id']].x,
             y_mm=board.components[c['id']].y, rotation_deg=board.components[c['id']].rot,
             side=c['side']) for c in sorted(facts['components'], key=lambda c: c['id'])])


class _ConstrainedAnnealer(Annealer):
    def __init__(self, board, facts, seed, check, counts, *, validator=None, source_sha256=None):
        self._facts, self._check, self._counts = facts, check, counts
        check()
        self._validate = _alternative_validator(facts) if validator is None else validator
        self._source_sha256 = digest(facts) if source_sha256 is None else source_sha256
        super().__init__(board, margin=facts['clearance_mm'], seed=seed,
                         channel_scale=0.0, cohesion_scale=0.0, cross_weight=0.0)
        # Identity-neutral tokens plus empty electrical annotations must not
        # trigger hidden net omission, decoupling or connector policies.
        assert not self.decap
        assert set(self.net_members) == set(board.nets())
        assert all(not c.is_connector and not c.edge for c in self.comps)
        self._rigid = tuple(board.components[name] for name in facts['groups'][0]['members']) if facts['groups'] else ()
        rigid_ids = {c.ref for c in self._rigid}
        self._rigid_origins = {row['id']: tuple(Decimal(str(n)) for n in row['position_mm'])
                               for row in facts['components'] if row['id'] in rigid_ids}
        check()

    def _quality(self):
        self._check()
        quality = super()._quality()
        self._check()
        return quality

    def _move(self, method, *args):
        self._check()
        before = {ref: (c.x, c.y, c.rot) for ref, c in self.board.components.items()}
        self._counts['attempted_moves'] += 1
        result = method(*args)
        self._check()
        try:
            self._validate(_candidate(self._facts, self.board, source_sha256=self._source_sha256))
        except Refused:
            # Restore complete poses, including position changes caused by the
            # upstream rotation/swap clamps; do not trust its partial reverts.
            for ref, (x, y, rot) in before.items():
                c = self.board.components[ref]
                c.x, c.y, c.rot = x, y, rot
            self._counts['constraint_rejected_moves'] += 1
            result = None
        self._check()
        return result

    def _try_nudge(self, temperature):
        if self._rigid:
            before = {ref: (c.x, c.y, c.rot) for ref, c in self.board.components.items()}
            try:
                return self._move(self._nudge_rigid_group, temperature)
            except BaseException:
                for ref, (x, y, rot) in before.items():
                    c = self.board.components[ref]
                    c.x, c.y, c.rot = x, y, rot
                raise
        return self._move(super()._try_nudge, temperature)

    def _nudge_rigid_group(self, temperature):
        with localcontext(Context(prec=50)):
            return self._nudge_rigid_group_context(temperature)

    def _nudge_rigid_group_context(self, temperature):
        """One shared integer-nm offset; reuse upstream cost and acceptance.

        Individual clamping would shear the group. Existing whole-candidate
        validation instead rejects and rolls back any infeasible translation.
        """
        members = self._rigid
        before = [(c, c.x, c.y) for c in members]
        before_cost = self.local_cost(members)
        leader = members[0]; origin = self._rigid_origins[leader.ref]
        amp = max(1.0, temperature)
        delta_nm = [int(((Decimal(str(current))-origin[i]
                         + Decimal(str((self.rng.random()-0.5)*2*amp)))*1000000).to_integral_value())
                    for i, current in enumerate((leader.x, leader.y))]
        for c in members:
            x, y = self._rigid_origins[c.ref]
            c.x = float(x + Decimal(delta_nm[0])/1000000)
            c.y = float(y + Decimal(delta_nm[1])/1000000)
        after_cost = self.local_cost(members)
        def revert():
            for c, x, y in before:
                c.x, c.y = x, y
        return self._accept(after_cost-before_cost, temperature, revert)

    def _try_rotate(self, temperature):
        if self._rigid:
            self._check(); return None
        return self._move(super()._try_rotate, temperature)

    def _try_swap(self):
        if self._rigid:
            self._check(); return None
        return self._move(super()._try_swap)


def propose(source, *, seed=0, steps=200, alternatives=2, seconds=2.0, cancel_event=None,
            region_initialization=None):
    """Return at most three independently valid, source-bound transform alternatives.

    Deadline/cancellation checks run before and after each bounded upstream move
    and quality evaluation. This is a cooperative single-thread CPU/wall bound,
    not an OS quota. Cancellation/budget exhaustion discards all alternatives.
    Empty output is not an infeasibility proof. No result authorizes application.
    """
    started, cpu_started = time.monotonic(), time.process_time()
    _integer(seed, 0, 2**31 - 1, 'seed')
    _integer(steps, 1, MAX_STEPS, 'steps')
    _integer(alternatives, 1, MAX_ALTERNATIVES, 'alternatives')
    _integer(seed + alternatives - 1, 0, 2**31 - 1, 'last alternative seed')
    if type(seconds) not in (int, float) or not 0.01 <= seconds <= MAX_SECONDS:
        raise Refused('seconds: finite 0.01..5 cooperative budget required')
    if cancel_event is not None and type(cancel_event) is not threading.Event:
        raise Refused('A threading.Event cancellation token is required')
    if region_initialization is not None and (type(region_initialization) is not str
            or region_initialization != REGION_INITIALIZATION_POLICY):
        raise Refused('Unsupported region initialization policy')

    def check():
        if cancel_event is not None and cancel_event.is_set():
            raise _Stopped('cancelled')
        if time.monotonic() - started >= seconds or time.process_time() - cpu_started >= seconds:
            raise _Stopped('budget_exhausted')

    original_bytes = encoded(source)
    facts = prepare(source)
    initial = original_alternative(facts)
    # A deliberate first-scope limit: no heuristic repair of initially illegal
    # rectangles, or moving a component through a prohibited placement region.
    if region_initialization is None:
        try:
            validate_alternative(facts, initial)
        except Refused as exc:
            raise Refused('Initially feasible rectangular placement required: ' + str(exc)) from exc
    free_count = len(facts['components']) - len(immovable(facts))
    if free_count < 2:
        raise Refused('Pinned upstream annealer requires at least two movable components')
    found, fingerprints = [], set()
    counts = dict(attempted_moves=0, constraint_rejected_moves=0, attempted_alternatives=0)
    status = 'no_changed_alternative'
    initialization = (dict(policy=region_initialization, status='not_started',
        source_context_only=True, original_facts_sha256=initial['source_sha256'],
        candidates_checked=0, candidate_limit=MAX_REGION_SEED_CANDIDATES,
        seed_publicly_validated=False, native_validation_performed=False,
        execution_authorized=False, approval_granted=False) if region_initialization is not None else None)
    start_pose = initial
    try:
        check()
        # Keep preparation private to this search; the independent public
        # validator remains mandatory at each completed/final alternative.
        validate_move = _alternative_validator(facts)
        source_sha256 = digest(facts)
        check()
        if region_initialization is not None:
            initialization['status'] = 'checking_source'
            source_context(facts, region_initialization=region_initialization)
            check()
            try:
                validate_alternative(facts, initial)
                initialization['status'] = 'already_feasible'
            except Refused:
                check()
                start_pose = _region_seed(facts, initial, validate_move, check, initialization)
                initialization['status'] = 'seed_ready' if start_pose is not None else 'no_feasible_region_seed'
            check()
        for index in range(alternatives if start_pose is not None else 0):
            check(); counts['attempted_alternatives'] += 1
            board = _model(facts)
            if region_initialization is not None:
                for transform in start_pose['transforms']:
                    component = board.components[transform['component_id']]
                    component.x, component.y, component.rot = transform['x_mm'], transform['y_mm'], transform['rotation_deg']
            static = _engine_facts(board)
            engine = _ConstrainedAnnealer(board, facts, seed + index, check, counts,
                                         validator=validate_move, source_sha256=source_sha256)
            before_quality = engine._quality()
            engine.run(steps=steps)
            check()
            if _engine_facts(board) != static:
                raise Refused('Engine changed component/pad identities, nets, geometry or locks')
            candidate = validate_alternative(facts, _candidate(facts, board))
            key = digest(candidate)
            if candidate != initial and key not in fingerprints:
                fingerprints.add(key)
                found.append(dict(candidate=candidate, seed=seed + index,
                                  before_proxy_cost=before_quality, after_proxy_cost=engine._quality()))
            check()
        status = ('no_feasible_region_seed' if start_pose is None else
                  'proposals_ready' if found else 'no_changed_alternative')
    except _Stopped as exc:
        status = str(exc); found = []
        if initialization is not None:
            initialization['status'] = status
            initialization.pop('seed', None); initialization['seed_publicly_validated'] = False
    if encoded(source) != original_bytes:
        raise Refused('Caller source facts changed during search')
    # Validate every output again independently after the whole search.
    try:
        for item in found:
            if region_initialization is not None: check()
            validate_alternative(facts, item['candidate'])
            if region_initialization is not None: check()
    except _Stopped as exc:
        status = str(exc); found = []
    if region_initialization is not None and encoded(source) != original_bytes:
        raise Refused('Caller source facts changed during final region readback')
    wall, cpu = time.monotonic() - started, time.process_time() - cpu_started
    if wall >= seconds or cpu >= seconds:
        status = 'budget_exhausted'; found = []
    if cancel_event is not None and cancel_event.is_set():
        status = 'cancelled'; found = []
    result = dict(schema=1, kind='constrained-placement-engine-only-prototype', status=status,
                source_sha256=digest(facts), upstream_commit=UPSTREAM_COMMIT,
                alternatives=found, bounds=dict(seed=seed, steps_per_alternative=steps,
                    alternatives=alternatives, wall_and_cpu_seconds=seconds),
                counts=counts, sampled_wall_seconds=wall, sampled_cpu_seconds=cpu,
                fixed_components=sorted(immovable(facts)), source_unchanged=True,
                supplied_connectivity_and_pad_identities_preserved=True, native_validation_performed=False,
                execution_authorized=False, approval_granted=False,
                limits=['Rectangular proxy geometry only; no pad-shape, copper or Native legality claim.',
                        'Every component on any tracked net is immovable; supplied track witnesses are not Native connectivity proof.',
                        'Track geometry is not modeled; any placement obstacle corridor must be supplied as a rectangular keepout.',
                        ('Only one rigid selected translation group; no group rotation, side flips, polygons, cutouts or initially infeasible placement.'
                         if facts['groups'] else 'No side flips, polygons, cutouts, rigid groups or initially infeasible placement.'),
                        'The reused objective conservatively penalizes rectangle proximity across both sides.',
                        'No changed alternative is not a proof of infeasibility; no full-board or live application.'])
    if initialization is not None:
        if status in ('cancelled', 'budget_exhausted'):
            initialization.update(status=status, seed_publicly_validated=False)
            initialization.pop('seed', None)
        result['region_initialization'] = initialization
        result['limits'][3] = ('Explicit region-only initialization for at most two independent selected parts; '
            'physical source conflicts are not repaired. A finite seed miss is not infeasibility proof.')
        result['limits'].append('Initialization and optimization share the same time budget. A region-valid '
            'automatic seed is a proposal, not proof of Native legality or improved electrical placement.')
    return result
