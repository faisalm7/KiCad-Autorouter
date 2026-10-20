#!/usr/bin/env python3
"""Report explicitly pinned, completed comparison evidence without running readers.

No routing, Native, GUI, runtime query, source script, download or publication is
performed. Stored hashes/processes/full-SCH reports are checked, not revalidated.
Default output is LOCAL and contains bounded failure text: audit before sharing.
--public-sanitize replaces free-form reasons/ignored-check text by exact local
field references and hashes; it never changes classification or hides counts.
Only generated facts are retained. CAD/DSN/SES/plots/logs/raw findings stay local.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import provenance as pv, floor_route as f, placement_clearance as io
from scripts import freeze_current_comparison as frozen

KEYS = ('opens', 'blocking', 'warnings', 'exclusions')
KINDS = {'frozen-current-six-arm-exposed-development-v1': 'GUI-qualified prerequisite recorded by freezer; no new GUI claim',
         frozen.IMPROVE_POPULATION_KIND: 'Installed050 CLI prerequisite; GUI087 prepared only, no current GUI qualification',
         'frozen-runtime043-labelled-IR-native-support-followup-v1': 'labelled Native-only support follow-up; GUI qualification NOT supplied',
         'frozen-runtime049-labelled-Devobordo-native-CLI-development-followup-v1': 'labelled Devobordo Native/CLI-only development follow-up; GUI qualification NOT supplied',
         'frozen-runtime050-labelled-Devobordo-native-CLI-development-followup-v1': 'labelled Devobordo Native/CLI-only development follow-up; GUI qualification NOT supplied'}
MAX_JSON = 4 * 1024**2
MAX_REPORT_BYTES = 16 * 1024**2


def require(ok, message):
    if not ok: raise ValueError(message)


def digest(path, limit=100 * 1024**2):
    return pv.file_digest(pv.canonical(Path(path)), limit)[0]


def read(path):
    raw = pv.read_bytes(pv.canonical(Path(path)), MAX_JSON)
    def nonfinite(_): raise ValueError('nonfinite JSON refused')
    value = json.loads(raw, object_pairs_hook=pv._strict_object, parse_constant=nonfinite)
    require(type(value) is dict, 'stored JSON object required')
    return value


def pinned(path, pin):
    require(type(pin) is str and pv._DIGEST.fullmatch(pin), 'exact lowercase SHA256 required')
    require(digest(path, MAX_JSON) == pin, 'stored input hash differs: ' + str(path))
    return read(path)


def complete_cost(path):
    """The existing complete-exit -p / macOS -l parsers, never nested addition."""
    raw = pv.read_bytes(pv.canonical(Path(path)), 64 * 1024).decode('utf8')
    rows = [line.split() for line in raw.splitlines() if line.split() and line.split()[0] in ('real', 'user', 'sys')]
    if len(rows) == 3 and all(len(row) == 2 for row in rows) and {row[0] for row in rows} == {'real', 'user', 'sys'}:
        values = {name: float(value) for name, value in rows}
        wall, user, system = (values[name] for name in ('real', 'user', 'sys'))
    else:
        pattern = r'\s*([0-9]+(?:\.[0-9]+)?)\s+real\s+([0-9]+(?:\.[0-9]+)?)\s+user\s+([0-9]+(?:\.[0-9]+)?)\s+sys\s*'
        matches = [match for line in raw.splitlines() if (match := re.fullmatch(pattern, line))]
        require(len(matches) == 1, 'one complete external time header required')
        wall, user, system = map(float, matches[0].groups())
    require(all(math.isfinite(v) and v >= 0 for v in (wall, user, system)), 'invalid complete exit cost')
    return dict(wall_seconds=wall, CPU_seconds=round(user + system, 2), user_seconds=user,
                system_seconds=system, time_log_sha256=digest(path), source=str(path),
                scope='Complete external exit; nested method/Native samples are included, not added again.')


def inventory(path):
    # Preserve the exact public enclosure's sealed-evidence semantics.
    path = pv.canonical(Path(path))
    if not path.exists(): return None
    require(path.is_dir(), 'real evidence directory required')
    return f.evidence_inventory(path)


def custody(out, plan, outer, arm):
    roots = []
    if arm == 'B2_portfolio':
        portfolio = out.with_name(out.name + '-portfolio')
        require(plan['portfolio_output'] == str(portfolio), 'portfolio root differs')
        roots = [portfolio, *[portfolio.with_name(portfolio.name + '-' + f'{index:02d}-' + variant)
            for index, variant in enumerate(frozen.VARIANTS, 1)]]
    require(plan.get('material_roots', []) == outer['material_roots'] == [str(path) for path in roots], 'sibling root population differs')
    child = out / 'result.json'
    require(outer['child_receipt'] == str(child) and outer['child_sha256'] == (digest(child) if child.is_file() else None), 'terminal child hash differs')
    require(inventory(out) == outer['completed_evidence'], 'method material changed')
    require({str(path): inventory(path) for path in roots} == outer['completed_material_roots'], 'portfolio material changed or absent-state changed')
    return roots


def counts(native):
    if native is None: return None
    require(type(native) is dict and all(type(native.get(key)) is int and native[key] >= 0 for key in KEYS), 'typed Native counts required')
    return [native[key] for key in KEYS]


def field_fact(value, path, field, public_sanitize):
    """Keep inconvenient reasons addressable even when public text is withheld."""
    raw = f.canonical(value).encode()
    result = dict(receipt=str(path), field=field, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    if not public_sanitize and len(raw) <= 8192: result['value'] = value
    else: result['text_not_retained'] = 'explicit public sanitize' if public_sanitize else 'over 8192-byte inline ceiling; exact local field retained'
    return result


def reasons(data, path, public_sanitize):
    return {key: field_fact(data[key], path, key, public_sanitize) for key in
            ('reason', 'error', 'negative_reader_refusal', 'portfolio_reason') if data.get(key) is not None}


def finding_types(native):
    rows = native['findings']; require(type(rows) is list, 'finding list required')
    counter = Counter()
    for row in rows:
        require(type(row) is dict and row.get('severity') in ('error', 'warning', 'exclusion')
                and type(row.get('type')) is str and re.fullmatch(r'[A-Za-z0-9_:-]{1,128}', row['type']), 'bounded finding type required')
        counter[row['severity'] + ':' + row['type']] += 1
    return dict(sorted(counter.items()))


def metric_facts(value):
    if value is None: return None
    require(type(value) is dict, 'metric object required')
    result = {key: value[key] for key in ('vias', 'track_length_mm', 'length_mm', 'segments', 'arcs',
        'tracks', 'unrouted', 'pads', 'nets', 'footprints', 'zones', 'copper_layers') if key in value}
    require(all(type(number) in (int, float) and math.isfinite(number) and number >= 0 for number in result.values()), 'typed finite metrics required')
    # Native metrics use track_length_mm, not the portfolio's length_mm key.
    # Preserve the producer version separately from numeric measurements.
    if 'version' in value:
        require(type(value['version']) is str and re.fullmatch(r'[A-Za-z0-9._()+ -]{1,128}', value['version']), 'bounded metric version required')
        result['version'] = value['version']
    return result


def ignored_check_facts(value, path, field, public_sanitize):
    require(type(value) is list, 'ignored check list required')
    keys = []
    for row in value:
        key = row.get('key') if type(row) is dict else row
        require(type(key) is str and re.fullmatch(r'[A-Za-z0-9_:-]{1,128}', key), 'typed safe ignored-check key required')
        keys.append(key)
    fact = field_fact(value, path, field, public_sanitize)
    fact.update(keys=keys, count=len(value))
    return fact


def native_application_policy(native, plan):
    """Reuse the pure product predicate only under its recorded source pins.

    This does not run Native or a central reader. If the currently loaded pure
    policy differs from the recorded implementation, refuse to reinterpret it.
    """
    from autorouter import pipeline as application, schematic_field_evidence, schematic_fields, sexpr
    modules = (application,schematic_field_evidence,schematic_fields,sexpr)
    pins = plan['tools'].get('implementation_sha256')
    require(type(pins) is dict, 'recorded Native application-policy implementation required')
    files = {}
    for module in modules:
        name = 'autorouter/'+Path(module.__file__).name
        path = pv.canonical(Path(module.__file__))
        require(path == ROOT/name and pins.get(name) == digest(path), 'Native application-policy source differs')
        files[name] = pins[name]
    accepted = application.native_accepted(native)
    rejected = application.native_rejection_reasons(native)
    require(type(accepted) is bool and accepted is (not rejected), 'Native application-policy predicates disagree')
    for name,pin in files.items(): require(digest(ROOT/name) == pin, 'Native application-policy source changed')
    return dict(accepted=accepted,rejection_reasons=rejected,implementation_sha256=files)


def own_final(receipt, *, export, plan, allowed, accepted, public_sanitize=False, trial_parent=None):
    """The proven final-output/cwd selector, independent of phaseNone/trial order.

    This checks retained bytes/process metadata, not source semantics or a live
    central reader. A complete negative uses the same own-final binding.
    """
    receipt = pv.canonical(Path(receipt))
    require(any(root in receipt.parents for root in allowed), 'receipt escaped frozen evidence roots')
    data = read(receipt); source_hashes = plan['source_hashes']
    trial = trial_parent is not None
    header = trial_parent if trial else data
    require(not trial or not export and receipt.parent.parent == Path(trial_parent['candidate']).parent.parent/'trials',
            'trial escaped its exact Improve parent')
    require(header['source_hashes'] == source_hashes and header['tools'] == plan['tools'], 'stored source/tools differ from frozen protocol')
    identity = header['tools']['source_provenance']
    require(identity['git_head'] == plan['source_head'] and identity['manifest_sha256'] == plan['runtime_manifest_sha256']
            and header['tools']['kicad'] == '10.0.7', 'stored selected7 identity differs')
    if not trial: require(data['schematic_parity'] == 'checked by final native DRC', 'own final full-SCH completion required')
    require(data['export_accepted' if export else 'accepted'] is accepted, 'stored acceptance differs')
    require(header['original_geometry_and_routing_unchanged' if export else 'invariants_unchanged'] is True, 'original invariants not established')
    native = counts(data['native'])
    policy = native_application_policy(data['native'],plan)
    if accepted: require(policy['accepted'], 'delivered Native evidence rejected by application policy')
    elif not trial or data['status'] == 'drc_rejected':
        require(not policy['accepted'], 'completed-negative proof has no application-policy rejection')
    else: require(policy['accepted'], 'Native-valid unselected trial rejected by application policy')
    candidate = (receipt.parent/'candidate'/Path(plan['source']).name) if trial else pv.canonical(Path(data['candidate']))
    folder = receipt.parent / 'validation' if export else receipt.parent
    require(candidate == folder / 'candidate' / candidate.name and any(root in candidate.parents for root in allowed), 'candidate escaped own final directory')
    require(digest(candidate) == data['candidate_sha256'], 'candidate hash differs')
    expected = dict(source_hashes); expected[candidate.name] = data['candidate_sha256']
    binding = read(folder / 'final-drc-binding.json')
    require(binding['source'] == str(candidate) and binding['saved'] is False
            and binding['input'] == str(folder / 'final-drc-input' / candidate.name)
            and binding['before'] == expected, 'original/full-SCH input binding differs')
    after = binding['after']; prl = candidate.with_suffix('.kicad_prl').name
    require(type(after) is dict and all(after.get(name) == pin for name, pin in expected.items())
            and not (set(after) - set(expected) - {prl}) and io.inventory(folder / 'final-drc-input') == after, 'final input or allowed PRL changed')
    report = folder / 'final-drc.json'
    require(digest(report) == data['native_report_sha256'], 'own final report hash differs')
    raw = read(report)
    require(raw['kicad_version'] == '10.0.7' and raw['source'] == candidate.name
            and raw['$schema'] == 'https://schemas.kicad.org/drc.v1.json'
            and set(raw['included_severities']) == {'error', 'warning', 'exclusion'}, 'full original Native report scope differs')
    findings = raw['violations'] + raw['unconnected_items'] + raw['schematic_parity']
    raw_counts = dict(opens=len(raw['unconnected_items']),
        blocking=sum(item['severity'] == 'error' for item in raw['violations'] + raw['schematic_parity']),
        warnings=sum(item['severity'] == 'warning' for item in findings),
        exclusions=sum(item['severity'] == 'exclusion' or item.get('excluded', False) for item in findings))
    require(all(data['native'][key] == value for key, value in raw_counts.items())
            and data['native']['findings'] == findings and data['native']['ignored_checks'] == raw['ignored_checks'], 'raw Native findings/counts differ')
    steps = data['steps']
    require(type(steps) is list and all(step.get('cleanup_complete') is True and step.get('log_truncated') is False for step in steps), 'incomplete or truncated process evidence')
    selected = [step for step in steps if step.get('name') == 'final-drc' and type(step.get('argv')) is list
        and step['argv'].count('--output') == 1 and step['argv'].index('--output') + 1 < len(step['argv'])
        and step['argv'][step['argv'].index('--output') + 1] == str(report)]
    require(len(selected) == 1, 'own final must be distinguished from trial/incumbent')
    step = selected[0]; argv = step['argv']
    require(step['cwd'] == str(folder) and argv[-1] == binding['input']
            and all(flag in argv for flag in ('--schematic-parity', '--all-track-errors', '--refill-zones', '--exit-code-violations')),
            'own final command/input/cwd differs')
    cli = [name for name in plan['tools']['files'] if Path(name).name == 'kicad-cli']
    require(len(cli) == 1 and cli[0] in argv and argv[argv.index(cli[0]) + 1:argv.index(cli[0]) + 3] == ['pcb', 'drc'], 'selected pinned Native CLI absent')
    exit_code = 5 if findings else 0
    require(step['exit_code'] == exit_code and step['status'] == ('nonzero_exit' if exit_code else 'success'), 'Native warning/nonzero exit differs')
    process_path = folder / 'final-drc-process.json'; process = read(process_path)
    require(all(key in step and process.get(key) == step[key] for key in
                ('argv', 'cwd', 'status', 'exit_code', 'cleanup_complete', 'log_truncated', 'pid')), 'own final process receipt differs')
    return dict(receipt=str(receipt), receipt_sha256=digest(receipt), candidate_sha256=data['candidate_sha256'],
        native_report_sha256=data['native_report_sha256'], process_sha256=digest(process_path), binding_sha256=digest(folder / 'final-drc-binding.json'),
        Native_counts=native, Native_application_policy=policy, finding_types=finding_types(data['native']),
        ignored_checks=ignored_check_facts(raw['ignored_checks'], report, 'ignored_checks', public_sanitize),
        ignored_check_count=len(raw['ignored_checks']), protected_count=None if export or 'protected_route_import' not in data else len(data['protected_route_import']['matches']),
        whole_project_drc_clean=None if trial else data['whole_project_drc_clean'], full_schematic_flag=True,
        interpretation='Stored own-final bytes only; no new Native, central readback, human or electrical qualification.')


def classify(outer, data, timing, arm, summary=None):
    method = [data.get('method_wall_seconds'), data.get('method_full_cpu_seconds', data.get('method_full_CPU_seconds'))]
    method_ok = all(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 450 for value in method)
    cap = timing['wall_seconds'] <= 600 and timing['CPU_seconds'] <= 600
    process = outer['process']
    qualified = (outer.get('passed') is True and outer.get('status') == 'completed' and process.get('status') == 'success'
        and type(process.get('exit_code')) is int and process['exit_code'] == 0
        and process.get('cleanup_complete') is True and process.get('log_truncated') is False
        and data.get('status') == 'completed' and data.get('controls_passed') is True
        and data.get('accepted') is False and data.get('production_admitted') is False and cap and method_ok)
    if arm == 'B2_portfolio': qualified = qualified and summary is not None and summary.get('status') in ('completed', 'no_valid_candidate')
    else: qualified = qualified and data.get('attempt_qualified') is True
    delivered = qualified and data.get('workflow_delivered') is True and data.get('outcome') in ('validated_delivery', 'validated_winner_delivery')
    negative = qualified and arm != 'Cimprove' and data.get('workflow_delivered') is not True and data.get('outcome') in ('validated_completed_negative', 'validated_no_valid_candidate')
    qualified = bool(delivered or negative)
    return dict(attempt_qualified=qualified, workflow_delivered=bool(delivered), validated_completed_negative=bool(negative),
        evidence_classification='validated_delivery' if delivered else 'validated_completed_negative' if negative else 'unqualified_or_not_delivered_method',
        complete_external_cap_ok=cap, method_cap_ok=method_ok,
        method_sample=dict(wall_seconds=method[0], full_CPU_seconds=method[1]))


def improve_auxiliary(folder, data, plan):
    """Stored Default/field/PRL bridges, shared by parent, child and trials."""
    audit = read(folder/'final-netclass-audit.json'); mapping = folder/'final-netclasses.json'
    require(audit['candidate_sha256'] == data['candidate_sha256']
        and audit['project_sha256'] == plan['source_hashes'][Path(plan['source']).with_suffix('.kicad_pro').name]
        and audit['native_map_file_sha256'] == digest(mapping) and audit['native']['passed'] is True
        and audit['route_dimensions']['passed'] is True
        and audit['default_targets']['policy'] == 'single-default-global-floor-targets-v2', 'own Improve Default audit differs')
    proof = read(folder/'final-drc-fields-proof.json'); binding = read(folder/'final-drc-binding.json')
    require(data['native']['field_parity'] == proof, 'own field proof differs from Native record')
    for name, key in (('final-drc.json','native_report_sha256'),('final-drc-binding.json','binding_sha256'),
        ('final-drc-fields.net','netlist_sha256'),('final-drc-fields.json','fields_sha256'),
        ('final-drc-fields-local-settings.json','local_settings_guard_sha256')):
        require(digest(folder/name) == proof[key], 'own field hash bridge changed')
    guard = read(folder/'final-drc-fields-local-settings.json')
    require(guard['input'] == binding['input'] and guard['before'] == guard['after'] == binding['after']
        and guard['policy'] == 'job-owned-field-prl-immutable-v1', 'field input/PRL bridge differs')
    protection = guard['protection']
    require(protection['policy'] == 'mac-owned-prl-immutable-v1' and type(protection['present']) is bool
        and (protection['present'] is False or protection.get('flags_restored') is True
             and protection.get('bytes_unchanged') is True), 'field PRL restoration incomplete')
    for name in ('final-drc-fields-netlist','final-drc-fields-audit'):
        journal = folder/(name+'-process.json'); process = read(journal)
        require(digest(journal) == guard['processes_sha256'][name] and process['cwd'] == str(folder)
            and process['status'] == 'success' and process['exit_code'] == 0
            and process['cleanup_complete'] is True and process['log_truncated'] is False, 'field process custody differs')
    names = ('final-netclass-audit.json','final-netclasses.json','final-netclasses-process.json',
        'refill-drc.json','refill-drc-binding.json','refill-drc-process.json','final-drc-fields-proof.json',
        'final-drc-fields-local-settings.json','final-drc-fields-netlist-process.json','final-drc-fields-audit-process.json')
    require(type(proof['qualification']) is dict and type(proof['qualification'].get('qualified')) is bool,
            'typed field qualification required')
    return dict(files_sha256={name:digest(folder/name) for name in names},
        field_qualification=dict(qualified=proof['qualification']['qualified'],
            detail=field_fact(proof['qualification'],folder/'final-drc-fields-proof.json','qualification',True)),
        Default_targets_policy=audit['default_targets']['policy'],
        protected_count=audit['route_dimensions']['checked']['protected'])


def improve_facts(receipt, plan, allowed, *, qualified_parent, public_sanitize=False):
    """Retain every attempt; only completed trials receive own-final facts.

    Trial records inherit caller-frozen source/tool context, never fabricated
    Route headers. This is stored evidence reporting, not central revalidation.
    """
    receipt = pv.canonical(Path(receipt)); parent = read(receipt); folder = receipt.parent
    require(type(qualified_parent) is bool, 'typed parent qualification required')
    require(any(root in receipt.parents for root in allowed), 'Improve parent escaped frozen arm')
    rows = parent.get('trials', [])
    require(type(rows) is list and len(rows) <= 32, 'bounded Improve trial population required')
    result = dict(parent_receipt_sha256=digest(receipt), trials=[], qualified_parent=qualified_parent)
    incumbent_path = folder/'incumbent/result.json'
    if not qualified_parent:
        for row in rows:
            require(type(row) is dict and type(row.get('id')) is str, 'raw trial row malformed')
        # Failed parents remain raw; missing or incomplete trial material cannot
        # be upgraded to an independently qualified routing result.
    else:
        require(parent['accepted'] is True and parent['strategy'] == 'native_validated_zone_net_pruning'
            and parent['proposal_policy'] == 'single' and parent['engine_profile'] == 'tuned'
            and parent['budget_seconds'] == parent['cpu_budget_seconds'] == 420
            and parent['finalization_reserve_seconds'] == parent['finalization_cpu_reserve_seconds'] == 25,
            'shipped single Improve parent contract differs')
        marker = parent['native7_improve_parent']; sidecar = folder/'native7-improve-parent.json'
        context = read(sidecar)['context']
        require(marker == dict(policy='selected-native7-single-improve-parent-v1',file=sidecar.name,sha256=digest(sidecar))
            and context['parent'] == str(folder) and context['output'] == str(folder/'incumbent')
            and context['source'] == plan['source'] and context['source_hashes'] == plan['source_hashes']
            and context['runtime'] == plan['runtime'] and context['method_seconds'] == 420
            and context['finalization_reserve_seconds'] == 25 and context['scoring_variant'] is None
            and context['profile'] == 'tuned' and context['proposal_policy'] == 'single'
            and context['tools_sha256'] == hashlib.sha256(f.canonical(plan['tools']).encode()).hexdigest(),
            'Improve parent marker/context differs')
        result['parent_auxiliary'] = improve_auxiliary(folder,parent,plan)
    best = None; best_metrics = None
    if incumbent_path.is_file():
        inc = read(incumbent_path); summary = parent.get('incumbent') or {}
        summary_matches = (summary.get('receipt') == str(incumbent_path) and summary.get('status') == inc.get('status')
            and summary.get('accepted') is inc.get('accepted'))
        require(summary_matches or not qualified_parent, 'incumbent summary differs')
        result['incumbent'] = dict(receipt=str(incumbent_path),receipt_sha256=digest(incumbent_path),
            status=inc.get('status'),accepted=inc.get('accepted'),Native_counts=counts(inc.get('native')),
            reasons=reasons(inc,incumbent_path,public_sanitize),summary_matches=summary_matches)
        if qualified_parent:
            child_context = incumbent_path.parent/'improve-child-context.json'
            require(inc['native_improve_child'] == dict(policy='selected-native7-single-improve-child-v1',
                file=child_context.name,sha256=digest(child_context)) and read(child_context) == context,
                'incumbent context differs from its exact parent')
            result['incumbent']['own_final'] = own_final(incumbent_path,export=False,plan=plan,allowed=allowed,accepted=True,public_sanitize=public_sanitize)
            result['incumbent']['auxiliary'] = improve_auxiliary(incumbent_path.parent,inc,plan)
            basis = parent['native7_default_target_basis']; guide = incumbent_path.parent/'default-targets.json'
            require(basis == dict(policy='single-default-global-floor-targets-v2',receipt='incumbent/result.json',
                receipt_sha256=digest(incumbent_path),file='incumbent/default-targets.json',sha256=digest(guide))
                and inc['default_target_transport'] == dict(policy=basis['policy'],file=guide.name,sha256=basis['sha256']),
                'mandatory inherited Default basis differs')
        best, best_metrics = inc.get('candidate_sha256'),inc.get('metrics')
    else: require(not qualified_parent, 'qualified Improve parent lacks incumbent')
    trial_root = folder/'trials'
    if qualified_parent:
        require(trial_root.is_dir() and {path.name for path in trial_root.iterdir()} == {f'trial-{i:04d}' for i in range(len(rows))}, 'omitted or extra Improve trial folder')
    for index,row in enumerate(rows):
        directory = pv.canonical(trial_root/f'trial-{index:04d}'); path = directory/'result.json'
        require(row.get('id') == directory.name and row.get('receipt') == str(path), 'trial escaped canonical ordered parent')
        require(path.is_file() or not qualified_parent, 'qualified parent has missing trial receipt')
        if not path.is_file():
            result['trials'].append(dict(id=directory.name,receipt=str(path),missing=True)); continue
        trial = read(path)
        require(row == dict(id=directory.name,receipt=str(path),status=trial.get('status'),accepted=trial.get('accepted'))
            and trial.get('id') == directory.name and type(row.get('accepted')) is bool
            and type(trial.get('accepted')) is bool, 'trial summary differs')
        fact = dict(id=directory.name,receipt=str(path),receipt_sha256=digest(path),status=trial.get('status'),
            accepted=trial['accepted'],Native_counts=counts(trial.get('native')),metrics=metric_facts(trial.get('metrics')),
            reasons=reasons(trial,path,public_sanitize))
        if trial.get('native') is not None:
            fact['finding_types'] = finding_types(trial['native'])
            fact['ignored_checks'] = ignored_check_facts(trial['native']['ignored_checks'],path,'native.ignored_checks',public_sanitize)
        raw_evidence = {}
        for name,key in (('candidate/'+Path(plan['source']).name,'candidate_sha256'),('final-drc.json','native_report_sha256')):
            file = directory/name
            if file.is_file():
                pin = digest(file)
                require(trial.get(key) is None or trial[key] == pin, 'raw trial candidate/report hash differs')
                raw_evidence[key] = pin
        for name in ('final-drc-process.json','final-drc-binding.json','refill-drc-process.json'):
            if (directory/name).is_file(): raw_evidence[name] = digest(directory/name)
        fact['stored_native_evidence'] = raw_evidence
        fact['Native_completion_qualified'] = False
        completed = trial.get('status') in ('improvement_validated','quality_rejected','drc_rejected') and 'reason' not in trial
        if qualified_parent:
            require(trial.get('base_candidate_sha256') == best, 'trial base differs from previous checked best')
            require(trial['accepted'] is (trial.get('status') == 'improvement_validated'), 'trial selection/status differs')
        if qualified_parent and completed:
            guard = trial['single_trial_guard']; start=trial['started_elapsed_seconds']; finish=trial['finished_elapsed_seconds']; used=trial['finished_observed_cpu_seconds']
            values=(start,finish,used,guard['wall_deadline_elapsed_seconds'],guard['work_cpu_limit_seconds'])
            require(all(type(v) in (int,float) and math.isfinite(v) and v >= 0 for v in values)
                and start <= finish <= guard['wall_deadline_elapsed_seconds'] <= 395
                and used <= guard['work_cpu_limit_seconds'] == 395
                and all(step.get('status') in ('success','nonzero_exit') for step in trial['steps']), 'trial exceeded work reserve or worker failed')
            fact['own_final'] = own_final(path,export=False,plan=plan,allowed=allowed,accepted=trial['accepted'],
                public_sanitize=public_sanitize,trial_parent=parent)
            fact['auxiliary'] = improve_auxiliary(directory,trial,plan)
            fact['Native_completion_qualified'] = True
            if trial['accepted']:best,best_metrics=trial['candidate_sha256'],trial['metrics']
        else:
            require(not qualified_parent or not trial['accepted'], 'unqualified trial was selected')
            fact['interpretation']='Unqualified retained attempt; no Native-completion or selection claim.'
        result['trials'].append(fact)
    if qualified_parent:
        require(parent['metrics'] == parent['best_observed_metrics'] == best_metrics, 'parent/selected-best metrics differ')
        result['interpretation']='Own parent/incumbent and every trial retained; parent refill has its own hash, not an assumed selected-trial byte hash.'
    return result


def population_shape(population, children):
    require(type(population.get('schema')) is int and population['schema'] == 1 and population.get('kind') in KINDS, 'unsupported frozen population schema')
    version = 'improve-v2' if population['kind'] == frozen.IMPROVE_POPULATION_KIND else 'legacy-v1'
    names, order, _, _, _ = frozen.contract(version)
    require(population['population'] == list(names) and population['planned_arm_order'] == list(order)
            and population['limits'] == frozen.LIMITS, 'frozen arm population/budgets differ')
    families = population['planned_family_order']
    require(type(families) is list and 1 <= len(families) <= 4 and len(set(families)) == len(families)
            and set(families) == set(population['families']) == set(population['outputs']) == set(children['protocols']), 'family denominator differs')
    require(type(children.get('schema')) is int and children['schema'] == 1 and children['administration_head'] == population['administration_head']
            and children['policy_or_board_changes_after_first_arm'] is False, 'child freeze authority differs')
    for family in families:
        require(re.fullmatch(r'[a-z][a-z0-9-]{0,63}', family) and set(children['protocols'][family]) == set(names)
                and set(population['outputs'][family]) == set(names), 'omitted/extra planned arm')
    native_only = {
        'frozen-runtime043-labelled-IR-native-support-followup-v1': 'runtime043-labelled-native-only-IR-followup-prerequisites-v1',
        'frozen-runtime049-labelled-Devobordo-native-CLI-development-followup-v1': 'runtime049-labelled-native-CLI-Devobordo-prerequisites-v1',
        'frozen-runtime050-labelled-Devobordo-native-CLI-development-followup-v1': 'runtime050-labelled-native-CLI-Devobordo-prerequisites-v1',
    }
    if population['kind'] in native_only:
        q = population['qualification']
        require(q['source_head'] == population['source_head'] and q['runtime'] == population['runtime']
                and q['runtime_manifest_sha256'] == population['runtime_manifest_sha256'], 'Native-only prerequisite identity differs')
        require(q['kind'] == native_only[population['kind']]
                and q['actual_GUI_qualified'] is False and q['full_GUI_claim'] is False, 'Native-only qualification promoted or malformed')
    elif version == 'improve-v2':
        q = population['qualification']
        require(q['kind'] == frozen.IMPROVE_QUALIFICATION_KIND and q['actual_GUI_qualified'] is False
            and q['full_GUI_claim'] is False, 'installed CLI-only qualification promoted or malformed')
    else:
        require(population['qualification']['kind'] == frozen.QUALIFICATION_KIND
                and population['qualification']['full_GUI_claim'] is False, 'public freezer qualification schema differs')
    return families


def administration(population):
    """Frozen seven-file commit, not the reporter's later/current Git HEAD."""
    pins = population['tracked_administration_files_sha256']; head = population['administration_head']
    require(type(pins) is dict and set(pins) == set(frozen.ADMIN_FILES) and pv._HEAD.fullmatch(head), 'frozen administration population differs')
    opts = ('-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '--literal-pathspecs')
    rows = pv._git(ROOT, *opts, 'ls-tree', '-r', '-l', '-z', head, '--', *sorted(pins)).split(b'\0')
    blobs = {}
    for row in filter(None, rows):
        metadata, name = row.split(b'\t', 1); mode, kind, oid, size = metadata.split()
        require(mode in (b'100644', b'100755') and kind == b'blob' and size.isdigit(), 'committed regular administration required')
        blobs[name.decode()] = (oid.decode(), int(size))
    require(set(blobs) == set(pins), 'incomplete frozen commit administration')
    for name, (oid, size) in blobs.items():
        raw = pv.read_bytes(ROOT / name)
        require(size == len(raw) and hashlib.sha256(raw).hexdigest() == pins[name]
                and pv._git(ROOT, *opts, 'cat-file', 'blob', oid, limit=pv.MAX_FILE_BYTES) == raw, 'frozen administration bytes changed')


def plan_binding(plan, family, arm, entry, population, population_path, population_pin):
    version = 'improve-v2' if population['kind'] == frozen.IMPROVE_POPULATION_KIND else 'legacy-v1'
    names, _, _, method_kind, child_name = frozen.contract(version)
    runtime = Path(population['runtime']); output = pv.canonical(Path(population['outputs'][family][arm]))
    require(output.parent == runtime / '.runs' and plan['output'] == str(output), 'frozen method output differs')
    require(plan['runtime'] == str(runtime) and plan['runtime_manifest_sha256'] == population['runtime_manifest_sha256']
            and plan['source_head'] == population['source_head'] and plan['source'] == entry['source']
            and plan['source_hashes'] == entry['source_hashes'] and plan['source_rights'] == entry['source_rights']
            and plan['population_protocol_path'] == str(population_path) and plan['population_protocol_sha256'] == population_pin
            and plan['enclosure_sha256'] == population['enclosure_sha256'] == frozen.ENCLOSURE_SHA
            and plan['whole_wall_full_cpu_seconds'] == 600 and plan['pass_key'] == 'controls_passed'
            and plan['administration_root'] == str(ROOT), 'frozen source/runtime/protocol binding differs')
    tools = plan['tools']; provenance = tools['source_provenance']
    require(tools['git_head'] == provenance['git_head'] == population['source_head'] and tools['kicad'] == '10.0.7'
            and provenance['manifest_sha256'] == population['runtime_manifest_sha256']
            and tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2', 'frozen selected7 tools differ')
    pins = population['tracked_administration_files_sha256']
    if arm == 'B2_portfolio':
        require(plan['kind'] == 'installed-native7-comparison-portfolio-functional-v1'
            and all(plan[key] == value for key, value in frozen.LIMITS.items())
            and plan['variants'] == list(frozen.VARIANTS) and plan['allocation'] == 'balanced'
            and plan['trial_readback_reserve_seconds'] == 30 and plan['root_finalization_reserve_seconds'] == 15
            and plan['installed_trial_accounting_policy'] == 'installed-route-readback-reserve-v1'
            and plan['comparison_api_policy'] == 'installed-native7-scored-portfolio-api-v2'
            and plan['administration_head'] == population['administration_head']
            and plan['administration_files_sha256'] == {name: pins[name] for name in frozen.ADMIN_FILES[:3]}
            and plan['controller'] == str(ROOT / frozen.ADMIN_FILES[0])
            and plan['controller_sha256'] == pins[frozen.ADMIN_FILES[0]], 'portfolio contract differs')
    else:
        require(plan['kind'] == method_kind and plan['arm'] == arm
            and plan['population'] == list(names) and plan['outputs'] == population['outputs'][family]
            and plan['limits'] == frozen.LIMITS and plan['default_settings'] == population['default_settings']
            and plan['controller'] == str(runtime / '.runs'/child_name)
            and plan['controller_sha256'] == pins['scripts/qualify_current_method.py']
            and plan['qualifier_sha256'] == pins['scripts/qualify_installed_workflow.py']
            and plan['source_inventory_sha256'] == hashlib.sha256((f.canonical(entry['source_hashes']) + '\n').encode()).hexdigest()
            and plan['source_rights_sha256'] == hashlib.sha256(f.canonical(entry['source_rights']).encode()).hexdigest(), 'method contract differs')
        if version == 'improve-v2': require(plan['improve_settings'] == population['improve_settings'], 'Improve settings changed')
        prerequisites = plan['prerequisite_sha256']
        require(type(prerequisites) is dict and 1 <= len(prerequisites) <= 32, 'bounded frozen prerequisite map required')
        for path, pin in prerequisites.items(): require(digest(Path(path), MAX_JSON) == pin, 'prerequisite changed')
    require(digest(Path(plan['controller'])) == plan['controller_sha256'], 'copied/external controller changed')
    return output


def report(*, population, population_sha256, children, children_sha256, output, public_sanitize=False):
    population = pv.canonical(Path(population)); children = pv.canonical(Path(children)); output = pv.canonical(Path(output))
    require(children.parent == population.parent and children.name == 'frozen-children.json' and population.name == 'population.json', 'explicit paired freeze files required')
    pop = pinned(population, population_sha256); frozen_children = pinned(children, children_sha256)
    families = population_shape(pop, frozen_children)
    require(frozen_children['population_path'] == str(population) and frozen_children['population_sha256'] == population_sha256, 'child population hash differs')
    runtime = pv._directory(Path(pop['runtime'])); manifest = runtime / pv.MANIFEST
    require(digest(manifest, pv.MAX_MANIFEST_BYTES) == pop['runtime_manifest_sha256'], 'runtime manifest changed')
    manifest_data = read(manifest); implementation = {name: pin for name, pin in pv._file_map(manifest_data['immutable_files_sha256']).items() if name.startswith('autorouter/')}
    identity = pv._runtime_identity(runtime, implementation)
    require(identity['git_head'] == pop['source_head'] and identity.get('native_version') == '10.0.7', 'runtime source/selected version changed')
    source_spec = dict(schema=1, split='development-exposed', families=pop['families'])
    require(frozen.sources(source_spec, runtime) == pop['families'], 'original complete source inventory differs')
    administration(pop)
    require(output.parent.is_dir() and output.parent.stat().st_uid == os.getuid() and not os.path.lexists(output)
            and not any(root == output or root in output.parents or output in root.parents for root in
                        (runtime, population.parent, *[Path(entry['source']).parent for entry in pop['families'].values()])), 'fresh owned non-overlapping report output required')
    rows = []; observations = []; output_owner = {}
    for family in families:
        entry = pop['families'][family]
        for arm in pop['planned_arm_order']:
            item = frozen_children['protocols'][family][arm]; protocol = pv.canonical(Path(item['path']))
            require(protocol == population.parent / family / arm / 'protocol.json', 'protocol escaped exact planned folder')
            plan = pinned(protocol, item['sha256']); out = plan_binding(plan, family, arm, entry, pop, population, population_sha256)
            outer_path = protocol.parent / 'enclosure/result.json'; outer = read(outer_path)
            require(outer['protocol_sha256'] == item['sha256'] and outer['status'] in ('completed', 'failed', 'budget_exceeded')
                    and type(outer['passed']) is bool, 'every planned arm needs its own terminal enclosure')
            process = read(protocol.parent / 'enclosure/process.json')
            require(process == outer['process'] and all(type(process.get(key)) is bool for key in ('cleanup_complete', 'log_truncated'))
                    and process['cwd'] == str(protocol.parent / 'enclosure') and process['log'] == str(protocol.parent / 'enclosure/command.log')
                    and type(process.get('argv')) is list and str(protocol) in process['argv'] and item['sha256'] in process['argv'], 'outer process/cleanup/command binding differs')
            for name in ('outer.log', 'enclosure/command.log'): pv.file_digest(protocol.parent / name, 512 * 1024)
            require(plan['tools']['source_provenance'] == identity and plan['tools']['implementation_sha256'] == implementation, 'protocol runtime identity differs')
            extra = custody(out, plan, outer, arm); allowed = [out, *extra]
            child = out / 'result.json'; data = read(child) if child.is_file() else {}
            if data:
                require(data['protocol_sha256'] == item['sha256'] and data['controller_sha256'] == plan['controller_sha256']
                        and data['runtime'] == str(runtime) and data['source'] == plan['source']
                        and data['source_hashes'] == entry['source_hashes'] and data['tools'] == plan['tools'], 'terminal child identity differs')
            timing = complete_cost(protocol.parent / 'outer-time.log')
            summary = None; trials = []
            if arm == 'B2_portfolio':
                summary_path = extra[0] / 'portfolio-summary.json'
                if summary_path.is_file(): summary = read(summary_path)
                bound = summary is not None and data.get('portfolio_summary_sha256') == digest(summary_path)
                if data.get('portfolio_summary_sha256') is not None: require(bound, 'portfolio summary hash differs')
                if summary is not None:
                    trial_rows = summary['trials']; ids = [row['id'] for row in trial_rows]
                    require(type(trial_rows) is list and len(ids) <= 3 and len(set(ids)) == len(ids)
                            and all(name in frozen.VARIANTS for name in ids), 'portfolio trial denominator differs')
                    for trial in trial_rows:
                        variant = trial['id']; expected = extra[frozen.VARIANTS.index(variant) + 1] / 'route/result.json'
                        fact = dict(variant=variant, eligible=trial.get('eligible'), validated_rejection=trial.get('validated_rejection'),
                            status=trial.get('status'), Native_counts=counts(trial.get('native')), result_sha256=trial.get('result_sha256'),
                            reasons=reasons(trial, summary_path, public_sanitize))
                        if trial.get('result') is not None:
                            require(Path(trial['result']) == expected and digest(expected) == trial['result_sha256'], 'portfolio trial result/hash differs')
                            attempt = read(expected); fact['raw_reasons'] = reasons(attempt, expected, public_sanitize)
                            if trial.get('eligible') is True or trial.get('validated_rejection') is True:
                                fact['own_final'] = own_final(expected, export=False, plan=plan, allowed=allowed,
                                    accepted=trial.get('eligible') is True, public_sanitize=public_sanitize)
                                require(fact['Native_counts'] == fact['own_final']['Native_counts'], 'trial summary Native counts differ')
                        else: require(trial.get('eligible') is not True and trial.get('validated_rejection') is not True, 'qualified trial has no own receipt')
                        trials.append(fact)
            state = classify(outer, data, timing, arm, summary)
            if arm == 'B2_portfolio' and state['attempt_qualified']:
                require(bound and summary.get('all_variants_attempted') is True and len(trials) == 3
                        and [row['variant'] for row in trials] == list(frozen.VARIANTS)
                        and all(row['eligible'] is True or row['validated_rejection'] is True for row in trials), 'qualified portfolio lacks all three bound trials')
                if state['validated_completed_negative']:
                    require(summary.get('selected') is None and all(row['validated_rejection'] is True for row in trials), 'all-negative portfolio has a winner or unqualified trial')
            row = dict(family=family, arm=arm, **state, complete_cost=timing,
                outer_passed=outer['passed'], outer_status=outer['status'], process_status=process['status'], cleanup_complete=process['cleanup_complete'], log_truncated=process['log_truncated'],
                controller_status=data.get('status'), outcome=data.get('outcome'), Native_counts=counts(data.get('route_native', data.get('native'))),
                route_metrics=metric_facts(data.get('route_metrics')), delivered_metrics=metric_facts(data.get('metrics')),
                protocol_sha256=item['sha256'], outer_sha256=digest(outer_path), child_sha256=outer['child_sha256'], source_hashes=entry['source_hashes'],
                reasons=dict(child=reasons(data, child, public_sanitize), outer=reasons(outer, outer_path, public_sanitize)))
            if state['attempt_qualified'] and arm != 'B2_portfolio':
                if state['validated_completed_negative']:
                    require(data.get('negative_readback', {}).get('validated_rejection') is True, 'negative has no stored reader witness')
                selected = Path(data['selected_route_receipt'])
                require(digest(selected) == data['selected_route_sha256'], 'selected route receipt hash differs')
                row['route_own_final'] = own_final(selected, export=False, plan=plan, allowed=allowed,
                    accepted=state['workflow_delivered'], public_sanitize=public_sanitize)
            if state['workflow_delivered']:
                proofs = {}
                for label, path_key, hash_key, is_export in (('route', 'selected_route_receipt', 'selected_route_sha256', False), ('export', 'export_receipt', 'export_sha256', True)):
                    receipt = Path(data[path_key]); require(digest(receipt) == data[hash_key], 'delivery receipt hash differs')
                    proofs[label] = own_final(receipt, export=is_export, plan=plan, allowed=allowed, accepted=True, public_sanitize=public_sanitize)
                require(proofs['route']['candidate_sha256'] == proofs['export']['candidate_sha256'], 'Route/export candidates differ')
                row['delivered_own_proof'] = proofs
                if arm == 'Cimprove':
                    row['export_auxiliary'] = improve_auxiliary(Path(data['export_receipt']).parent/'validation',read(Path(data['export_receipt'])),plan)
                if arm == 'B2_portfolio':
                    winner = summary['selected']
                    require(type(winner) is dict and winner['id'] in frozen.VARIANTS
                        and Path(data['selected_route_receipt']) == extra[frozen.VARIANTS.index(winner['id']) + 1] / 'route/result.json'
                        and winner['result_sha256'] == data['selected_route_sha256']
                        and winner['candidate_sha256'] == proofs['route']['candidate_sha256']
                        and winner['native_report_sha256'] == proofs['route']['native_report_sha256'], 'portfolio winner differs from delivered own proof')
            if arm == 'B2_portfolio':
                row['portfolio'] = dict(status=summary.get('status') if summary else None, summary_bound_to_child=bound,
                    summary_sha256=digest(summary_path) if summary else None, trials=trials,
                    unattempted_variants=summary.get('unattempted_variants') if summary else list(frozen.VARIANTS),
                    selected=({key: summary['selected'].get(key) for key in ('id', 'result_sha256', 'candidate_sha256', 'native_report_sha256', 'vias', 'length_mm')} if summary and summary.get('selected') else None))
            if arm == 'B0': row['stock_DSN_observation'] = {key: data.get(key) for key in ('stock_native_dsn_sha256', 'stock_task_dsn_sha256', 'stock_dsn_identical')}
            if arm == 'Cimprove':
                parent_path = Path(data['workspace'])/'route/result.json' if data.get('workspace') else out/'route/result.json'
                require(out in pv.canonical(parent_path).parents, 'Improve parent escaped frozen method')
                if parent_path.is_file():
                    row['Improve'] = improve_facts(parent_path,plan,allowed,
                        qualified_parent=state['workflow_delivered'],public_sanitize=public_sanitize)
                else: require(not state['attempt_qualified'], 'qualified Improve has no parent')
            if not state['attempt_qualified'] and arm != 'B2_portfolio':
                raw_path = Path(data['workspace']) / 'route/result.json' if arm in ('Cdefault','Cimprove') and data.get('workspace') else out / ('thermal-route/result.json' if arm == 'Cthermal' else 'route/result.json')
                require(out in pv.canonical(raw_path).parents, 'raw failure receipt escaped frozen method')
                if raw_path.is_file():
                    raw = read(raw_path)
                    row['unqualified_raw_attempt'] = dict(receipt=str(raw_path), receipt_sha256=digest(raw_path), status=raw.get('status'), accepted=raw.get('accepted'),
                        schematic_parity=raw.get('schematic_parity'), Native_counts=counts(raw.get('native')), reasons=reasons(raw, raw_path, public_sanitize),
                        finding_types=finding_types(raw['native']) if raw.get('native') is not None else None,
                        ignored_checks=ignored_check_facts(raw['native']['ignored_checks'], raw_path, 'native.ignored_checks', public_sanitize) if raw.get('native') is not None else None,
                        interpretation='Raw source/design/transport/routing failure only; never promoted to qualified negative/delivery by this reporter.')
            metadata_pins = {name: digest(protocol.parent / name) for name in ('outer-time.log', 'outer.log', 'enclosure/process.json', 'enclosure/command.log', 'enclosure/result.json')}
            rows.append(row); observations.append((protocol, item['sha256'], out, plan, outer, arm, metadata_pins))
    require(len(rows) == len(families) * len(pop['population']), 'entire frozen denominator required')
    def fresh():
        if output_owner: require(frozen.h.owned_destination(output_owner) == output, 'report output directory was replaced')
        else: require(not os.path.lexists(output), 'report output appeared before exclusive creation')
        pinned(population, population_sha256); pinned(children, children_sha256); administration(pop)
        require(pv._runtime_identity(runtime, implementation) == identity and frozen.sources(source_spec, runtime) == pop['families'], 'source/runtime changed during reporting')
        for protocol, pin, out, plan, outer, arm, metadata_pins in observations:
            pinned(protocol, pin); require(read(protocol.parent / 'enclosure/result.json') == outer, 'terminal enclosure changed')
            custody(out, plan, outer, arm)
            for name, digest_pin in metadata_pins.items(): require(digest(protocol.parent / name) == digest_pin, 'external-cost/process metadata changed')
    fresh()
    result = dict(schema=1, kind='stored-current-comparison-facts-v1', accepted=False, production_admitted=False, project_complete=False, actual_GUI=False, human_review=False,
        source_head=pop['source_head'], runtime_manifest_sha256=pop['runtime_manifest_sha256'], administration_head=pop['administration_head'],
        population_sha256=population_sha256, frozen_children_sha256=children_sha256, population_kind=pop['kind'], qualification_scope=KINDS[pop['kind']],
        planned_family_order=families, planned_arm_order=pop['planned_arm_order'], rows=rows, limits=pop['limits'], source_rights={name: entry['source_rights'] for name, entry in pop['families'].items()},
        complete_external_totals=dict(wall_seconds=round(sum(row['complete_cost']['wall_seconds'] for row in rows), 2), CPU_seconds=round(sum(row['complete_cost']['CPU_seconds'] for row in rows), 2)),
        record_is_authoritative=False, receipt_may_remain_on_refusal=True, public_sanitize=public_sanitize, reporter_sha256=digest(Path(__file__)),
        accounting='Complete external exits only are summed; method/portfolio/Native samples overlap and are not added. Setup/full/targeted/research/authoring/review/reporting/interactive costs additional; unmetered costs unknown, not zero.',
        scope='Stored evidence spot bindings, not Native revalidation/central-reader replay. Exposed development, not holdout/independent pedigree, default change, broad superiority/speed, fullGUI/human/electrical/Windows/restore/release qualification.',
        delivery_workload_caveat='B0 retains common fidelity/Native safeguards, not untouched vanilla. API comparison authority/delivery differs from C CLI workload; no generic algorithmic/end-to-end speed claim.',
        retention='Generated facts only; no CAD/DSN/SES/plots/raw findings/log copies. Default reason text is LOCAL and needs publication audit. Public-sanitize retains field/hash references, counts and classifications unchanged.')
    raw = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    require(len(raw) <= min(MAX_JSON, MAX_REPORT_BYTES), 'bounded fact report ceiling')
    output.mkdir(mode=0o700); frozen.h.capture_destination(output_owner, output)
    fresh()
    with (frozen.h.owned_destination(output_owner) / 'report.json').open('xb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    index = dict(schema=1, files=[dict(path='report.json', sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))], generated_only=True)
    frozen.save_new(frozen.h.owned_destination(output_owner) / 'files.json', index)
    fresh()
    require(digest(frozen.h.owned_destination(output_owner) / 'report.json') == index['files'][0]['sha256'], 'report bytes changed')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('population', 'children', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    for name in ('population-sha256', 'children-sha256'): parser.add_argument('--' + name, required=True)
    parser.add_argument('--public-sanitize', action='store_true')
    try:
        result = report(**vars(parser.parse_args(argv)))
        print(json.dumps(dict(rows=len(result['rows']), classifications=dict(Counter(row['evidence_classification'] for row in result['rows'])), accepted=False)))
        return 0
    except (ValueError, OSError, KeyError, TypeError, IndexError, f.p.Rejected) as exc:
        print('Comparison facts refused: ' + str(exc), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
