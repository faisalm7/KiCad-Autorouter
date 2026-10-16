"""Curate saved runtime008 GUI059 with shared read-only readers; no Native rerun.

Adapted from GUI057 readback002. Only this fresh controller and the selected
public evidence/notes are written; current stale exports are never repaired.
"""
from pathlib import Path
import datetime, hashlib, json, sys, time
START = time.monotonic()
ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-008/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, review_export as ex, placement_clearance as io, sexpr as sx
from autorouter import config as c, board_floor as g, floor_route as f, netclass as nc, local_settings as ls

base = runtime / '.runs/gui-session059'
workspace = base / 'jobs/autorouter-gui-7598cc61844943f7a80b04f466d53a8c'
PUBLIC = ROOT / 'evidence/gui-runtime008-059-native-opening-001.json'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']

def read(path): return f.read_json(Path(path))
def pin(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path))
def require(condition, reason):
    if not condition: raise p.Rejected(reason)
def payload(path):
    return io.inventory(path, contents=True, max_bytes=32 * 1024**2, max_files=2048, max_entries=4096)
def hash_payload(files): return {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
def fresh(path):
    require(not Path(path).exists() and not Path(path).is_symlink(), 'fresh curation destination required: ' + str(path))

def cli_stage(path):
    """CliJob schema has cleanup_scope, not runner.cleanup_complete."""
    value = read(path)
    log = path.with_name(path.name[:-len('.process.json')] + '.log')
    raw = io.read_bytes(log, 512 * 1024)
    require(type(value.get('exit_code')) is int and value.get('cancel_requested') is False
        and value.get('log_truncated') is False and value.get('log_bytes') == len(raw)
        and value.get('cleanup_scope') == 'CLI existing workers; UI does not certify descendant cleanup'
        and type(value.get('wall_seconds')) in (int, float) and value['wall_seconds'] >= 0,
        'actual CliJob process/log schema differs')
    return dict(process=pin(path), log=pin(log), argv=value['argv'], exit_code=value['exit_code'],
        cancel_requested=value['cancel_requested'], wall_seconds=value['wall_seconds'],
        log_truncated=value['log_truncated'], cleanup_scope=value['cleanup_scope'])

def geometry(source, candidate, protected):
    tree = sx.read(candidate)
    require(p.immutable(source) == p.immutable(tree), 'complete source invariant AST differs')
    require(sx.one(tree, 'layers') == sx.one(source, 'layers'), 'complete physical/display layer table differs')
    require(nc.four_copper_source_layers(tree) == LAYERS, 'canonical four-copper physical layers differ')
    require(len(protected) == 10 and all(p.locked(row) and row in p.routes(tree) for row in protected),
            'all ten exact locked protected routes required')
    source_pads = [(sx.one(fp, 'uuid'), sx.children(fp, 'pad')) for fp in sx.children(source, 'footprint')]
    candidate_pads = [(sx.one(fp, 'uuid'), sx.children(fp, 'pad')) for fp in sx.children(tree, 'footprint')]
    require(source_pads == candidate_pads and sum(len(rows) for _, rows in source_pads) == 6,
            'all source footprint/pad UUIDs and full geometry required')
    _, resolve = g.source_net_identity(tree)
    generated = [row for row in p.routes(tree) if row not in protected]
    inner = sorted({resolve(sx.one(row, 'net')) for row in generated
        if row[0] in {'segment', 'arc'} and sx.one(row, 'layer') in
        (['layer', '"In1.Cu"'], ['layer', '"In2.Cu"'])})
    require('ROUTE' in inner, 'required actual new inner ROUTE copper absent')
    vias = [row for row in generated if row[0] == 'via']
    require(all(sx.one(row, 'layers') == ['layers', '"F.Cu"', '"B.Cu"'] for row in vias),
            'generated through-via layer coverage differs')
    return dict(full_source_invariant_ast_exact=True, complete_layer_table_exact=True,
        source_pad_census_exact=True, physical_copper_layers=LAYERS,
        protected_route_count=len(protected), new_inner_nets=inner, generated_through_vias=len(vias))

def native_evidence(folder, data, candidate, source, protected, *, exported):
    """Replay each run's own retained Native/field/class/pour evidence."""
    binding = read(folder / 'final-drc-binding.json')
    require(binding['source'] == str(candidate), 'native final report bound to a different candidate')
    native = f.check_drc_stage(folder, data, 'final-drc', candidate,
        folder / 'final-drc-input' / candidate.name, False, binding['before'],
        schematic_parity=True, sandboxed=exported)
    require(native == data['native'] and p.native_accepted(native)
        and [native[k] for k in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 6, 0]
        and len(native['ignored_checks']) == 2, 'actual original-rule final Native findings differ')
    fields = native['field_parity']['qualification']
    require(fields['qualified'] is True and fields['component_count'] == 6
        and fields['compared_field_count'] == 18 and len(fields['warning_uuids']) == 6,
        'complete actual six-Datasheet field proof required')
    p.check_pour_evidence(folder, data, source, candidate,
        source_hashes=data['source_hashes'], correction=not exported, sandboxed=True if exported else False)
    matrix = read(folder / 'pour-keepout-audit.json')
    require(len(matrix['fill_checks']) == 2
        and any(row['layer'] == 'In1.Cu' and row['applicable'] is False
            and row['intersection'] and row['native_fill_outline_count'] > 0 for row in matrix['fill_checks'])
        and any(row['layer'] == 'In2.Cu' and row['applicable'] is True
            and not row['intersection'] and row['native_fill_outline_count'] > 0 for row in matrix['fill_checks']),
        'complete nonvacuous In1/In2 Native pour matrix required')
    classmap = read(folder / 'final-netclasses.json')
    classes = p.audit_candidate_netclasses(candidate, protected, classmap)
    classes['native_map_file_sha256'] = p.sha(folder / 'final-netclasses.json')
    require(classes == read(folder / 'final-netclass-audit.json'), 'own native class audit differs')
    require({row['name']: row['class'] for row in classmap['nets']} ==
        {'KEEP': 'Default', 'GND': 'SIGNAL,Default', 'ROUTE': 'POWER,Default'},
        'owned effective class/parent identities differ')
    prefix = f.SANDBOX if exported else []
    f.process_check(folder, data, 'final-netclasses', [*prefix, str(c.PYTHON),
        str(c.ROOT / 'autorouter/native.py'), 'netclasses', str(candidate), str(folder / 'final-netclasses.json')])
    ls.check_normal_policy(folder, data, max_bytes=256 * 1024**2, max_files=12000)
    return dict(final_drc=pin(folder / 'final-drc.json'), field_proof=pin(folder / 'final-drc-fields-proof.json'),
        classes=pin(folder / 'final-netclass-audit.json'), pour=pin(folder / 'pour-keepout-audit.json'),
        fill_checks=matrix['fill_checks'], native=native)


NOTES = ROOT / 'evidence/gui-runtime008-059-native-opening-notes-001'

def main():
    require(c.ROOT == runtime, 'shared readers must originate in runtime008')
    fresh(PUBLIC); fresh(NOTES)
    setup = read(runtime.parent / 'setup.json'); launch = read(base / 'launch.json')
    pre = read(base / 'preopen-001.json'); snapshot = Path(pre['snapshot'])
    tools = p.tool_manifest(); original = Path(launch['source']); source = sx.read(original)
    require(tools['git_head'] == setup['source_head'] == launch['source_git_head'] ==
        '76d2c666f3fe8f009e46f5421c77e18eaacbf7b2', 'frozen source identity differs')
    require(p.tree_hash(original.parent) == launch['source_sha256'] == setup['source_hashes'], 'original source changed')
    route_path = workspace / 'route/result.json'; export_path = workspace / 'export/export.json'
    gr = read(route_path); ge = read(export_path); initial = dict(pre['snapshot_hashes'])
    exportpin = p.sha(export_path)
    require(p.tree_hash(snapshot) == initial and len(initial) == 95 and
        p.sha(snapshot / 'export.json') == exportpin, '95-file pre-open proof changed')
    require(pre['source_unchanged'] is True and pre['route']['current'] is True and
        pre['export']['current'] is True and pre['human_review'] is False,
        'saved fresh pre-open reader evidence incomplete')
    require(gr['accepted'] is True and ge['export_accepted'] is True and
        ge['status'] == 'export_validated' and ge['tools'] == gr['tools'] == tools,
        'source/tool-bound accepted pre-open records differ')
    p.check_resource_accounting(ge, child_key='child_step_cpu_seconds')
    require(ge['control_child_cpu_seconds'] >= 0, 'new export CPU residual invalid')
    with p.validation_readback_session():
        route_check = p.check_result(route_path)
        binding, original_report = ex.bind(ge['inputs']['choice'])
        require(route_check['current'] is True and binding == ge['inputs'] and original_report == gr,
            'own route/choice/review lineage differs')
        try: ex.check_export(export_path)
        except p.Rejected as exc: stale = str(exc)
        else: raise p.Rejected('opened export unexpectedly current')
    require(stale == 'export inputs/runtime/evidence changed', 'unexpected stale refusal')
    after = p.tree_hash(workspace / 'export')
    changes = dict(added=sorted(set(after)-set(initial)), removed=sorted(set(initial)-set(after)),
        changed=sorted(k for k in set(initial)&set(after) if initial[k]!=after[k]))
    require(any(changes.values()), 'natural post-open material change absent')
    for name, digest in initial.items():
        if not name.startswith('validation/candidate/'):
            require(after.get(name) == digest, 'noncandidate proof changed: '+name)
    for suffix in ('.kicad_pcb', '.kicad_sch'):
        name = 'validation/candidate/' + original.with_suffix(suffix).name
        require(after.get(name) == initial[name], 'opened candidate board/schematic changed')
    protected = p.protected_for_record(gr, source)
    candidate = Path(gr['candidate']); frozen = snapshot / 'validation/candidate' / original.name
    require(p.sha(candidate) == gr['candidate_sha256'] == ge['candidate_sha256'] ==
        p.sha(frozen) == pre['export']['candidate_sha256'], 'candidate hash lineage differs')
    route_geometry = geometry(source, candidate, protected)
    require(route_geometry == geometry(source, frozen, protected) and
        p.routes(sx.read(candidate)) == p.routes(sx.read(frozen)), 'pre-open geometry differs')
    with p.validation_readback_session():
        route_native = native_evidence(workspace/'route', gr, candidate, source, protected, exported=False)
        # Current candidate PRO/PRL are stale. This reader validates only the
        # retained final stage, its original absolute process/input bindings and
        # unchanged input material; it does not authorize the current export.
        ef = workspace/'export/validation'; nb = read(ef/'final-drc-binding.json')
        export_stage = f.check_drc_stage(ef, ge, 'final-drc', Path(ge['candidate']),
            ef/'final-drc-input'/original.name, False, nb['before'],
            schematic_parity=True, sandboxed=True)
    require(export_stage == ge['native'] and p.native_accepted(export_stage), 'retained export DRC stage differs')
    frozen_folder = snapshot/'validation'; raw = read(frozen_folder/'final-drc.json')
    nb = read(frozen_folder/'final-drc-binding.json')
    expected = dict(launch['source_sha256']); expected[original.name] = ge['candidate_sha256']
    require(raw['$schema'] == 'https://schemas.kicad.org/drc.v1.json' and raw['kicad_version'] == '10.0.0' and
        raw['source'] == original.name and set(raw['included_severities']) == {'error','warning','exclusion'} and
        raw['violations']+raw['unconnected_items']+raw['schematic_parity'] == ge['native']['findings'] and
        nb['source'] == ge['candidate'] and nb['input'] == str(ef/'final-drc-input'/original.name) and
        nb['saved'] is False and nb['before'] == nb['after'] == expected and
        p.tree_hash(frozen_folder/'final-drc-input') == expected and
        p.sha(frozen_folder/'final-drc.json') == ge['native_report_sha256'], 'historical raw Native bindings differ')
    normalized = {}
    for suffix in ('.kicad_pro','.kicad_prl'):
        name = 'validation/candidate/' + original.with_suffix(suffix).name
        old = read(snapshot/name); new = read(workspace/'export'/name)
        normalized[suffix] = dict(preopen_sha256=initial[name],postopen_sha256=after[name],
            changed=initial[name]!=after[name],added_top_level_json_keys=sorted(set(new)-set(old)),
            changed_top_level_json_keys=sorted(k for k in set(old)&set(new) if old[k]!=new[k]),
            effective_equivalence_claimed=False)
    require(gr['metrics'] == ge['metrics'] and ge['metrics']['copper_layers'] == 4 and
        ge['metrics']['pads'] == ge['metrics']['footprints'] == 6 and ge['metrics']['zones'] == 3 and
        gr['schematic_parity'] == ge['schematic_parity'] == 'checked by final native DRC', 'fullSCH/metrics differ')
    preview = read(workspace/'preview.command.log'); review = read(workspace/'review/review.json')
    choice = read(workspace/'choice/choice.json')
    require(preview['existing_route_items'] == preview['protected_route_items'] == 10 and
        preview['rerouted_route_items'] == 0 and preview['copper_layers'] == LAYERS and
        preview['effective_preferences'] == gr['routing_preferences']['effective'], 'actual preview differs')
    require(review['preview']['layers'] == LAYERS and choice['choice'] == 'accept' and
        choice['human_pcb_approval_observed'] is False and choice['applied'] is False and
        ge['native_validation_performed'] is True and ge['human_pcb_approval_observed'] is False,
        'review/test-intent/export flags differ')
    for name, digest in review['preview']['files'].items():
        require(p.sha(workspace/'review'/name) == digest, 'preview changed: '+name)
    stages = [cli_stage(path) for path in sorted(workspace.glob('*.command.process.json'))]
    checks = []
    for path in sorted(workspace.glob('inspect-export-*.command.log')):
        value = read(path); process = cli_stage(path.with_suffix('.process.json'))
        require(process['argv'][-2:] == ['review-export-check',str(export_path)] and
            process['exit_code'] == (0 if value['current'] else 2), 'actual background status/exit differs')
        checks.append(dict(receipt=pin(path),process=process,current=value['current'],reason=value.get('reason')))
    require(len(checks)==2 and sum(x['current'] is True for x in checks)==1 and
        sum(x['current'] is False for x in checks)==1, 'positive/negative Open checked export reader pair required')
    for row in stages:
        if row['exit_code'] != 0:
            require('inspect-export-' in Path(row['process']['path']).name and row['exit_code']==2,
                'unexpected GUI command failure')
    require(len(stages)==8, 'exact eight saved CLI command journals required')
    verify = read(workspace/'verify_export.command.log')
    require(verify['current'] is True and verify['candidate_sha256']==ge['candidate_sha256'], 'saved verification differs')
    observations = dict(provenance='Lead-reported actual CUA observations during this session; curator performed no GUI operation.',
        setup='Fresh runtime008 at76d2, launcher059, isolated configuration/documents/cache without footprint libraries.',
        inspection='Finder opened the exact hidden inspection PRO. No native Open-picker attempt was made in059. Manager PCB Editor became available and launched the Python GUI.',
        configuration='Actual gui-session059 source/jobs,60seconds,Route/Finish gaps,all ten protected items,all source copper layers. Inspection PCB editor closed before routing.',
        sequence=['preview passed','Route passed','Create Review passed','Chrome showed actual original/candidate images for all four copper layers and all findings','owned preview closed and manager File Close Project','software-test accept intent recorded','fresh export passed','fresh preopen shared route/export readback passed and95-file snapshot retained','first Open checked export background reader currentTrue; actual export manager and Tools PCB Editor opened the four-copper export','editor closed and manager File Close Project','second Open checked export background reader refused stale evidence; actual inline generic failure observed'],
        focus_interruption='One Close Project action did not execute because focus was interrupted. The lead refreshed full state, then clicked the current Close Project control successfully; no extra Native run.',
        stale_panel='Actual inline generic failure observed, without an adopted positive. UX limitation: panel did not present the specific stale-evidence reason visible in the saved CLI log.',
        shutdown='Router closed normally, empty KiCad manager quit normally, launcher PID65474 reaped exit0; lead verified no active KiCad/GUI processes with scoped process checks.',
        human_review=False,physical_electrical_validation=False,GUI_DRC_performed=False,live_apply=False,
        cancellation_or_rejection_scenario_rerun=False)
    copies = {
        'source-as-run/curate-gui-runtime008-059.py':Path(__file__),
        'source-as-run/prepare-gui-runtime008-059.py':ROOT/'.runs/prepare-gui-runtime008-059.py',
        'source-as-run/gui059-preopen-001.py':ROOT/'.runs/gui059-preopen-001.py',
        'preopen-command.log':ROOT/'.runs/gui059-preopen-001-command.log',
        'preopen-time.log':ROOT/'.runs/gui059-preopen-001-time.log',
        'prepare-command.log':ROOT/'.runs/prepare-gui-runtime008-059-command.log',
        'records/launch.json':base/'launch.json','records/preopen-001.json':base/'preopen-001.json',
        'records/settings.json':workspace/'settings.json','records/preview.json':workspace/'preview.command.log',
        'records/route-result.json':route_path,'records/review.json':workspace/'review/review.json',
        'records/choice.json':workspace/'choice/choice.json','records/preopen-export.json':snapshot/'export.json',
        'records/route-final-drc.json':workspace/'route/final-drc.json',
        'records/route-final-drc-binding.json':workspace/'route/final-drc-binding.json',
        'records/route-final-drc-fields-proof.json':workspace/'route/final-drc-fields-proof.json',
        'records/preopen-export-final-drc.json':frozen_folder/'final-drc.json',
        'records/preopen-export-final-drc-binding.json':frozen_folder/'final-drc-binding.json',
        'records/preopen-export-final-drc-fields-proof.json':frozen_folder/'final-drc-fields-proof.json',
        'records/preopen-export-final-netclasses.json':frozen_folder/'final-netclasses.json',
        'records/preopen-export-final-netclass-audit.json':frozen_folder/'final-netclass-audit.json',
        'records/preopen-export-pour-keepout-audit.json':frozen_folder/'pour-keepout-audit.json'}
    for path in sorted(workspace.glob('*.command.process.json')):
        copies['records/'+path.name] = path
    for path in sorted(workspace.glob('inspect-export-*.command.log')):
        copies['records/'+path.name] = path
    copies['records/verify_export.command.log'] = workspace/'verify_export.command.log'
    record = dict(schema=1,kind='actual-runtime008-GUI059-route-fresh-export-native-opening-and-stale-refusal',
        accepted=False,qualification_passed=True,qualification_scope='Owned directive-free four-copper GUI route/review/fresh Native export/opening before natural staleness; actual background and generic inline stale refusal observed.',
        actual_GUI=True,human_review=False,physical_electrical_validation=False,
        GUI_route_export_open_passed=True,natural_stale_reader_passed=True,visual_generic_stale_refusal_observed=True,
        source_head=tools['git_head'],tools=tools,runtime_manifest=pin(runtime/'runtime-distribution.json'),
        curation_source=pin(Path(__file__)),launch=pin(base/'launch.json'),
        source_hashes=launch['source_sha256'],source_unchanged=True,
        route_receipt=pin(route_path),route_current_readback=route_check,
        export_receipt=pin(export_path),preopen_export_accepted=True,export_current=False,current_export_refusal=stale,
        candidate_sha256=gr['candidate_sha256'],native=ge['native'],metrics=ge['metrics'],geometry=route_geometry,
        route_own_native=route_native,preopen_export_retained_shared_DRC_stage=export_stage,
        preopen_export_proof_scope='Historical95-file pre-open proof with original absolute Native input/report/process/field bindings. Current normalized export project is stale, not audited for effective class equivalence or accepted.',
        preopen=pin(base/'preopen-001.json'),preopen_snapshot=str(snapshot.relative_to(ROOT)),
        preopen_snapshot_hashes=initial,post_open_changes=changes,post_open_project_normalization=normalized,
        project_settings_effective_equivalence_claimed=False,whole_project_clean=False,
        observations=observations,inspection_readers=checks,CLI_stages=stages,
        preview_file_count=len(review['preview']['files']),
        stage_compute={name:{k:value.get(k) for k in ('wall_seconds','total_cpu_seconds','budget_seconds','cpu_budget_seconds')}
            for name,value in [('route',gr),('rendered_review',review),('test_intent',choice),('fresh_export',ge)]},
        CPU_correction_actual_export=dict(parent_cpu_seconds=ge['parent_cpu_seconds'],child_step_cpu_seconds=ge['child_step_cpu_seconds'],
            control_child_cpu_seconds=ge['control_child_cpu_seconds'],monitor_cpu_seconds=ge['monitor_cpu_seconds'],total_cpu_seconds=ge['total_cpu_seconds']),
        preopen_readback_external_compute=dict(wall_seconds=1.99,CPU_seconds=1.96),
        interactive_whole_wall_seconds=None,interactive_full_CPU_seconds=None,
        GUI_preparation_complete_external_cost_known=False,
        related_evidence=[pin(ROOT/'evidence/gui-runtime007-058-export-accounting-refusal-001.json'),
            pin(ROOT/'evidence/export-cpu-roundoff-source-full141-001.json'),pin(ROOT/'evidence/mixer-hierarchy-diagnostic-001.json')],
        limitations=['Owned exposed fixture on the existing Mac/apps/cache and fixed runtime path; no comparative gain or generalized support claim.',
            'Six Datasheet parity warnings and two original ignored checks remain; whole-project DRC cleanliness is false.',
            'Full interactive/UI-idle wall and full CPU are unknown. CLI stages and Native receipts are separate bounded samples, not a whole interactive benchmark.',
            'Software-test accept intent is not human PCB approval. No new cancellation, reject-intent, live application/undo, unsaved-buffer, GUI DRC or physical/electrical qualification.',
            'Current export PRO/PRL and generated history/backup files changed after actual KiCad opening. No restoration, archive inspection, current class equivalence or accepted current export is claimed.',
            'Actual generic inline refusal was observed; the CLI retains the specific stale-evidence reason. More explanatory failure text remains a UX limitation.',
            'Current runtime008 CLI Native regression qualification belongs to the lead and is excluded from this GUI record.',
            'Curator used shared read-only readers only, with no Native/JVM rerun, GUI operation, product/docs edits or incidental Finder/Chrome contents.'],
        notes_directory=str(NOTES.relative_to(ROOT)),
        retained_files={name:dict(original=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)
            for name,path in copies.items()},utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    # Recheck immutable witnesses before any public write; never repair current export.
    require(p.tree_hash(snapshot)==initial and p.sha(export_path)==exportpin and
        p.tree_hash(original.parent)==launch['source_sha256'] and p.tree_hash(workspace/'export')==after and
        p.tool_manifest()==tools, 'late source/runtime/evidence drift')
    require(p.check_result(route_path)['current'] is True, 'late route readback failed')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):
            require(Path(module.__file__).resolve().is_relative_to(runtime), 'reader import escaped runtime008: '+name)
    NOTES.mkdir();(NOTES/'source-as-run').mkdir();(NOTES/'records').mkdir()
    for name,path in copies.items():
        target=NOTES/name
        with target.open('xb') as handle:handle.write(io.read_bytes(path,2*1024**2))
        require(p.sha(target)==p.sha(path), 'copied source/record differs')
    p.save_json(PUBLIC,record)
    print(json.dumps(dict(GUI_route_export_open_passed=True,natural_stale_reader_passed=True,
        visual_generic_stale_refusal_observed=True,preopen_files=len(initial),
        source_unchanged=True,export_current=False,public_sha256=p.sha(PUBLIC),curation_wall_seconds=time.monotonic()-START)))

if __name__ == '__main__': main()
