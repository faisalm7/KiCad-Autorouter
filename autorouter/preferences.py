"""Explicit saved routing preferences; no global settings or new routing support.

Captured bytes, rather than a mutable parsed dictionary, are authoritative.
Readback verifies a run's captured choices without rereading the current preset.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from types import MappingProxyType

MAX_PRESET_BYTES = 16 * 1024
MAX_SNAPSHOT_BYTES = 64 * 1024
DEFAULTS = MappingProxyType({
    'schema': 1, 'scope': 'whole_board_unlocked_routing', 'seconds': 120,
    'adapter': 'none', 'profile': 'standard', 'guidance': 'native',
    'layers': 'source_all', 'scoring_preference': None,
})
REQUIRED = frozenset(DEFAULTS) - {'scoring_preference'}
CHOICES = {
    'scope': {'whole_board_unlocked_routing', 'partial_completion', 'selected_nets'},
    'adapter': {'none', 'graphics', 'planes', 'both'},
    'profile': {'standard', 'tuned', 'completion-only'},
    'guidance': {'native', 'board-floors-v1', 'placement-clearance-v1'},
}
SCORING = {'via_default', 'via_low', 'via_high'}


class PreferenceError(ValueError):
    pass


@dataclass(frozen=True)
class CapturedPreset:
    path: Path
    raw: bytes
    sha256: str
    parsed: dict  # Convenience only; never used to resolve or serialize a run.


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise PreferenceError('invalid preferences JSON value') from exc


def _parse(raw, limit):
    if type(raw) is not bytes or not 0 < len(raw) <= limit:
        raise PreferenceError('bounded nonempty preferences bytes required')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PreferenceError('duplicate preferences key: ' + key)
            result[key] = value
        return result

    def constant(value):
        raise PreferenceError('nonfinite preferences value: ' + value)

    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise PreferenceError('invalid preferences JSON: ' + str(exc)) from exc


def _path(path):
    if not isinstance(path, (str, Path)) or not str(path) or '\x00' in str(path):
        raise PreferenceError('explicit preferences file path required')
    if '..' in str(path).split('/'):
        raise PreferenceError('parent aliases in preferences path are unsupported')
    return Path(os.path.abspath(path))


def _read(path):
    # Lazy import avoids a preferences -> pipeline -> preferences import cycle.
    from .placement_clearance import read_bytes
    from .pipeline import Rejected
    try:
        return read_bytes(path, MAX_PRESET_BYTES)
    except (OSError, ValueError, RuntimeError, Rejected) as exc:
        raise PreferenceError('cannot read bounded regular preferences file: ' + str(exc)) from exc


def validate(config):
    """Validate a complete preset; selected scope additionally requires nets."""
    if type(config) is not dict or not REQUIRED <= set(config) or set(config) - (set(DEFAULTS) | {'nets'}):
        raise PreferenceError('missing or unknown preferences keys')
    if type(config['schema']) is not int or config['schema'] != 1:
        raise PreferenceError('unsupported preferences schema')
    result = dict(config)
    result.setdefault('scoring_preference', None)
    for name, choices in CHOICES.items():
        if type(result[name]) is not str or result[name] not in choices:
            raise PreferenceError('unsupported preferences ' + name)
    seconds = result['seconds']
    if type(seconds) not in (int, float) or not 5 <= seconds <= 900 or not math.isfinite(seconds):
        raise PreferenceError('preferences budget must be finite 5–900 seconds')
    scoring = result['scoring_preference']
    if scoring is not None and (type(scoring) is not str or scoring not in SCORING):
        raise PreferenceError('unsupported scoring preference')
    if result['scope'] == 'selected_nets':
        from .routing_scope import validate_names
        try: result['nets'] = validate_names(result.get('nets'))
        except ValueError as exc: raise PreferenceError(str(exc)) from exc
        if (result['guidance'] != 'native' or result['profile'] != 'completion-only'
                or result['layers'] != 'source_all'):
            raise PreferenceError('selected nets require native completion-only routing and source_all layers')
    elif 'nets' in result:
        raise PreferenceError('nets require selected_nets scope; remove nets when changing scope')
    if result['guidance'] != 'native':
        if (result['scope'] != 'whole_board_unlocked_routing' or result['adapter'] != 'both'
                or scoring is not None):
            raise PreferenceError('guidance requires whole-board scope, adapter both and no scoring override')
        if result['guidance'] == 'placement-clearance-v1' and result['profile'] != 'completion-only':
            raise PreferenceError('placement guidance requires completion-only profile')
    if result['layers'] != 'source_all':
        from .layer_policy import validate_request
        try:
            result['layers'] = validate_request(result['layers'], scope=result['scope'],
                engine_profile=result['profile'], guidance_policy=result['guidance'])
        except ValueError as exc:
            raise PreferenceError(str(exc)) from exc
    return result


def load(path):
    """Capture one explicit, bounded regular file, rejecting symlink ancestors."""
    path = _path(path)
    raw = _read(path)
    parsed = validate(_parse(raw, MAX_PRESET_BYTES))
    return CapturedPreset(path, raw, hashlib.sha256(raw).hexdigest(), parsed)


def _captured(captured):
    if captured is None:
        return dict(DEFAULTS)
    if type(captured) is not CapturedPreset or not isinstance(captured.path, Path):
        raise PreferenceError('invalid captured preferences')
    if _path(captured.path) != captured.path:
        raise PreferenceError('captured preferences path must be absolute')
    parsed = validate(_parse(captured.raw, MAX_PRESET_BYTES))
    if type(captured.sha256) is not str or hashlib.sha256(captured.raw).hexdigest() != captured.sha256:
        raise PreferenceError('captured preferences digest differs')
    return parsed


def _overrides(overrides):
    if overrides is None:
        return {}
    if type(overrides) is not dict or set(overrides) - ((set(DEFAULTS) - {'schema'}) | {'nets'}):
        raise PreferenceError('unknown or aliased preferences override')
    return dict(overrides)


def resolve(captured=None, overrides=None):
    """Explicit overrides win; absent override keys retain captured/default values."""
    return validate({**_captured(captured), **_overrides(overrides)})


def route_arguments(effective):
    effective = validate(effective)
    return {'seconds': effective['seconds'],
            'keep_existing': effective['scope'] == 'partial_completion',
            'adapter': effective['adapter'], 'engine_profile': effective['profile'],
            'guidance_policy': effective['guidance'],
            'scoring_variant': effective['scoring_preference']}


def snapshot(captured=None, overrides=None):
    """Return bounded receipt bytes; caller exclusively writes and hashes them."""
    explicit = _overrides(overrides)
    effective = resolve(captured, explicit)
    preset = None if captured is None else {
        'path': str(captured.path), 'raw_utf8': captured.raw.decode('utf-8'),
        'sha256': hashlib.sha256(captured.raw).hexdigest(),
    }
    raw = _canonical({'schema': 1, 'preset': preset, 'overrides': explicit, 'effective': effective}) + b'\n'
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise PreferenceError('preferences snapshot exceeds bound')
    return raw


def readback(snapshot_bytes, expected_effective=None):
    """Recompute captured choices; current external preset edits are irrelevant."""
    record = _parse(snapshot_bytes, MAX_SNAPSHOT_BYTES)
    if (type(record) is not dict or set(record) != {'schema', 'preset', 'overrides', 'effective'}
            or type(record['schema']) is not int or record['schema'] != 1):
        raise PreferenceError('invalid preferences snapshot schema')
    captured = None
    preset = record['preset']
    if preset is not None:
        if (type(preset) is not dict or set(preset) != {'path', 'raw_utf8', 'sha256'}
                or type(preset['path']) is not str or type(preset['raw_utf8']) is not str):
            raise PreferenceError('invalid captured preset snapshot')
        path = _path(preset['path'])
        if str(path) != preset['path']:
            raise PreferenceError('noncanonical captured preferences path')
        try:
            raw = preset['raw_utf8'].encode('utf-8')
        except UnicodeError as exc:
            raise PreferenceError('invalid captured preferences encoding') from exc
        captured = CapturedPreset(path, raw, preset['sha256'], {})
    if type(record['overrides']) is not dict:
        raise PreferenceError('snapshot overrides must be an explicit object')
    effective = resolve(captured, record['overrides'])
    if _canonical(record['effective']) != _canonical(effective):
        raise PreferenceError('snapshot effective preferences differ from captured input and overrides')
    if expected_effective is not None:
        validate(expected_effective)
        if _canonical(expected_effective) != _canonical(effective):
            raise PreferenceError('run effective preferences differ from captured snapshot')
    return effective


def check_fresh(captured):
    """During a run only: detect changed source bytes without rebasing the capture."""
    _captured(captured)
    if captured is not None and _read(captured.path) != captured.raw:
        raise PreferenceError('preferences changed during execution')
