"""Bounded candidate proposer using the pinned upstream annealer, never a writer.

Only rectangular, initially feasible, explicitly selected placement is admitted.
The host adds constraint rejection/rollback and cooperative resource checks; the
upstream move generation, random sequence, cooling and objective remain reused.
No KiCad, shell, network, model, subprocess or filesystem operations occur here.
"""
import dataclasses
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


class _Stopped(Exception):
    pass


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise Refused(name + ': bounded exact integer required')


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
        return self._move(super()._try_nudge, temperature)

    def _try_rotate(self, temperature):
        return self._move(super()._try_rotate, temperature)

    def _try_swap(self):
        return self._move(super()._try_swap)


def propose(source, *, seed=0, steps=200, alternatives=2, seconds=2.0, cancel_event=None):
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
    try:
        check()
        # Keep preparation private to this search; the independent public
        # validator remains mandatory at each completed/final alternative.
        validate_move = _alternative_validator(facts)
        source_sha256 = digest(facts)
        check()
        for index in range(alternatives):
            check(); counts['attempted_alternatives'] += 1
            board = _model(facts); static = _engine_facts(board)
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
        status = 'proposals_ready' if found else 'no_changed_alternative'
    except _Stopped as exc:
        status = str(exc); found = []
    if encoded(source) != original_bytes:
        raise Refused('Caller source facts changed during search')
    # Validate every output again independently after the whole search.
    for item in found:
        validate_alternative(facts, item['candidate'])
    wall, cpu = time.monotonic() - started, time.process_time() - cpu_started
    if wall >= seconds or cpu >= seconds:
        status = 'budget_exhausted'; found = []
    if cancel_event is not None and cancel_event.is_set():
        status = 'cancelled'; found = []
    return dict(schema=1, kind='constrained-placement-engine-only-prototype', status=status,
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
                        'No side flips, polygons, cutouts, rigid groups or initially infeasible placement.',
                        'The reused objective conservatively penalizes rectangle proximity across both sides.',
                        'No changed alternative is not a proof of infeasibility; no full-board or live application.'])
