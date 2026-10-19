"""Private selected-7 Improve incumbent authority; no parent admission.

A trusted future parent passes this live object explicitly. JSON, pathnames and
sidecars are detection/binding material, never factories for caller authority.
The parent/Preview/export guards remain closed in this prerequisite slice.
"""
from dataclasses import dataclass, field
import hashlib
import math
import os
from pathlib import Path
import re
import stat
import time
from . import config as c, provenance as pv

POLICY = 'selected-native7-single-improve-child-v1'
SIDECAR = 'improve-child-context.json'
RESERVE_SECONDS = 25


def _encode(value):
    from .floor_route import canonical
    return canonical(value)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _owned(path, *, directory=False):
    from .pipeline import Rejected
    pv.canonical(path)
    info = path.lstat()
    if (info.st_uid != os.getuid() or not (stat.S_ISDIR(info.st_mode) if directory
            else stat.S_ISREG(info.st_mode) and info.st_nlink == 1)):
        raise Rejected('Improve child requires owned canonical regular material')
    return info


def _inventory(path):
    from .placement_clearance import inventory
    _owned(path, directory=True)
    result = inventory(path)
    for name in result:
        target = path / name
        _owned(target)
        for parent in target.parents:
            if parent == path:break
            _owned(parent, directory=True)
    return result


def _check_parent_owner(owner, parent):
    """Retain exact live types; numeric equality cannot renew this witness."""
    from . import handoff as h, pipeline as p
    if (type(owner) is not dict or set(owner) != {'created', 'destination', 'directory_identity'}
            or owner['created'] is not True or not isinstance(owner['destination'], Path)
            or owner['destination'] != parent or type(owner['directory_identity']) is not tuple
            or len(owner['directory_identity']) != 2
            or any(type(value) is not int or value < 0 for value in owner['directory_identity'])
            or h.owned_destination(owner) != parent):
        raise p.Rejected('exact captured Improve parent owner required')


@dataclass(frozen=True)
class _Context:
    source: Path
    parent: Path
    parent_owner: dict
    method_seconds: float
    assigned_seconds: float
    allocation: dict
    tools: dict
    source_hashes: dict
    _inputs: dict = field(init=False, repr=False)
    _owner: dict = field(init=False, repr=False)
    _seal: str = field(init=False, repr=False)

    def __post_init__(self):
        from . import handoff as h, pipeline as p
        if (not isinstance(self.source, Path) or not isinstance(self.parent, Path)
                or not _number(self.method_seconds) or not 30 <= self.method_seconds <= 900
                or not _number(self.assigned_seconds) or not 5 <= self.assigned_seconds <= 875
                or type(self.allocation) is not dict or set(self.allocation) != {'elapsed_wall_seconds', 'elapsed_cpu_seconds'}
                or any(not _number(value) or value < 0 for value in self.allocation.values())
                or self.assigned_seconds != min(self.method_seconds - self.allocation['elapsed_wall_seconds'],
                    self.method_seconds - self.allocation['elapsed_cpu_seconds']) - RESERVE_SECONDS
                or type(self.tools) is not dict or type(self.source_hashes) is not dict):
            raise p.Rejected('exact Improve child context and reserved allocation required')
        pv.canonical(self.source); pv.canonical(self.parent)
        if (self.source.suffix != '.kicad_pcb'
                or self.source.parent == self.parent or self.source.parent in self.parent.parents
                or self.parent in self.source.parents
                or not 1 <= len(self.source_hashes) <= 2000
                or any(self.source.with_suffix(suffix).name not in self.source_hashes
                    for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'))):
            raise p.Rejected('Improve child requires a complete source outside its owned parent')
        for name, digest in self.source_hashes.items():
            if (type(name) is not str or str(Path(name)) != name or Path(name).is_absolute()
                    or '..' in Path(name).parts or type(digest) is not str or pv._DIGEST.fullmatch(digest) is None):
                raise p.Rejected('invalid Improve child source inventory')
        # strategy.prune captures its fresh protected Job's owner before code,
        # preferences and snapshot. Accept that exact live caller snapshot; do
        # not recapture a replacement directory or assume GUI/CLI namespaces.
        owner = self.parent_owner
        _check_parent_owner(owner, self.parent)
        _owned(self.parent, directory=True)
        object.__setattr__(self, '_owner', dict(owner))
        object.__setattr__(self, '_inputs', self._material())
        seal = _encode(self.record())
        if len(seal.encode()) > 512 * 1024:raise p.Rejected('Improve child context exceeds bound')
        object.__setattr__(self, '_seal', seal)
        self.check()

    @property
    def output(self):
        return self.parent / 'incumbent'

    def _material(self):
        from . import pipeline as p, preferences as pref
        from .layer_policy import _two_copper_table
        from .local_settings import policy_declaration
        _owned(self.parent, directory=True)
        if _inventory(self.source.parent) != self.source_hashes or _inventory(self.parent / 'snapshot') != self.source_hashes:
            raise p.Rejected('Improve source/parent snapshot changed')
        # This slice deliberately excludes class-bearing, hierarchy, alias and
        # four-layer inputs. No existing ordinary capability guard is widened.
        tree = p.preflight(self.source, task_scope=('whole_board_unlocked_routing', 'native', 'source_all'))
        _two_copper_table(tree)
        if p.netclass_policy(self.source) is not None or p.check_schematic_class_support(self.source) is not None:
            raise p.Rejected('Improve child requires the unflagged single Default scope')
        expected = {**pref.DEFAULTS, 'seconds': self.method_seconds, 'profile': 'tuned'}
        preferences = self.parent / 'pruning-preferences.json'
        _owned(preferences)
        raw = pv.read_bytes(preferences, pref.MAX_SNAPSHOT_BYTES)
        pref.readback(raw, expected)
        pins = self.tools.get('implementation_sha256')
        if (type(pins) is not dict or not pins or len(pins) > 256
                or any(type(name) is not str or Path(name).parts != ('autorouter', Path(name).name)
                    or not name.endswith('.py') or type(digest) is not str or pv._DIGEST.fullmatch(digest) is None
                    for name, digest in pins.items())):
            raise p.Rejected('invalid Improve implementation pins')
        expected_code = {Path(name).name: digest for name, digest in pins.items()}
        if _inventory(self.parent / 'code') != expected_code:
            raise p.Rejected('Improve parent code snapshot changed')
        for name, declaration in (('pipeline.py', 'NATIVE7_IMPROVE_CHILD_POLICY'), ('_improve_context.py', 'POLICY')):
            if policy_declaration(pv.read_bytes(self.parent / 'code' / name), name=declaration, expected=POLICY) != POLICY:
                raise p.Rejected('Improve child source policy differs')
        if 'strategy.py' not in expected_code:raise p.Rejected('Improve parent source pin missing')
        return dict(snapshot=self.source_hashes, code=expected_code,
                    preferences_sha256=hashlib.sha256(raw).hexdigest(), effective=expected)

    def record(self):
        return dict(schema=1, policy=POLICY, runtime=str(c.ROOT), source=str(self.source),
            parent=str(self.parent), output=str(self.output), role='incumbent', proposal_policy='single',
            input_policy='native', scope='whole_board_unlocked_routing', profile='tuned', adapter='both',
            layers='source_all', scoring_variant=None, method_seconds=self.method_seconds,
            assigned_seconds=self.assigned_seconds, allocation=self.allocation,
            finalization_reserve_seconds=RESERVE_SECONDS, source_hashes=self.source_hashes,
            tools_sha256=hashlib.sha256(_encode(self.tools).encode()).hexdigest(),
            inputs=self._inputs, directory_identity=self._owner['directory_identity'])

    def check(self):
        from . import handoff as h, pipeline as p
        _check_parent_owner(self.parent_owner, self.parent)
        if (type(self.parent_owner) is not dict or self.parent_owner != self._owner
                or _encode(self.record()) != self._seal):
            raise p.Rejected('Improve caller context or captured owner changed')
        if h.owned_destination(self._owner) != self.parent:raise p.Rejected('Improve parent replaced')
        identity = self.tools.get('source_provenance')
        if (c.NATIVE_VERSION != '10.0.7' or self.tools.get('kicad') != '10.0.7'
                or type(identity) is not dict or identity.get('kind') != pv.KIND
                or identity.get('native_version') != '10.0.7'
                or type(identity.get('manifest_sha256')) is not str or pv._DIGEST.fullmatch(identity['manifest_sha256']) is None
                or self.tools.get('native_improve_child_policy') != POLICY or p.tool_manifest() != self.tools
                or self._material() != self._inputs):
            raise p.Rejected('Improve selected runtime/source/parent material changed')
        return self


def require(context):
    from .pipeline import Rejected
    if type(context) is not _Context:raise Rejected('exact live Improve child context required')
    return context.check()


@dataclass(frozen=True)
class _Budget:
    """Live execution clocks from the actual parent Job; never from a receipt.

    The retained Context describes lineage. This separate object supplies the
    changing work limit, including time spent constructing/checking Context.
    CPU is checked cooperatively before workers and at publication, not
    preempted by the OS. Existing polling overshoot limits still apply.
    """
    context: _Context
    parent_job: object
    children_start: float
    _clocks: tuple = field(init=False, repr=False)

    def __post_init__(self):
        from . import pipeline as p
        require(self.context)
        job = self.parent_job
        if (type(job) is not p.Job or job.out != self.context.parent
                or job.seconds != self.context.method_seconds
                or job.protect_local_settings is not True or job.native_toolchain is not None
                or job.experimental_schematic_parity is not False
                or not _number(self.children_start) or self.children_start < 0
                or not _number(job.child_cpu_started) or job.child_cpu_started != self.children_start
                or any(not _number(value) or value < 0 for value in
                    (job.started, job.deadline, job.cpu_started))
                or job.deadline != job.started + job.seconds):
            raise p.Rejected('live exact Improve parent Job budget required')
        _check_parent_owner(job._local_settings_owner, self.context.parent)
        if job._local_settings_owner != self.context._owner:
            raise p.Rejected('Improve parent Job owner differs from Context')
        object.__setattr__(self, '_clocks', (job.started, job.deadline, job.cpu_started,
                                            job.seconds, job.child_cpu_started))
        self.check()

    def check(self):
        from . import pipeline as p
        job = self.parent_job
        if (type(self.context) is not _Context or type(job) is not p.Job
                or (job.started, job.deadline, job.cpu_started, job.seconds, self.children_start) != self._clocks
                or not _number(job.child_cpu_started) or job.child_cpu_started != self.children_start
                or job.out != self.context.parent or job.protect_local_settings is not True
                or job.native_toolchain is not None or job.experimental_schematic_parity is not False
                or _encode(self.context.record()) != self.context._seal):
            raise p.Rejected('Improve parent execution budget changed')
        _check_parent_owner(self.context.parent_owner, self.context.parent)
        _check_parent_owner(job._local_settings_owner, self.context.parent)
        _owned(self.context.parent, directory=True)
        if self.context.parent_owner != self.context._owner or job._local_settings_owner != self.context._owner:
            raise p.Rejected('Improve parent execution owner changed')
        return self

    def remaining(self, *, work=True):
        from . import pipeline as p
        from .floor_route import child_cpu
        self.check()
        if type(work) is not bool:raise p.Rejected('explicit Improve work-budget scope required')
        job = self.parent_job
        parent = time.process_time() - job.cpu_started
        children = child_cpu() - self.children_start
        if not _number(parent) or not _number(children) or parent < 0 or children < 0:
            raise p.Rejected('invalid live Improve full CPU accounting')
        reserve = RESERVE_SECONDS if work else 0
        return min(job.deadline - time.monotonic() - reserve,
                   job.seconds - parent - children - reserve)

    def _work_job(self, job):
        from . import pipeline as p
        if type(job) is not p.Job:raise p.Rejected('exact Improve worker Job required')
        if job is self.parent_job:return False
        if job.out == self.context.output:return True
        if (job.out.parent == self.context.parent / 'trials'
                and re.fullmatch(r'trial-(?:00[0-2][0-9]|003[01])', job.out.name)):
            return True
        raise p.Rejected('Improve worker escaped fixed parent lineage')

    def attach(self, job):
        from . import pipeline as p
        self.check()
        work = self._work_job(job)
        prior = getattr(job, '_inherited_budget', None)
        if (job.protect_local_settings is not True or job.native_toolchain is not None
                or job.experimental_schematic_parity is not False
                or prior is not None and prior is not self):
            raise p.Rejected('Improve worker cannot mix execution budgets')
        _check_parent_owner(job._local_settings_owner, job.out)
        if work:job.deadline = min(job.deadline, self.parent_job.deadline - RESERVE_SECONDS)
        job._inherited_budget = self
        return job


def require_budget(budget, context):
    from .pipeline import Rejected
    if type(budget) is not _Budget or budget.context is not context:
        raise Rejected('exact live Improve execution budget required')
    return budget.check()


def marked(directory, data=None):
    return os.path.lexists(Path(directory) / SIDECAR) or data is not None and 'native_improve_child' in data


def authorize(context, source, output, seconds, keep, adapter, profile, scoring, guidance, extras):
    from .pipeline import Rejected
    require(context)
    if (Path(source) != context.source or Path(output) != context.output or os.path.lexists(context.output)
            or type(seconds) not in (int, float) or seconds != context.assigned_seconds
            or keep is not False or type(adapter) is not str or adapter != 'both'
            or type(profile) is not str or profile != 'tuned' or scoring is not None
            or type(guidance) is not str or guidance != 'native' or any(value is not None for value in extras)):
        raise Rejected('unsupported Improve incumbent child request')


def bind(directory, data, context):
    from .pipeline import Rejected
    require(context)
    if Path(directory) != context.output:raise Rejected('Improve child output differs')
    raw = (_encode(context.record()) + '\n').encode()
    target = Path(directory) / SIDECAR
    with target.open('xb') as stream:stream.write(raw)
    data['native_improve_child'] = dict(policy=POLICY, file=SIDECAR, sha256=hashlib.sha256(raw).hexdigest())


def check_record(directory, data, context):
    from . import pipeline as p
    from .floor_route import read_json
    directory = Path(directory)
    if context is None:
        if marked(directory, data):raise p.Rejected('Improve child requires its live caller context')
        return False
    require(context)
    raw = pv.read_bytes(directory / SIDECAR, 512 * 1024)
    marker = dict(policy=POLICY, file=SIDECAR, sha256=hashlib.sha256(raw).hexdigest())
    forbidden = ('strategy', 'input_policy', 'guidance_policy', 'routing_preferences', 'pruning_preferences',
        'pruning_preferences_policy', 'incumbent_scoring_variant', 'incumbent_scoring_contract',
        'incumbent_receipt_sha256', 'comparison_route', 'production_admitted', 'diagnostic_schema',
        'production_qualified', 'experimental_route_policy', 'experimental_native_toolchain',
        'experimental_schematic_parity_policy', 'engine_fanout_override', 'engine_optimizer_override',
        'engine_angle_binding', 'engine_planning_clearance_margin_nm', 'engine_global_width_policy')
    if (directory != context.output or type(data.get('schema')) is not int or data['schema'] != 1
            or data.get('native_improve_child') != marker or _encode(read_json(directory / SIDECAR)) != context._seal
            or any(key in data for key in forbidden) or data.get('source') != str(context.source)
            or data.get('source_hashes') != context.source_hashes or data.get('tools') != context.tools
            or data.get('baseline') != p.engine_baseline('tuned', 'both') or data.get('engine_profile') != 'tuned'
            or data.get('adapter') != 'both' or data.get('scope') != 'whole_board_unlocked_routing'
            or data.get('scoring_variant') is not None or data.get('budget_seconds') != context.assigned_seconds
            or data.get('cpu_budget_seconds') != context.assigned_seconds
            or _inventory(directory / 'code') != context._inputs['code']):
        raise p.Rejected('Improve child receipt differs from live caller contract')
    return True
