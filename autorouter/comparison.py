"""Caller-owned fixed comparison Route; never ordinary product admission.

This first slice has no portfolio, review or export authority. Full native and
original-design checks remain in pipeline.py; local evidence is not authenticated.
"""
from dataclasses import dataclass, field
import hashlib
import math
import os
from pathlib import Path
from . import config as c, provenance as pv

POLICY = 'selected-native7-fixed-comparison-v1'
PREFIX = 'native7-comparison-'
SIDECAR = 'comparison-context.json'


def encode(value):
    from .floor_route import canonical
    return canonical(value)


@dataclass(frozen=True)
class Context:
    source: Path
    output: Path
    profile: str
    seconds: float
    tools: dict
    source_hashes: dict
    _seal: str = field(init=False, repr=False)

    def __post_init__(self):
        from .pipeline import Rejected
        if (not isinstance(self.source,Path) or not isinstance(self.output,Path)
                or self.profile not in ('standard','tuned') or type(self.profile) is not str
                or type(self.seconds) not in (int,float) or not math.isfinite(self.seconds) or not 5 <= self.seconds <= 900
                or type(self.tools) is not dict or type(self.source_hashes) is not dict):
            raise Rejected('exact typed fixed comparison context required')
        pv.canonical(self.source); pv.canonical(self.output)
        if (self.source.suffix != '.kicad_pcb' or not any(part.startswith(PREFIX) for part in self.output.parts)
                or c.ROOT / '.runs' not in self.output.parents
                or self.source.parent == self.output or self.source.parent in self.output.parents
                or not 1 <= len(self.source_hashes) <= 2000
                or any(self.source.with_suffix(s).name not in self.source_hashes for s in ('.kicad_pcb','.kicad_pro','.kicad_sch'))):
            raise Rejected('comparison requires complete source and reserved owned output')
        for name, digest in self.source_hashes.items():
            if (type(name) is not str or str(Path(name)) != name or Path(name).is_absolute() or '..' in Path(name).parts
                    or type(digest) is not str or pv._DIGEST.fullmatch(digest) is None):
                raise Rejected('invalid comparison source inventory')
        sealed = encode(self.record())
        if len(sealed.encode()) > 512 * 1024:raise Rejected('comparison context exceeds bound')
        object.__setattr__(self, '_seal', sealed)

    def record(self):
        return dict(policy=POLICY, runtime=str(c.ROOT), source=str(self.source), output=str(self.output),
            profile=self.profile, seconds=self.seconds, source_hashes=self.source_hashes,
            tools_sha256=hashlib.sha256(encode(self.tools).encode()).hexdigest())

    def check(self):
        from . import pipeline as p, placement_clearance as pc
        if encode(self.record()) != self._seal:raise p.Rejected('comparison caller expectations changed')
        pv.canonical(self.source); pv.canonical(self.output)
        identity=self.tools.get('source_provenance')
        if (c.NATIVE_VERSION != '10.0.7' or self.tools.get('kicad') != '10.0.7'
                or type(identity) is not dict or identity.get('kind') != pv.KIND or identity.get('native_version') != '10.0.7'
                or self.tools.get('comparison_route_policy') != POLICY
                or p.tool_manifest() != self.tools or pc.inventory(self.source.parent) != self.source_hashes):
            raise p.Rejected('comparison selected runtime/tools/source changed')


def require_context(context):
    from .pipeline import Rejected
    if type(context) is not Context:raise Rejected('exact explicit comparison caller context required')
    context.check()
    return context


def marked(directory, data=None):
    directory=Path(directory)
    return (any(part.startswith(PREFIX) for part in directory.parts)
        or os.path.lexists(directory / SIDECAR) or data is not None and 'comparison_route' in data)


def authorize(context, source, output, seconds, keep, adapter, profile, scoring, guidance, extras):
    from .pipeline import Rejected
    require_context(context)
    if (Path(source) != context.source or Path(output) != context.output or seconds != context.seconds
            or profile != context.profile or keep is not False or adapter != 'both'
            or scoring is not None or guidance != 'native' or any(value is not None for value in extras)):
        raise Rejected('unsupported fixed comparison Route request')


def bind(directory, data, context):
    from . import pipeline as p
    require_context(context)
    target=Path(directory)/SIDECAR
    if target.exists() or target.is_symlink():raise p.Rejected('comparison context output already exists')
    p.save_json(target,context.record())
    data.update(comparison_route=dict(policy=POLICY,file=SIDECAR,sha256=p.sha(target)),production_admitted=False)


def check_record(directory, data, context):
    from . import pipeline as p
    from .floor_route import read_json
    from .local_settings import policy_declaration
    directory=Path(directory)
    if context is None:
        if marked(directory,data):raise p.Rejected('comparison evidence requires its explicit caller context')
        return False
    require_context(context)
    if directory != context.output:raise p.Rejected('comparison receipt escaped its exact output')
    expected=dict(policy=POLICY,file=SIDECAR,sha256=hashlib.sha256(pv.read_bytes(directory/SIDECAR,512*1024)).hexdigest())
    forbidden=('strategy','input_policy','routing_preferences','diagnostic_schema','production_qualified',
        'experimental_route_policy','experimental_native_toolchain','experimental_schematic_parity_policy',
        'guidance_policy','engine_fanout_override','engine_optimizer_override','engine_angle_binding',
        'engine_planning_clearance_margin_nm','engine_global_width_policy','incumbent_scoring_contract',
        'incumbent_scoring_variant','incumbent_receipt_sha256','pruning_preferences','pruning_preferences_policy')
    if (type(data.get('schema')) is not int or data['schema'] != 1 or data.get('comparison_route') != expected
            or data.get('production_admitted') is not False or any(name in data for name in forbidden)
            or data.get('source') != str(context.source) or data.get('source_hashes') != context.source_hashes
            or data.get('tools') != context.tools or data.get('engine_profile') != context.profile
            or data.get('baseline') != p.engine_baseline(context.profile,'both') or data.get('adapter') != 'both'
            or data.get('scope') != 'whole_board_unlocked_routing' or data.get('scoring_variant') is not None
            or data.get('budget_seconds') != context.seconds or data.get('cpu_budget_seconds') != context.seconds
            or data.get('schematic_parity') != 'checked by final native DRC'
            or encode(read_json(directory/SIDECAR)) != context._seal):
        raise p.Rejected('comparison receipt differs from fixed caller contract')
    for name, declaration in (('pipeline.py','COMPARISON_ROUTE_POLICY'),('comparison.py','POLICY')):
        raw=pv.read_bytes(directory/'code'/name)
        if (hashlib.sha256(raw).hexdigest() != context.tools['implementation_sha256'].get('autorouter/'+name)
                or policy_declaration(raw,name=declaration,expected=POLICY) != POLICY):
            raise p.Rejected('comparison source policy/provenance differs')
    return True
