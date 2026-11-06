"""Read-only saved-project facts and untrusted routing intent validation.

The caller retains the inspection; a model supplies only proposal arguments.
Neither an inspection nor a validated proposal grants permission to run, approve,
change a board, or bypass the ordinary native checks and separate export flow.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

from . import gui, pipeline as p, preferences as pref, routing_scope as rs, sexpr as sx
from .placement_clearance import read_bytes


class IntentError(ValueError):
    """An ambiguous, stale, unsupported or malformed request was refused."""


_PROPOSAL_KEYS = frozenset({'action', 'scope', 'nets', 'preserve_existing', 'seconds', 'search'})


def tool_schema():
    """Fresh OpenAI-compatible function descriptor; this tool only proposes."""
    return {
        'type': 'function',
        'function': {
            'name': 'propose_route',
            'description': ('Propose bounded routing settings for the caller-selected saved project. '
                'This grants no execution or approval authority. Use exact observed net names. '
                'all_remaining preserves every existing route; unlocked permits rerouting only '
                'unlocked copper. selected_nets preserves other nets. Completion search is '
                'available only for all_remaining or unlocked. Unsupported requests are refused.'),
            'strict': True,
            'parameters': {
                'type': 'object', 'additionalProperties': False,
                'required': ['action', 'scope', 'nets', 'preserve_existing', 'seconds', 'search'],
                'properties': {
                    'action': {'type': 'string', 'enum': ['route']},
                    'scope': {'type': 'string', 'enum': ['all_remaining', 'selected_nets', 'unlocked']},
                    'nets': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': rs.MAX_NAMES,
                             'description': 'Exact native names for selected_nets; otherwise an empty list.'},
                    'preserve_existing': {'type': 'boolean',
                        'description': 'True for all_remaining; false for unlocked. Selected preservation refuses any unlocked copper already on selected nets.'},
                    'seconds': {'type': 'integer', 'minimum': 5, 'maximum': 900},
                    'search': {'type': 'string', 'enum': ['standard', 'completion_search']},
                },
            },
        },
    }


def _capture(board):
    if not isinstance(board, (str, Path)) or not str(board) or '\x00' in str(board):
        raise IntentError('An exact saved PCB path is required.')
    source = gui.canonical(board)
    if source.suffix != '.kicad_pcb' or not source.is_file():
        raise IntentError('Select the exact saved .kicad_pcb file.')
    for suffix in ('.kicad_pro', '.kicad_sch'):
        sibling = gui.canonical(source.with_suffix(suffix))
        if not sibling.is_file():
            raise IntentError('A matching saved project and schematic are required.')
    before = gui.source_inventory(source)
    raw = read_bytes(source)
    digest = hashlib.sha256(raw).hexdigest()
    if before.get(source.name) != digest:
        raise IntentError('Saved source changed during inspection; inspect again.')
    tree = sx.parse(raw.decode('utf-8'))
    mapping = rs._net_mapping(tree)
    routes = list(rs._route_map(tree).values())
    footprints = sx.children(tree, 'footprint')
    pads = [pad for footprint in footprints for pad in sx.children(footprint, 'pad')]
    facts = {name: {'name': name, 'terminal_count': 0, 'existing_route_items': 0,
                    'locked_route_items': 0} for name in sorted(mapping[2])}
    for pad in pads:
        row = rs._one(pad, 'net')
        name = (mapping[1].get(row[1]) if row is not None else None) if mapping[0] == 'legacy_table' else rs._net_name(pad, mapping)
        if name is not None:
            facts[name]['terminal_count'] += 1
    unnamed_routes = 0
    for route in routes:
        name = rs._net_name(route, mapping)
        if name is None:
            unnamed_routes += 1
        else:
            facts[name]['existing_route_items'] += 1
            facts[name]['locked_route_items'] += int(rs._locked(route))
    version = sx.one(tree, 'version')
    if version is None or len(version) != 2 or type(version[1]) is not str:
        raise IntentError('An unambiguous board format version is required.')
    result = {
        'schema': 1, 'kind': 'autorouter.saved-project-inspection.v1', 'status': 'inspected',
        'source': str(source), 'source_sha256': digest, 'source_hashes': before,
        'board_format': version[1], 'footprint_count': len(footprints), 'terminal_count': len(pads),
        'nets': list(facts.values()), 'existing_route_items': len(routes),
        'locked_route_items': sum(rs._locked(route) for route in routes),
        'unnamed_route_items': unnamed_routes,
        'unconnected_items': None, 'native_validation_performed': False,
        'execution_authorized': False, 'approval_granted': False,
        'limitations': ['Saved files only; unsaved editor changes are not inspected.',
            'Terminal counts are declared physical pad occurrences, not native connectivity.',
            'Routing support is checked against the exact proposal by the shared static preview.',
            'Native refill, connectivity, original-rule checks and review remain required.'],
    }
    if gui.source_inventory(source) != before:
        raise IntentError('Saved source changed during inspection; inspect again.')
    return result, tree, mapping


def inspect_project(board):
    """Bounded static inspection; no subprocesses, native checks or writes."""
    try:
        return _capture(board)[0]
    except (OSError, ValueError, UnicodeError, TypeError, IndexError, p.Rejected) as exc:
        raise IntentError(str(exc)) from exc


def _proposal(value):
    if type(value) is not dict or set(value) != _PROPOSAL_KEYS:
        raise IntentError('Exactly the six routing proposal fields are required; extra commands or permissions are refused.')
    if type(value['action']) is not str or value['action'] != 'route':
        raise IntentError('Only the route proposal action is supported.')
    if type(value['scope']) is not str or value['scope'] not in {'all_remaining', 'selected_nets', 'unlocked'}:
        raise IntentError('An explicit supported routing scope is required.')
    if type(value['preserve_existing']) is not bool:
        raise IntentError('preserve_existing must be an explicit boolean.')
    if type(value['seconds']) is not int or not 5 <= value['seconds'] <= 900:
        raise IntentError('The routing budget must be an integer from 5 to 900 seconds.')
    if type(value['search']) is not str or value['search'] not in {'standard', 'completion_search'}:
        raise IntentError('An explicit supported search preference is required.')
    if value['scope'] == 'selected_nets':
        names = rs.validate_names(value['nets'])
        if value['search'] != 'standard':
            raise IntentError('Completion search is unsupported for selected nets; settings were not changed.')
    else:
        if type(value['nets']) is not list or value['nets']:
            raise IntentError('Exact net selection requires selected_nets scope; other scopes require nets: [].')
        names = []
    if value['scope'] == 'all_remaining' and not value['preserve_existing']:
        raise IntentError('all_remaining requires preserve_existing: true; choose unlocked explicitly to permit rerouting.')
    if value['scope'] == 'unlocked' and value['preserve_existing']:
        raise IntentError('unlocked cannot preserve all existing routing; choose all_remaining explicitly.')
    return {**value, 'nets': names}


def validate_route_proposal(inspection, proposal):
    """Validate untrusted arguments against a caller-retained static inspection.

    Do not take the inspection from the model. A valid return is reviewable
    settings only; the ordinary workflow must capture consent and recheck source
    freshness itself at execution time. Native-enriched reports should pass
    their original nested ``static`` record, never an altered inspection.
    """
    from .__main__ import preview

    try:
        requested = _proposal(proposal)
        if type(inspection) is not dict or type(inspection.get('source')) is not str:
            raise IntentError('A caller-retained saved-project inspection is required.')
        current, tree, mapping = _capture(inspection['source'])
        if inspection != current:
            raise IntentError('Inspection is stale or changed; inspect the saved project again.')
        settings = dict(pref.DEFAULTS, seconds=requested['seconds'])
        if requested['scope'] == 'all_remaining':
            settings['scope'] = 'partial_completion'
        elif requested['scope'] == 'selected_nets':
            names = requested['nets']
            if not set(names) <= mapping[2]:
                raise IntentError('Selected net is unknown; use exact names from the saved source.')
            if requested['preserve_existing'] and any(
                    rs._net_name(route, mapping) in names and not rs._locked(route)
                    for route in p.routes(tree)):
                raise IntentError('unsupported: preserving existing selected-net copper requires every existing selected item to be locked; no copper was removed or scope widened.')
            settings.update(scope='selected_nets', profile='completion-only', nets=names)
        if requested['search'] == 'completion_search':
            settings = gui.completion_search_preset(settings)
        settings = pref.validate(settings)
        # Complete preferences go through the same public preflight as the GUI/CLI.
        overrides = {key: value for key, value in settings.items() if key != 'schema'}
        checked = preview(current['source'], overrides=overrides)
        if (checked.get('source') != current['source']
                or checked.get('source_sha256') != current['source_sha256']
                or checked.get('effective_preferences') != settings
                or checked.get('native_validation_performed') is not False):
            raise IntentError('Shared preview did not preserve exact source and requested settings.')
        if gui.source_inventory(Path(current['source'])) != current['source_hashes']:
            raise IntentError('Saved source changed during proposal validation; inspect again.')
        return {
            'schema': 1, 'kind': 'autorouter.route-proposal.v1', 'status': 'proposed',
            'source': current['source'], 'source_sha256': current['source_sha256'],
            'source_hashes': current['source_hashes'], 'intent': copy.deepcopy(requested),
            'effective_preferences': copy.deepcopy(settings),
            'existing_route_items': checked['existing_route_items'],
            'protected_route_items': checked['protected_route_items'],
            'rerouted_route_items': checked['rerouted_route_items'], 'preview': checked,
            'unconnected_items': None, 'native_validation_performed': False,
            'execution_authorized': False, 'approval_granted': False,
            'next_step': 'Review these exact settings. Running still needs explicit approval through the ordinary guarded workflow; a candidate needs separate native checks and review.',
        }
    except (OSError, ValueError, UnicodeError, TypeError, IndexError, p.Rejected) as exc:
        raise IntentError(str(exc)) from exc
