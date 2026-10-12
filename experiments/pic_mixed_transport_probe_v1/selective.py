"""One selective-state transition; process/source capture stays in the existing caller."""
import copy
import json
from experiments.pic_mixed_transport_probe_v1 import transport, ses_checks


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def equal(left, right, message):
    if canonical(left) != canonical(right):
        raise ValueError(message)


def by_id(rows, label):
    if not isinstance(rows, list) or len(rows) > 4096:
        raise ValueError(label + ' population bound')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or type(row.get('id')) is not int or row['id'] in result:
            raise ValueError(label + ' duplicate/illtyped ID')
        result[row['id']] = row
    return result


def id_list(value, allowed, label):
    if (not isinstance(value, list) or len(value) > 4096 or any(type(x) is not int for x in value)
            or value != sorted(set(value)) or not set(value) <= set(allowed)):
        raise ValueError(label + ' identity list differs')
    return set(value)


def route_geometry(geometry, state):
    ses_checks.geometry_check(geometry, state)
    return by_id(geometry['traces'], 'traces'), by_id(geometry['vias'], 'vias')


def predicates(data, state, geometry):
    items = by_id(state['items'], 'items')
    areas = by_id(state['areas'], 'areas')
    traces, vias = route_geometry(geometry, state)
    routes = traces | vias
    for key, count in (('area_count', len(areas)), ('route_count', len(routes)), ('item_count', len(items))):
        if type(data.get(key)) is not int or data[key] != count:
            raise ValueError('predicate census differs')
    entries = by_id(data['tree_entries'], 'tree entries')
    if set(entries) != set(items) or data.get('search_tree_population_verified') is not True:
        raise ValueError('complete search-tree population proof missing')
    indexed = unindexed = 0
    for identity, row in entries.items():
        if (set(row) != {'id', 'kind', 'on_board', 'shape_count', 'tile_shape_count', 'entry_count', 'valid'}
                or row['kind'] != items[identity]['kind'] or row['on_board'] is not True
                or type(row['shape_count']) is not int or not 0 <= row['shape_count'] <= 16384
                or type(row['tile_shape_count']) is not int or not 0 <= row['tile_shape_count'] <= 16384
                or type(row['valid']) is not bool):
            raise ValueError('search-tree item witness differs')
        if row['kind'] == 'app.freerouting.board.model.items.ComponentOutline':
            if row['shape_count'] != 0 or row['tile_shape_count'] != 0 or row['entry_count'] is not None or row['valid'] is not False:
                raise ValueError('unindexed outline must have exact zero/null witness')
            unindexed += 1
        else:
            if row['shape_count'] <= 0 or type(row['entry_count']) is not int or row['entry_count'] != row['shape_count'] or row['valid'] is not True:
                raise ValueError('indexed item entries must validate')
            indexed += 1
    if (type(data.get('all_tree_entries_valid')) is not bool
            or data['all_tree_entries_valid'] != all(r['valid'] for r in entries.values())
            or type(data.get('indexed_items')) is not int or data['indexed_items'] != indexed
            or type(data.get('unindexed_zero_shape_outlines')) is not int or data['unindexed_zero_shape_outlines'] != unindexed):
        raise ValueError('search-tree population counts/raw validation differ')
    observed = by_id(data['areas'], 'predicate areas')
    if set(observed) != set(areas):
        raise ValueError('predicate area membership differs')
    for identity, area in areas.items():
        recorded = observed[identity]
        if (set(recorded) != {'id', 'filled', 'obstacle', 'routes'} or type(recorded['filled']) is not bool
                or type(recorded['obstacle']) is not bool or recorded['obstacle'] is not area['obstacle']):
            raise ValueError('area predicate flags differ')
        table = by_id(recorded['routes'], 'area route predicates')
        if set(table) != set(routes):
            raise ValueError('complete area/ordinary-route predicate population missing')
        for rid, route in routes.items():
            if len(route['nets']) != 1:
                raise ValueError('ordinary route single-net scope')
            same = bool(set(area['nets']) & set(route['nets']))
            obstruction = area['obstacle'] and not same
            shares_layer = area['first_layer'] <= route['last_layer'] and route['first_layer'] <= area['last_layer']
            equal(table[rid], {'id': rid, 'kind': 'trace' if rid in traces else 'via', 'net': route['nets'][0],
                              'same_net': same, 'shares_layer': shares_layer, 'item_obstacle': obstruction,
                              'trace_obstacle': obstruction, 'drillable': not obstruction},
                  'area predicate disagrees with exact source contract')
    queries = by_id(data['trace_queries'], 'trace queries')
    if set(queries) != set(traces):
        raise ValueError('complete trace query population missing')
    total = 0
    for identity, query in queries.items():
        if (set(query) != {'id', 'shape_count', 'tree_trace_check_clear', 'raw_overlap_ids', 'flag_filtered_overlap_ids'}
                or type(query['shape_count']) is not int or not 1 <= query['shape_count'] <= 4096
                or type(query['tree_trace_check_clear']) is not bool):
            raise ValueError('trace query schema/bounds differ')
        total += query['shape_count']
        raw = id_list(query['raw_overlap_ids'], items, 'raw overlaps')
        blocking = id_list(query['flag_filtered_overlap_ids'], raw, 'filtered overlaps')
        # Raw spatial hits do not by themselves imply that a ConductionArea blocks traces.
        for aid in set(areas) & raw:
            required = areas[aid]['obstacle'] and not bool(set(areas[aid]['nets']) & set(traces[identity]['nets']))
            if (aid in blocking) != required:
                raise ValueError('area hit filtering differs from selective trace predicate')
    if type(data.get('trace_shape_count')) is not int or total != data['trace_shape_count'] or total > 16384:
        raise ValueError('trace shape aggregate differs')
    return observed, queries


def compare(observed, expected, verified_local_observation):
    """Recheck the actual two-case local basis; never fabricate a second import row.

    Caller captures/binds all three inputs plus original files/process/runtime using
    the existing controller. This function verifies representation, not routing.
    """
    baseline_result = transport.validate_local(verified_local_observation, expected)
    if len(baseline_result) != 2 or not all(row.get('observed') is True for row in baseline_result):
        raise ValueError('actual local baseline did not validate')
    if (type(observed.get('schema')) is not int or observed['schema'] != 1
            or observed.get('mode') != 'selective_local250' or observed.get('routing_executed') is not False
            or observed.get('ses_executed') is not False):
        raise ValueError('selective observation mode/schema differs')
    row = observed['case']
    if row.get('status') != 'observed' or row.get('post_load_awaited') is not True or row.get('requested_obstacle') is not False:
        raise ValueError('single false import was not fully observed')
    baseline = verified_local_observation['cases'][0]
    for field in ('input_sha256', 'argv', 'settings_before', 'settings_after', 'parser_result_class',
                  'state_before_local', 'local_override', 'state'):
        equal(row[field], baseline[field], 'fresh false import/local basis differs: ' + field)
    if row['input_sha256'] != expected['derived_dsn_sha256']:
        raise ValueError('input digest differs')
    result=transition(row)
    result['baseline_false_state_exact']=True
    return result

def transition(row):
    """Check the same exact transition on one independently validated import."""
    equal(row['settings_after_selective'], row['settings_after'], 'manager settings changed')
    for phase in ('settings_before', 'settings_after', 'settings_after_selective'):
        setting = row[phase]
        if (setting.get('plane_as_obstacle') is not False or setting.get('plane_nets') != []
                or setting.get('router_enabled') is not False or setting.get('optimizer_enabled') is not False):
            raise ValueError('explicit disabled/empty-plane lifecycle required')
    old, new = row['state'], row['state_after_selective']
    equal(row['route_geometry_before_local'], row['route_geometry'], 'local mutation changed ordinary routes')
    equal(row['route_geometry'], row['route_geometry_after_selective'], 'selective mutation changed ordinary routes')
    route_geometry(row['route_geometry_before_local'], row['state_before_local'])
    route_geometry(row['route_geometry'], old)
    route_geometry(row['route_geometry_after_selective'], new)
    targets = {body['area_id'] for body in row['local_override']['targets']}
    areas = by_id(old['areas'], 'old areas')
    originals = set(areas) - targets
    if (len(targets) != 2 or len(areas) != 3 or len(originals) != 1 or old['ignore_conduction'] is not True
            or any(a['obstacle'] is not False for a in areas.values())):
        raise ValueError('false original area scope differs')
    original = areas[next(iter(originals))]
    if original['nets'] != ['GND'] or original['fixed'] != 'SYSTEM_FIXED':
        raise ValueError('original plane identity differs')
    restored = copy.deepcopy(new)
    if restored['ignore_conduction'] is not False:
        raise ValueError('global selective flag not explicitly changed')
    restored['ignore_conduction'] = True
    for area in restored['areas']:
        if area['id'] in targets:
            if area['obstacle'] is not True:
                raise ValueError('both custom bodies must be enabled')
            area['obstacle'] = False
            for witness in area['foreign_pin_predicates']:
                if witness['trace_obstacle'] is not True or witness['is_obstacle'] is not False:
                    raise ValueError('custom foreign-pin predicate differs')
                witness['trace_obstacle'] = False
    equal(restored, old, 'selective change affected unrelated original state')
    audit = row['selective_override']
    if (audit.get('changed_area_ids') != sorted(targets) or audit.get('global_ignore_before') is not True
            or audit.get('global_ignore_after') is not False or audit.get('tree_refresh_completed') is not True):
        raise ValueError('selective mutation/refresh audit differs')
    equal(row['predicates_before']['tree_entries'], row['predicates_after']['tree_entries'],
          'tree entry population/witness changed after selective refresh')
    before_areas, before_queries = predicates(row['predicates_before'], old, row['route_geometry'])
    after_areas, after_queries = predicates(row['predicates_after'], new, row['route_geometry_after_selective'])
    for aid in areas:
        if before_areas[aid]['filled'] is not after_areas[aid]['filled']:
            raise ValueError('original/synthetic area fill state changed')
    for identity, before in before_queries.items():
        after = after_queries[identity]
        if before['shape_count'] != after['shape_count'] or before['raw_overlap_ids'] != after['raw_overlap_ids']:
            raise ValueError('unchanged geometry/matrix produced different raw tree hits')
        if set(before['flag_filtered_overlap_ids']) - targets != set(after['flag_filtered_overlap_ids']) - targets:
            raise ValueError('non-target filtered obstacle set changed')
        if before['tree_trace_check_clear'] is False and after['tree_trace_check_clear'] is True:
            raise ValueError('enabling bodies unexpectedly cleared trace check')
    return {'selective_transition_verified': True, 'changed_area_ids': sorted(targets), 'preserved_area_ids': sorted(originals),
            'ordinary_imported_routes_unchanged': True,
            'routing_accepted': False, 'native_route_survival_qualified': False, 'solver_lifecycle_qualified': False,
            'interpretation': 'Single retained-board representation observation against a revalidated actual local basis; no solver/SES/native equivalence.'}
