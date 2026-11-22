"""Source-derived routing scope for ordinary preserve-all-copper jobs."""
import hashlib

from . import native_connected, pipeline as p, routing_scope, schematic_field_evidence as fields, sexpr
from .floor_route import canonical, check_drc_stage
from .placement_clearance import read_bytes

POLICY = 'native-missing-connections-v1'
PARTITION_INPUT = 'finish-gaps-input.dsn'


def enabled(scope, guidance='native'):
    return p.c.NATIVE_VERSION == '10.0.7' and scope == 'partial_completion' and guidance == 'native'


def source_delivery(native, *, field_mismatches_only=False):
    """Use delivery policy for source findings that the requested task cannot fix."""
    reasons = p.native_rejection_reasons(native)
    if (type(native) is not dict or any(reason.startswith(('malformed', 'missing')) for reason in reasons)):
        return {'reasons': reasons, 'blocking_findings': [], 'related_findings': [], 'field_qualification': None}
    findings = native['findings']
    opens = [row for row in findings if row.get('type') == 'unconnected_items']
    if len(opens) == native.get('opens') and all(row.get('severity') == 'error' and not row.get('excluded') for row in opens):
        allowed = {'native opens=' + str(len(opens)), 'native error finding: unconnected_items',
                   'policy-critical native finding: unconnected_items (error)'}
        reasons = [reason for reason in reasons if reason not in allowed]
    blocked = []
    for row in findings:
        check, severity = row['type'], row['severity']
        if ('policy-critical native finding: ' + check + ' (' + severity + ')' in reasons
                or 'native error finding: ' + check in reasons or 'excluded native finding: ' + check in reasons
                or 'unknown native finding semantics: ' + check in reasons):
            blocked.append(row)
    if field_mismatches_only:
        # A reroute may repair ordinary opens or copper errors. Footprint
        # fields and the saved schematic are immutable in a routing job.
        blocked = [row for row in blocked if row['type'] == fields.TYPE]
        reasons = [reason for reason in reasons if fields.TYPE in reason]
    parity = native.get('field_parity', {}).get('qualification')
    related = [row for row in findings if row['type'] == 'footprint_symbol_mismatch'] if any(
        row['type'] == fields.TYPE for row in blocked) else []
    return {'reasons': reasons, 'blocking_findings': blocked, 'related_findings': related,
            'field_qualification': parity}


def source_delivery_lines(delivery):
    """Explain why an inspected source cannot yield a checked copy."""
    if not delivery['reasons']:
        return []
    lines = []
    for finding in (*delivery['blocking_findings'], *delivery['related_findings'])[:6]:
        refs = ', '.join(str(item.get('description', ''))[:150] for item in finding['items'][:2])
        lines.append(f"KiCad {finding['severity']} · {refs} · " + str(finding.get('description', finding['type']))[:550])
    if any(row['type'] == fields.TYPE for row in delivery['blocking_findings']):
        lines.append('Copperpath blocks delivery when it cannot verify a PCB and schematic field difference as harmless.')
        lines.append('Reconcile the shown fields and footprint assignments in KiCad. Save the PCB and schematic, then preview again.')
    elif lines:
        lines.append('Copperpath requires these source issues to be resolved before adding copper. Review the findings in KiCad and preview again.')
    elif 'disabled policy-critical native check: ' + fields.TYPE in delivery['reasons']:
        lines.append('Enable the schematic and PCB field comparison in KiCad Board Setup. Save the project and preview again.')
    else:
        lines.extend(delivery['reasons'][:6])
        lines.append('Copperpath requires verified source checks. Review the saved project in KiCad.')
    return lines


def plan(original, source_hashes, native):
    """Use a previously verified source check, across the entire board."""
    delivery = source_delivery(native)
    names = []
    if delivery['reasons']:
        status = 'blocked'
    elif native['opens'] == 0:
        status = 'already_connected'
    else:
        try:
            _, endpoints, _ = native_connected._index(original)
            names = routing_scope.validate_names(native_connected.open_names(native, endpoints))
            status = 'ready'
        except (ValueError, p.Rejected) as exc:
            status = 'unsupported'
            delivery['reasons'] = [str(exc)]
    result = {'policy': POLICY, 'status': status, 'nets': names, 'opens': native['opens'],
              'protected_routes': len(p.routes(original)), 'source_delivery': delivery}
    result['binding_sha256'] = hashlib.sha256(canonical({'source': source_hashes, 'plan': result}).encode()).hexdigest()
    return result


def require_ready(report, expected=None):
    if report['status'] == 'already_connected':
        raise p.Rejected('KiCad found no missing connections. There is nothing to route.')
    if report['status'] != 'ready':
        raise p.Rejected('\n'.join(source_delivery_lines(report['source_delivery'])))
    if expected is not None and report['binding_sha256'] != expected:
        raise p.Rejected('Finish gaps preview no longer matches the saved source and missing connections. Preview again.')


def partition(directory, task, names, *, default_targets=False):
    """Check native pins and partition the unchanged corrected board for the engine."""
    known, _, terminals = native_connected._index(task)
    # The existing Default-target proof verifies the lawful corrections to the
    # native network. Keep that exact network and terminal census in the partition.
    exported = read_bytes(directory / ('default-targets.dsn' if default_targets else 'native.dsn'), 20 * 1024**2)
    network = native_connected._dsn_members(exported, known, terminals)
    from .adapter import _parse_dsn
    raw = read_bytes(directory / PARTITION_INPUT, 20 * 1024**2)
    if sexpr.one(_parse_dsn(raw.decode()), 'network') != network:
        raise p.Rejected('Finish gaps corrections changed original net or class rules')
    return routing_scope.partition_dsn(raw, names)


def required(directory, data, *, ordinary):
    """Use the captured producer to keep scoped results from downgrading."""
    from .local_settings import policy_declaration

    marked = 'finish_gaps' in data or (directory / PARTITION_INPUT).exists() or (directory / PARTITION_INPUT).is_symlink()
    eligible = (ordinary and enabled(data.get('scope'), data.get('input_policy', 'native'))
                and data.get('adapter') == 'both')
    declared = False
    if eligible:
        producer = directory / 'code' / 'pipeline.py'
        if producer.exists() or producer.is_symlink():
            raw = read_bytes(producer, 1024**2)
            captured = data.get('tools', {}).get('implementation_sha256', {})
            if hashlib.sha256(raw).hexdigest() != captured.get('autorouter/pipeline.py'):
                raise p.Rejected('Finish gaps producer code differs')
            declared = policy_declaration(raw, name='FINISH_GAPS_POLICY', expected=POLICY) is not None
    if marked != declared:
        raise p.Rejected('Finish gaps result lacks its mandatory producer or scope proof')
    selected_input = directory / 'routing-scope-input.dsn'
    if declared and (selected_input.exists() or selected_input.is_symlink()):
        raise p.Rejected('Finish gaps cannot use replace-selected-copper evidence')
    return declared


def check(directory, data, original, candidate):
    source = directory / 'snapshot' / candidate.name
    native = check_drc_stage(directory, data, 'source-drc', source,
                            directory / 'source-drc-input' / candidate.name, False, data['source_hashes'],
                            schematic_parity=True, sandboxed=False)
    if native != data.get('source_drc'):
        raise p.Rejected('Finish gaps source finding summary differs from verified KiCad report')
    expected = plan(original, data['source_hashes'], native)
    require_ready(expected)
    task = p.routing_task(original, 'partial_completion')
    emitted, binding = partition(directory, task, expected['nets'], default_targets='default_target_transport' in data)
    audit = routing_scope.audit(original, sexpr.read(candidate), expected['nets'], preserve_all=True)
    if (data.get('finish_gaps') != {'plan': expected, 'partition': binding, 'audit': audit}
            or emitted != read_bytes(directory / 'task.dsn', 20 * 1024**2)):
        raise p.Rejected('Finish gaps plan, engine input or protected-copper audit differs')
    return binding
