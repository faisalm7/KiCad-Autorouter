"""Prepare all twelve exposed-development plans before any arm executes.

Identity port of freeze-runtime033-interf-current-comparison-001.py. Execute only
after the lead has completed/reviewed GUI081 and checkpointed it. This freezer
does not infer GUI completion from a Git SHA, run Native, query live tools, or
qualify a comparison. The existing controllers/enclosure stay unchanged.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, re, resource, shutil, sys, time

START = time.monotonic()
def cpu():
    return sum(item.ru_utime + item.ru_stime for item in
        (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, provenance as pv, preferences as pref

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--expected-administration-head', required=True,
    help='Exact audited post-GUI checkpoint HEAD; keep it stable for all twelve arms.')
parser.add_argument('--gui-summary', required=True, type=Path,
    help='Absolute final current081 functional-role summary; partial summaries are refused.')
parser.add_argument('--gui-summary-sha256', required=True)
parser.add_argument('--gui-journal', required=True, type=Path,
    help='Absolute final frozen081 journal bound by that summary.')
parser.add_argument('--gui-journal-sha256', required=True)
args = parser.parse_args()
for value in (args.gui_summary_sha256, args.gui_journal_sha256):
    assert re.fullmatch('[0-9a-f]{64}', value)
for path in (args.gui_summary, args.gui_journal):
    assert path.is_absolute() and ROOT in path.parents
    assert path.is_file() and not path.is_symlink() and path.resolve() == path
    assert path.stat().st_size <= 4 * 1024**2
assert args.gui_summary != args.gui_journal
assert re.fullmatch('[0-9a-f]{40}', args.expected_administration_head)
expected_head = args.expected_administration_head
runtime = ROOT / '.runs/runtime-directory-042/runtime'
manifest = runtime / 'runtime-distribution.json'
base = ROOT / '.runs/runtime042-two-family-current-comparison-001'
gui = runtime / '.runs/gui-session081'
prepared_path = gui / 'prepared-state.json'
recovery_path = gui / 'recovery-controls-001/protocol-required-001.json'
sonde_path = ROOT / '.runs/runtime042-ordinary-sonde-whole-001/protocol.json'
native_packet = ROOT / 'evidence/runtime042-native-milestone-001.json'
source_head = '82aaa3b750007ef2ffaafd367ffcb718aa93865e'
manifest_pin = '1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
assert not os.path.lexists(base), 'Fresh two-family administration namespace required'
assert p.sha(manifest) == manifest_pin
assert p.sha(prepared_path) == '7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
prepared = f.read_json(prepared_path)
assert prepared['source_head'] == source_head and prepared['runtime_manifest_sha256'] == manifest_pin
assert Path(prepared['recovery_protocol']) == recovery_path
assert p.sha(recovery_path) == prepared['recovery_protocol_sha256']
recovery = f.read_json(recovery_path)
assert recovery['source_head'] == source_head and recovery['runtime_manifest_sha256'] == manifest_pin
tools = prepared['tools']
assert tools['git_head'] == source_head and tools['kicad'] == '10.0.7'
assert tools['source_provenance']['native_version'] == '10.0.7'
assert tools['source_provenance']['manifest_sha256'] == manifest_pin
assert tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2'
# Existing immutable source bytes, not a fresh tool/engine/Native query.
for name, digest in tools['implementation_sha256'].items():
    assert p.sha(runtime / name) == digest
assert p.sha(sonde_path) == '5ff2b18c17318ac4574c9541a7d8616e5fa929609f32d0db7e4f55c6e23cfa4a'
sonde = f.read_json(sonde_path)
assert sonde['runtime'] == str(runtime) and sonde['runtime_manifest_sha256'] == manifest_pin
assert sonde['source_head'] == source_head and sonde['rights']['license'] == 'CC-BY-SA-4.0'
assert p.sha(native_packet) == '7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b'
packet = f.read_json(native_packet)
assert packet['source_head'] == source_head and packet['runtime_manifest_sha256'] == manifest_pin
assert packet['full187']['passed'] is True and packet['install015']['passed'] is True
assert packet['actual_invalid']['passed'] is True
# Future final artifacts are supplied explicitly, never guessed from today's
# partial journal or from the changing documentation/administration HEAD.
assert p.sha(args.gui_summary) == args.gui_summary_sha256
assert p.sha(args.gui_journal) == args.gui_journal_sha256
gui_summary = f.read_json(args.gui_summary)
gui_journal = f.read_json(args.gui_journal)
assert gui_summary['source_head'] == source_head
assert gui_summary['runtime_manifest_sha256'] == manifest_pin
assert gui_summary['session'] == '081'
assert gui_summary['protocol_functional_roles_recorded'] is True
assert Path(gui_summary['journal']) == args.gui_journal
assert gui_summary['journal_sha256'] == args.gui_journal_sha256
assert gui_journal['runtime'] == '042' and gui_journal['session'] == '081'
assert gui_journal['protocol_functional_roles_recorded'] is True
assert gui_journal['active_workspace'] is None
assert type(gui_journal['frozen_utc']) is str and gui_journal['frozen_utc']
completed_gui = dict(summary=str(args.gui_summary), summary_sha256=args.gui_summary_sha256,
    journal=str(args.gui_journal), journal_sha256=args.gui_journal_sha256,
    scope='Lead-audited current081 functional roles only; exact supplied frozen artifacts, not human/physical/release qualification')

public = ROOT / 'scripts/qualify_current_method.py'
qualifier = ROOT / 'scripts/qualify_installed_workflow.py'
enclosure = ROOT / '.runs/enclose-native7-independent-control-004.py'
assert p.sha(public) == '2610e8175b0fcbe256b9e6c570cdc878019f3f357fe0f51296d3464b0f2bf837'
assert p.sha(qualifier) == '8f29bf021b109569e844d10a1a1009e54611cf0abc1be2500288b53edcdd9d8e'
assert p.sha(enclosure) == '9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4'
admin_names = ('scripts/qualify_comparison_portfolio.py',
    'scripts/experiment_portfolio.py', 'scripts/experiment_quality.py')
admin = {name: p.sha(ROOT / name) for name in admin_names}
assert admin['scripts/qualify_comparison_portfolio.py'] == 'c99d47fc0eec00e77b34539b4601a9dbc9dda03fdddd2e1d8c766664f284de90'
assert admin['scripts/experiment_portfolio.py'] == 'a748da6492963fafd5418cddaac39bbf0313830b240ca7e2a120145c4aaa1e17'
# Same bounded, read-only tracked-source identity checks as the033 freezer.
assert pv.git_head(ROOT) == expected_head
tracked = {**admin, 'scripts/qualify_current_method.py': p.sha(public),
    'scripts/qualify_installed_workflow.py': p.sha(qualifier)}
assert not pv._git(ROOT, 'status', '--porcelain=v1', '--untracked-files=all', '--', *tracked)
for name, digest in tracked.items():
    assert hashlib.sha256(pv._git(ROOT, 'show', expected_head + ':' + name)).hexdigest() == digest

repair = recovery['recovery']['repair']
interf = Path(repair['original_source'])
assert interf == ROOT / '.data/boards/kicad-interf-u/interf_u.kicad_pcb'
assert len(repair['source_hashes']) == 25
assert p.tree_hash(interf.parent) == repair['source_hashes']
assert p.tree_hash(Path(repair['source']).parent) == repair['source_hashes']
# InstalledContext requires an external source. All arms use these exact original
# bytes, which also equal the separately owned GUI081 repair source; never use a
# runtime-contained GUI project as portfolio source authority.
assert runtime not in interf.parents
assert len(sonde['source_hashes']) == 16
assert Path(sonde['source']) == ROOT / '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb'
assert p.tree_hash(Path(sonde['source']).parent) == sonde['source_hashes']
assert runtime not in Path(sonde['source']).parents
assert p.sha(ROOT / sonde['rights']['ledger']['path']) == sonde['rights']['ledger']['sha256']
for notice in sonde['rights']['notices']:
    path = ROOT / notice['path']
    assert path.stat().st_size == notice['bytes'] and p.sha(path) == notice['sha256']
rights_interf = recovery['repair_source_rights']
assert rights_interf['family'] == 'kicad-interf-exposed' and rights_interf['license'] == 'CC-BY-SA-4.0'
rights_sonde = dict(family='kicad-sonde-xilinx-exposed', license='CC-BY-SA-4.0',
    provenance='Exact unchanged16-file official KiCad Sonde Xilinx source from its frozen042 Native CLI protocol; source commit69cafb907ebc09e7722a2a464b1d466fc2e3608d, original LICENSE.README/CC-BY-SA notices and data/sources.json retained. Different exposed circuit-family label from Interf, same demo publisher; independent pedigree/untouched status not established. No private board or reference route used for selection.')
families = {
    'interf': dict(source=str(interf), source_hashes=repair['source_hashes'],
        source_rights=rights_interf, original_protocol=str(recovery_path),
        original_protocol_sha256=p.sha(recovery_path), GUI_source=repair['source'],
        role='Existing exposed difficult thermal-completion case; no assumed recovery success.'),
    'sonde': dict(source=sonde['source'], source_hashes=sonde['source_hashes'],
        source_rights=rights_sonde, original_protocol=str(sonde_path),
        original_protocol_sha256=p.sha(sonde_path), original_rights=sonde['rights'],
        role='Existing exposed current042 B1 success; all26 inherited warnings/four ignored checks retained, not a predicted gain.')}

prereq_paths = [prepared_path, recovery_path, sonde_path, native_packet,
    ROOT / '.runs/full-integration-187/execution.json',
    ROOT / '.runs/install-distribution-native-015/execution.json',
    ROOT / '.runs/runtime-directory-042/result.json',
    ROOT / '.runs/runtime042-ordinary-whole4Cu-001/execution.json',
    ROOT / '.runs/runtime042-ordinary-partial2Cu-001/execution.json',
    ROOT / '.runs/runtime042-ordinary-sonde-whole-001/execution.json',
    Path(prepared['invalid_required']['receipt']),
    ROOT / 'data/sources.json', ROOT / 'SOURCE_LEDGER.md', args.gui_summary, args.gui_journal]
for path in prereq_paths:
    assert path.is_file() and not path.is_symlink()
for path in prereq_paths[4:7]:
    assert f.read_json(path)['passed'] is True
for path in prereq_paths[7:10]:
    observed = f.read_json(path)
    assert observed['controls_passed'] is True and observed['workflow_delivered'] is True
invalid = prepared['invalid_required']
assert p.sha(Path(invalid['receipt'])) == invalid['receipt_sha256']
assert f.read_json(Path(invalid['receipt']))['passed'] is True
assert p.sha(Path(invalid['child_receipt'])) == invalid['child_sha256']
assert shutil.disk_usage(ROOT).free > 2 * 1024**3, 'Existing minimum only; lead must assess batch headroom'

population = ['B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cthermal']
limits = dict(routing_seconds=420, method_wall_cpu_cap_seconds=450,
    delivery_wall_cpu_cap_seconds=600, export_validation_seconds=120)
defaults = pref.validate(dict(pref.DEFAULTS, seconds=420))
assert defaults == dict(schema=1, scope='whole_board_unlocked_routing', seconds=420,
    adapter='both', profile='standard', guidance='native', layers='source_all', scoring_preference=None)
outputs = {family: {arm: str(runtime / '.runs' /
    (('native7-comparison-' if arm.startswith('B') else 'native7-method-')
        + 'current-' + family + '-' + arm + '-042-001')) for arm in population} for family in families}
all_outputs = [Path(value) for rows in outputs.values() for value in rows.values()]
assert len(set(all_outputs)) == 12 and not any(os.path.lexists(path) for path in all_outputs)
extra_roots = {}
for family in families:
    portfolio = Path(outputs[family]['B2_portfolio'] + '-portfolio')
    extra_roots[family] = [portfolio, *[portfolio.with_name(portfolio.name + '-' + f'{index:02d}-' + variant)
        for index, variant in enumerate(('via_default','via_low','via_high'), 1)]]
    assert not any(os.path.lexists(path) for path in extra_roots[family])
child = runtime / '.runs/qualify-current-method-001.py'
assert not os.path.lexists(child), 'Fresh copied current-method controller required'
# Reuse only fixed portfolio schema, never historical tools, authority or results.
portfolio_template_path = ROOT / '.runs/runtime032-v2-portfolio-negative-002/protocol.json'
portfolio_template = f.read_json(portfolio_template_path)
assert portfolio_template['kind'] == 'installed-native7-comparison-portfolio-functional-v1'
assert portfolio_template['variants'] == ['via_default','via_low','via_high']
assert portfolio_template['routing_seconds'] == 420
assert portfolio_template['installed_trial_accounting_policy'] == 'installed-route-readback-reserve-v1'
assert portfolio_template['comparison_api_policy'] == 'installed-native7-scored-portfolio-api-v2'
assert pv.git_head(ROOT) == expected_head

base.mkdir(); shutil.copyfile(public, child)
assert p.sha(child) == p.sha(public)
parent = dict(schema=1, kind='frozen-two-family-six-arm-current-installed-exposed-development-v1',
    population=population, planned_family_order=list(families),
    planned_arm_order=['Cdefault','B0','B1','B2single_tuned','B2_portfolio','Cthermal'],
    outputs=outputs, runtime=str(runtime), runtime_manifest_sha256=manifest_pin,
    source_head=source_head, administration_head=expected_head, families=families,
    completed_GUI081=completed_gui,
    default_settings=defaults, limits=limits, freezer_sha256=p.sha(Path(__file__)),
    tracked_administration_files_sha256=tracked, enclosure_sha256=p.sha(enclosure),
    historical_portfolio_schema_template_sha256=p.sha(portfolio_template_path),
    policy='Corrected-standard/B1 remains default. Cdefault is the same algorithm through actual Workflow/CLI. Optional fixed thermal CLI is separate. B2single_tuned and fixed ordered three-score portfolio are separate; fixed valid(vias,length,index) selection, no board-specific tuning or policy changes during the batch.',
    eligibility='Two already exposed circuit-family labels; Sonde shares the KiCad demo publisher with Interf. No independent pedigree, unrelated-family confirmation, holdout or30-50-family population claim. All twelve arms and failures are prospectively retained.',
    stock_caveat='B0 uses identical native/task DSN and stock adapter with common fixed-placement/fidelity/Native safeguards; not untouched official vanilla-plugin qualification. API baselines/library delivery and actual default/recovery CLI startup differ and remain explicit.',
    negative_contract='Cdefault uses explicit standard completed-negative reader; B0/B1/B2 require live sealed Context. Cthermal without qualified final Native evidence is method_not_delivered, not a fabricated routing failure. Stale, cancelled, unsupported or over-budget evidence never authorizes acceptance.',
    accounting='Equal420allocation/450method/600completewall+fullCPU/export120; recovery420 covers the whole method, not420engine seconds. Portfolio420 includes all attempts/selection/readbacks with30inside each trial and15root reserve; no extra uncharged reserve. External complete exit includes imports/startup/conversion/attempts/selection/allvalidation/render/choice/export/readbacks/publication. Preparation/authoring/research/review/curation separate; nested costs not added twice. Unknown interactive CPU is notzero.',
    GUI_checkpoint_gate='Lead must supply exact final current081 functional summary+journal hashes and an audited stable post-GUI administration HEAD. Partial/unfrozen journals refuse; a GitSHA alone does not establish graphical qualification.',
    no_prior_Native_repeated_by_freezer=True, Native_executed=False, actual_GUI=False,
    not_confirmatory=True, project_complete=False, preparation_wall_before_publication=time.monotonic()-START,
    preparation_full_CPU_before_publication=cpu()-CPU0)
p.save_json(base / 'population.json', parent)
parent_pin = p.sha(base / 'population.json')
prereqs = {str(path): p.sha(path) for path in [*prereq_paths, base / 'population.json']}
assert len(prereqs) <= 32
common = dict(schema=1, runtime=str(runtime), runtime_manifest_sha256=manifest_pin,
    source_head=source_head, tools=tools, whole_wall_full_cpu_seconds=600,
    pass_key='controls_passed', administration_root=str(ROOT), enclosure_sha256=p.sha(enclosure))
children = {}
for family, entry in families.items():
    folder = base / family; folder.mkdir(); children[family] = {}
    for arm in population:
        arm_folder = folder / arm; arm_folder.mkdir()
        source_common = dict(common, source=entry['source'], source_hashes=entry['source_hashes'])
        if arm == 'B2_portfolio':
            plan = copy.deepcopy(portfolio_template)
            plan.update(source_common, **limits, variants=['via_default','via_low','via_high'],
                allocation='balanced', trial_readback_reserve_seconds=30,
                root_finalization_reserve_seconds=15,
                installed_trial_accounting_policy='installed-route-readback-reserve-v1',
                comparison_api_policy='installed-native7-scored-portfolio-api-v2', administration_head=expected_head,
                administration_files_sha256=admin, family=entry['source_rights']['family'],
                source_rights=entry['source_rights'], controller=str(ROOT / admin_names[0]),
                controller_sha256=admin[admin_names[0]], controller_args=['--runtime',str(runtime)],
                output=outputs[family][arm], portfolio_output=str(extra_roots[family][0]),
                material_roots=[str(path) for path in extra_roots[family]],
                scope='Frozen042 ' + family + ' B2 fixed-three-score API portfolio; same420/450/600/export120, all attempts/costs/failures retained, valid winner delivery only; no ordinary admission/GUI/general superiority claim.')
            plan.pop('prior_failed_protocol_sha256', None)
        else:
            hashes = entry['source_hashes']; rights = entry['source_rights']
            plan = dict(source_common, kind='installed-native7-current-method-v1', arm=arm,
                population=population, outputs=outputs[family], output=outputs[family][arm],
                controller=str(child), controller_sha256=p.sha(child), controller_args=['--runtime',str(runtime)],
                source_inventory_sha256=hashlib.sha256((json.dumps(hashes,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest(),
                source_rights=rights, source_rights_sha256=hashlib.sha256(f.canonical(rights).encode()).hexdigest(),
                qualifier_sha256=p.sha(qualifier), prerequisite_sha256=prereqs,
                default_settings=defaults, limits=limits,
                scope='Frozen042 ' + family + ' ' + arm + ' six-arm member: identical original constraints/source and420/450/600/export120. API baseline or actual default/recoverCLI distinction retained. All startup/attempt/selection/Native/readback/delivery costs counted; no holdout/GUI/general/electrical claim.')
        plan.update(population_protocol_path=str(base / 'population.json'), population_protocol_sha256=parent_pin)
        p.save_json(arm_folder / 'protocol.json', plan)
        children[family][arm] = dict(path=str(arm_folder / 'protocol.json'), sha256=p.sha(arm_folder / 'protocol.json'))
assert pv.git_head(ROOT) == expected_head
assert p.tree_hash(interf.parent) == repair['source_hashes']
assert p.tree_hash(Path(repair['source']).parent) == repair['source_hashes']
assert p.tree_hash(Path(sonde['source']).parent) == sonde['source_hashes']
assert p.sha(args.gui_summary) == args.gui_summary_sha256
assert p.sha(args.gui_journal) == args.gui_journal_sha256
p.save_json(base / 'frozen-children.json', dict(schema=1, population_path=str(base / 'population.json'),
    population_sha256=parent_pin, protocols=children, administration_head=expected_head,
    policy_or_board_changes_after_first_arm=False, project_complete=False,
    preparation_wall_before_last_publication=time.monotonic()-START,
    preparation_full_CPU_before_last_publication=cpu()-CPU0))
print(json.dumps(dict(frozen=True, base=str(base), population_sha256=parent_pin,
    protocols=children, administration_head=expected_head)))
