"""Runtime074 stored Native prerequisite replay for prospective v7 comparisons.

Reuses the completed Native13/invalid/class/live-warning/finite-GUI105 evidence.
Never launches Native, installs a runtime or grants full GUI/electrical approval.
Exact reviewed current source is required; old population gates remain closed.
"""
from pathlib import Path
RECORDED_NATIVE_PREREQUISITES_FILLED=True
ACTUAL_CLASS_COMPLETED_TRIALS=1
ACTUAL_GUI_CLOSURE_PATH='.runs/runtime074-gui105-actual-001/closure.json'
ACTUAL_GUI_CLOSURE_SHA256='aa6a1b8fdb861123cb0fb7036e7239b46a32f7701df75e43efbae08347f38638'
ACTUAL_GUI_CLOSURE_SCHEMA={'schema': 1,
 'kind': 'runtime074-GUI105-finite-core-closure-v1',
 'jobs': {'selected': 'autorouter-gui-d2e389d195c04233addabae33a455663',
          'ordinary-reject': 'autorouter-gui-523ef75766c449459d47115c665e35ad',
          'four-copper': 'autorouter-gui-3c1710bdf8574f95bfb26bcb11c841f7',
          'parent-class': 'autorouter-gui-e28f59dfc15744c49d56c9b9d4521324',
          'cancel-unsupported-tuned-preset': 'autorouter-gui-22a919f091bd437c9a847299b7ed014f',
          'cancel-observer-missed-uncancelled-route': 'autorouter-gui-2b02eb8c2fd3499fb72c6099ac3b15e5',
          'active-cancel': 'autorouter-gui-1c8af7bab691496495c57032c9380c68',
          'stale-source': 'autorouter-gui-2214d5ee4df341ab8bf963e6ba0f8d32'},
 'finite_controls': ['isolated_exact_project',
                     'actual_toolbar_single_worker',
                     'preset_save_load',
                     'missing_source_ack_refusal',
                     'zero_budget_refusal',
                     'selected_protected_route',
                     'ordinary_protected_route',
                     'four_layer_protected_route',
                     'class_Improve_protected_route',
                     'readable_findings',
                     'Edge_rendered_layers',
                     'explicit_reject_no_export',
                     'missing_review_ack_refusal',
                     'open_review_project_refusal_preserves_route',
                     'explicit_accept_intent',
                     'fresh_native_export',
                     'shared_readback',
                     'checked_project_and_PCB_opened',
                     'post_editor_export_stale_refusal',
                     'changed_settings_revoke_controls',
                     'active_Java_cancel_cleanup_no_downstream',
                     'changed_source_refusal_before_CLI'],
 'unexercised': ['genuine-live-updated-warning-dialog; no actual variation',
                 'exact-worker-return-to-queued-open-callback fault interval'],
 'supporting_sha256': {'start.json': '3fdc8e34da1b4fa1d0a9a5cb4689314c74027d4f4a3728bd5fba6795866541c6',
                       'selected-pristine-delivery.json': 'c91556deb84a498be5fc91970b292a98307e056f5c5524d56e4d03163da3d0d6',
                       'four-pristine-delivery.json': 'e55dc8306c2df896c32c1992a95b01f5b0a45beddeb14c9d126c945c3f3fdee3',
                       'class-pristine-delivery.json': 'c61343ef1e7080e18b7cbcc72b8c23328361c089258adfc0a1df0e3af75e8d58',
                       'active-cancel-closure.json': '44463a11a95f56dce6464ae956ee8c4a47c98eb33d436cdc47a7963ebdad35c8',
                       'cancel-active-observation-corrected.json': 'b0f7cfe0923c54f6bf7f71968f3072ddf9d41bb19e4127ab99e74c2e69155576',
                       'stale-source-fault.json': 'c630931f78cc743aebeec9e438ec54484f1e988460340c7b2a61498142b9d65f',
                       'additional-control-source-preparation.json': '4aa16f2925c36d4fe33113430c9f47172b1e215860ee8fdb1e1fb2e78fbe8f38',
                       'cancel-observer-diagnosis-complete.json': '2afcc0f73650dacd7106bb2a98dbc7b6ec7daaa645fd9dd44ae878be198bd137',
                       'selected-skeptical-review.json': 'c836b7fd2062564596c351bdb25e3c01e9998478950c1e188a6215849e82eb1d',
                       'reporter-fix-skeptical-review.json': 'd6fcdc96b06754559839c1addabf104c3c5c09927f31303f1a78f4b3c458b8a0',
                       'closure-skeptical-review.json': 'b3e5161a39ea59b43486a16a008165d90e34fca723c20b4aca76dc1d7fc296ea'}}
assert RECORDED_NATIVE_PREREQUISITES_FILLED is True, 'Actual074 Native13/invalid/class/public facts and finite GUI closure are required'
import hashlib,os,re
ROOT=Path(__file__).resolve().parents[1]
from autorouter import floor_route as f,preferences as pref,provenance as pv,placement_clearance as io
SHARED_HELPER_PATH=ROOT/'scripts/freeze_current_comparison.py'

# Verify exact owned source before importing, then bind its actual canonical
# module path before exposing any shared callable or population constants.
def _check_shared_helper_source():
    # A committed-source guard avoids a circular module/freezer digest pair.
    # Both exact files must match the same actual HEAD before helper import and
    # at final replay; the freezer also freezes their byte pins for each job.
    module=Path(__file__).absolute()
    require_paths=(SHARED_HELPER_PATH,module)
    head=pv._git(ROOT,'rev-parse','HEAD').decode().strip()
    if not pv._HEAD.fullmatch(head):raise ValueError('reviewed source HEAD required')
    pins={}
    for path in require_paths:
        if (path.resolve(strict=True)!=path or not path.is_file()
                or any(p.is_symlink() for p in (path,*path.parents))
                or not 0<path.stat().st_size<=2*1024**2):
            raise ValueError('canonical bounded committed qualification source required')
        relative=path.relative_to(ROOT).as_posix()
        data=path.read_bytes()
        if pv._git(ROOT,'show',head+':'+relative)!=data:
            raise ValueError('qualification/helper source differs from committed HEAD: '+relative)
        pins[relative]=hashlib.sha256(data).hexdigest()
    identity=dict(head=head,files=pins)
    if globals().get('SOURCE_IDENTITY',identity)!=identity:
        raise ValueError('qualification sources or HEAD changed during replay')
    return identity

SOURCE_IDENTITY=_check_shared_helper_source()
SHARED_HELPER_SHA256=SOURCE_IDENTITY['files']['scripts/freeze_current_comparison.py']
from scripts import freeze_current_comparison as _shared_metadata
assert Path(_shared_metadata.__file__).absolute()==SHARED_HELPER_PATH
assert Path(_shared_metadata.__file__).resolve(strict=True)==SHARED_HELPER_PATH
_check_shared_helper_source()
require=_shared_metadata.require
pinned_json=_shared_metadata.pinned_json
current40_reserve=_shared_metadata.current40_reserve
installed_root_binding=_shared_metadata.installed_root_binding
NATIVE_CASES=_shared_metadata.NATIVE_CASES
HIGH_CASES=_shared_metadata.HIGH_CASES
FAMILY_CLASS_VERSION='improve-v7-family-classes'
CHOICE60_METHOD_KIND='installed-native7-current-method-v5-review60-choice60'
HEAD='6fbbbf22dfb8250f1578fb4d7a45ff0e161b3194'
MANIFEST='584ee929eaf3d277dc535556e42c71ac5196a74f1c5e3fd53a2cce5a67853d61'
REPORTER_SHA='04ba7973534ecd57c7ed5ab79517c3bdf322cbc43a426dd7b990a5131744ff17'
FIXED_JSON_SHA256={
    ".runs/runtime074-installed-native-qualification-001/frozen.json": "7cf96a66ec7913fa53e52cf406c0e654ffad6ca0707284b8096907c384dee1fe",
    ".runs/runtime074-installed-native-qualification-001/batch-result.json": "e0945979f3172569a92acae38413fa1d7bebcabe3a7fd891af0afd3a61747040",
    ".runs/runtime074-native-controls-001/invalid/protocol.json": "a8a1e4aa70377e0a9ca70d1406ed80073323d1d96b7d256649c2d8fcd2bafeeb",
    ".runs/runtime074-native-controls-001/invalid/enclosure/result.json": "c4d77128cfa884c06d2bef040f42337b3e84d879f30108e40bd5f0db946f5423",
    ".runs/improve-parent-class-runtime074-native-qualification-001/protocol.json": "ad75ac1b3ce275186b8b7f0bbdc17e58d3ebc60c49b51fbc3d7bdc352315b3c4",
    ".runs/improve-parent-class-runtime074-native-qualification-001/positive/execution.json": "913c9599d96ca0ce027ab3776fe3f6e9cfd5976469186df216fb974111847cf2",
    ".runs/runtime074 fresh install 001/.runs/native7-comparison-parent-class-qualification-001/result.json": "ceaa37e0fa950eb37ed0dd536ed2fd4279de68377fcaee7a859d5461130b5708",
    "evidence/runtime074-installed-native-milestone-001.json": "be885c250b1236b928a1fcb3c99d2e3568584bb6a1433f9df7bb3c95e1b5769a",
    ".runs/improve-parent-class-runtime074-native-qualification-001/enclosure/result.json": "907efd05964a4aac5611e333f3e7841e9108529127b63a54566c7722510bd6c7",
    ".runs/full-integration-241/protocol.json": "697c71067155fbd0e0d13990f5dbc4683093da8ddf401c19021a90a148326909",
    ".runs/full-integration-241/execution.json": "e2c65e433b95b84dae850228c3363b689e74c1f3d92f2b7c85acec75a949ae9d",
    ".runs/runtime074-warning-native-controls-continuation-001/protocol.json": "885ceeb69e41bf6ef58b85a6eb9c06fb5b1a32469479e9def9b2a5d6d2343c92",
    ".runs/runtime074-warning-native-controls-continuation-001/enclosure/result.json": "ba4ed3393a5e6fcaef79c4d749755cc9417f9ebf4fa25dddb30160fcbc4f2175",
    ".runs/runtime074 fresh install 001/.runs/native7-comparison-live-warning074-continuation-001/result.json": "7bc4f7b77fe2c20ab9dafb5c4b1306437aab8623200b970f4bb2ba94de530836",
    "evidence/runtime074-warning-native-controls-001.json": "f4aefa2775d11203d09a70b764431c13da33d5a49acbacdf328cd36f54926c1e"
}
ADDITIONAL_PREREQUISITE_SHA256={str(ROOT/'.runs/runtime-directory-074/build.log'): '0d1bbfa059348c1c6f0bd57ae14a322cb983770d7f0b2166b64549657a7432c5'}

def installed_scope_contract(version):
    require(version==FAMILY_CLASS_VERSION, 'only prospective v7/runtime074 prerequisite contract allowed')
    require(type(REPORTER_SHA) is str and pv._DIGEST.fullmatch(REPORTER_SHA), 'reviewed v7 reporter source is not yet pinned')
    require(all(type(pin) is str and pv._DIGEST.fullmatch(pin) for pin in FIXED_JSON_SHA256.values()),
        'actual new Native/control/public proof pins required; no old substitute')
    require(type(ACTUAL_CLASS_COMPLETED_TRIALS) is int and ACTUAL_CLASS_COMPLETED_TRIALS>=1,
        'actual completed class trial count required; no historical count transfer')
    require(type(ACTUAL_GUI_CLOSURE_PATH) is str and not Path(ACTUAL_GUI_CLOSURE_PATH).is_absolute()
        and '..' not in Path(ACTUAL_GUI_CLOSURE_PATH).parts
        and type(ACTUAL_GUI_CLOSURE_SHA256) is str and pv._DIGEST.fullmatch(ACTUAL_GUI_CLOSURE_SHA256)
        and type(ACTUAL_GUI_CLOSURE_SCHEMA) is dict,
        'actual074 finite GUI closure path and pin required')
    return ('074','241',HEAD,MANIFEST,FIXED_JSON_SHA256,REPORTER_SHA,
        'runtime074-fresh-installed-review60-choice60-native-CLI-only-v1')

def required_actual_gui_closure(runtime,manifest_pin,report,bound,dependencies):
    """Bind only the exact observed105 finite core; no GUI replay/admission."""
    from autorouter import review_export as ex, handoff as h
    path=pv.canonical(ROOT/ACTUAL_GUI_CLOSURE_PATH)
    require(path.is_relative_to(ROOT), 'actual GUI closure escaped project')
    gui=bound(path,ACTUAL_GUI_CLOSURE_SHA256);shape=ACTUAL_GUI_CLOSURE_SCHEMA
    require(gui.get('schema')==shape['schema'] and type(gui['schema']) is int
        and gui.get('kind')==shape['kind'] and gui.get('runtime')==str(runtime)
        and gui.get('source_head')==HEAD and gui.get('runtime_manifest_sha256')==manifest_pin==MANIFEST
        and gui.get('finite_core_controls_passed') is True and gui.get('actual_GUI_observed') is True
        and gui.get('full_GUI_qualified') is False and gui.get('closed_observed_worker') is True
        and gui.get('software_test_intent_not_human_PCB_approval') is True
        and gui.get('unexercised')==shape['unexercised'], 'actual105 finite/limited identity differs')
    session=runtime/'.runs/gui-session105';jobs=session/'jobs'
    prepared=bound(session/'prepared-state.json',gui['prepared_state_sha256'])
    require(gui['observations']==str(path.parent/'observations.json'), 'actual105 observation path differs')
    obs=bound(pv.canonical(Path(gui['observations'])),gui['observations_sha256'])
    require(gui['prepared_state']==str(session/'prepared-state.json')
        and prepared['runtime']==str(runtime) and prepared['source_head']==HEAD
        and prepared['runtime_manifest_sha256']==manifest_pin and prepared['actual_GUI'] is False
        and obs.get('schema')==1 and type(obs['schema']) is int
        and obs.get('kind')=='runtime074-GUI105-lead-observations-v1'
        and obs.get('runtime')==str(runtime) and obs.get('source_head')==HEAD
        and obs.get('manifest_sha256')==manifest_pin and obs.get('actual_GUI_observed') is True
        and obs.get('full_GUI_qualified') is False and obs.get('unexercised')==shape['unexercised']
        and obs.get('human_PCB_approval') is False and obs.get('software_test_intent_only') is True
        and obs.get('GUI_worker51597_closed') is True
        and obs.get('original_sources_and_runtime54_unchanged') is True
        and set(obs['finite_core_controls'])==set(shape['finite_controls'])
        and all(value is True for value in obs['finite_core_controls'].values()), 'actual105 observations differ')
    support={name:bound(path.parent/name,pin) for name,pin in shape['supporting_sha256'].items()}
    review=support['closure-skeptical-review.json']
    require(review.get('schema')==1 and type(review['schema']) is int
        and review.get('kind')=='runtime074-GUI105-finite-core-independent-closure-review-v1'
        and review.get('closure_sha256')==ACTUAL_GUI_CLOSURE_SHA256
        and review.get('observations_sha256')==gui['observations_sha256']
        and review.get('blocking_findings')==[] and review.get('full_GUI_qualified') is False
        and review.get('unexercised')==shape['unexercised'], 'actual105 skeptical review differs')
    start=support['start.json']
    require(start['runtime']==str(runtime) and start['manifest_sha256']==manifest_pin
        and start['runtime54_unchanged'] is True and start['Edge_only'] is True
        and start['manager_pid']==95117 and start['GUI_worker_pid']==51597
        and start['GUI_worker_parent']==95117 and start['toolbar_click_count']==1
        and start['exact_manager_cwd']==str(session/'inspection')
        and start['jobs_initially_empty'] is True, 'actual105 toolbar/process witness differs')
    require(set(gui['source_checks'])==set(prepared['roles']), 'actual105 original role census differs')
    for name,role in prepared['roles'].items():
        source=pv.canonical(Path(role['source']));check=gui['source_checks'][name]
        require(check['source']==str(source) and check['hashes']==role['source_hashes']==io.inventory(source.parent)
            and check['preset_sha256']==role['settings_sha256']==report.digest(Path(role['settings']))
            and report.read(Path(role['settings']))==role['settings_content'], 'actual105 pristine source/preset changed')
    expected=shape['jobs'];rows=gui['jobs']
    require(type(gui['job_count']) is int and gui['job_count']==len(rows)==8
        and [row['role'] for row in rows]==list(expected), 'actual105 eight-job outcome census differs')
    require(review['eight_job_census']==[dict(role=row['role'],job=expected[row['role']],
        route_status=row.get('route_status'),choice=row.get('choice'),
        current_export_admitted=row.get('current_export_admitted'),stored_processes=len(row['processes']))
        for row in rows], 'actual105 skeptical/lead outcome census differs')
    actual=set()
    for entry in jobs.iterdir():
        require(not entry.is_symlink() and entry.is_dir() and pv.canonical(entry).parent==jobs,
            'unexpected linked/non-directory actual105 job')
        actual.add(entry.name)
    require(actual==set(expected.values()), 'actual105 extra/missing job')
    by_role={};total_wall=0.0
    for row in rows:
        role=row['role'];job=pv.canonical(Path(row['job']))
        require(job==jobs/expected[role] and report.inventory(job)==row['inventory']
            and report.read(job/'settings.json')==row['settings'], 'actual105 closed job material/settings changed')
        process_names={name for name in row['inventory'] if '/' not in name and name.endswith('.command.process.json')}
        require(process_names==set(row['processes']), 'actual105 process census differs')
        for name,process in row['processes'].items():
            log=job/name.replace('.process.json','.log')
            require(report.read(job/name)==process and log.stat().st_size==process['log_bytes']
                and type(process['exit_code']) is int and process['log_truncated'] is False
                and type(process['cancel_requested']) is bool
                and process['argv'][:4]==[str(runtime/'.venv/bin/python'),'-B','-m','autorouter']
                and type(process['wall_seconds']) in (int,float) and 0<=process['wall_seconds']<=1000,
                'actual105 process/log custody differs')
            total_wall+=process['wall_seconds']
        by_role[role]=(job,row)
    require(abs(total_wall-obs['CLI_process_wall_sum_seconds'])<1e-6
        and type(obs['compute_limit']) is str and bool(obs['compute_limit'])
        and len(obs['failed_or_limited_attempts'])==3, 'actual105 costs or failed attempts omitted')
    role_names={'selected':'selected','ordinary-reject':'ordinary','four-copper':'four-copper','parent-class':'parent-class'}
    for role,(job,row) in by_role.items():
        if 'stored_own_final' not in row:continue
        data=report.read(job/'route/result.json');source=pv.canonical(Path(data['source']))
        if role in role_names:
            original=prepared['roles'][role_names[role]]
            require(source==Path(original['source']) and row['settings']==original['settings_content'],
                'actual105 positive source/settings differ')
        plan=dict(source=str(source),source_hashes=data['source_hashes'],tools=data['tools'],
            source_head=HEAD,runtime_manifest_sha256=manifest_pin,runtime=str(runtime))
        require(data['accepted'] is True and data['status']==row['route_status']=='routing_accepted'
            and row['route_accepted'] is True
            and report.own_final(job/'route/result.json',export=False,plan=plan,allowed=[job],accepted=True)==row['stored_own_final'],
            'actual105 original positive own-final differs')
        if role=='cancel-observer-missed-uncancelled-route':
            require(row['processes']['route.command.process.json']['cancel_requested'] is False
                and not any((job/name).exists() for name in ('review','choice','export')),
                'missed105 cancellation was promoted or gained downstream work')
            continue
        review=report.read(job/'review/review.json');choice=report.read(job/'choice/choice.json')
        h.check_stage_budget(review,'review');h.check_stage_budget(choice,'choice')
        require(review['receipt']==choice['receipt']==str(job/'route/result.json')
            and review['receipt_sha256']==choice['receipt_sha256']==report.digest(job/'route/result.json')
            and choice['review_sha256']==report.digest(job/'review/review.json')
            and choice['choice']==row['choice'] and choice['choice_recorded'] is True
            and choice['applied'] is False and choice['human_pcb_approval_observed'] is False,
            'actual105 review/intent bridge differs')
        report.preview_material(job/'review',review['preview'])
        if role=='ordinary-reject':
            require(choice['choice']=='reject' and not (job/'export').exists()
                and row['stored_own_final']['protected_count']==4, 'actual105 reject/export/protection differs')
            continue
        exported=report.read(job/'export/export.json')
        require(choice['choice']=='accept' and exported['export_accepted'] is True
            and row['export_accepted_recorded'] is True and row['warning_challenge_observed'] is False
            and 'warning_review_acknowledgement' not in exported and not (job/'export/warning-review.json').exists()
            and exported['candidate_sha256']==data['candidate_sha256']==row['candidate_sha256']
            and exported['inputs']['choice_sha256']==report.digest(job/'choice/choice.json'),
            'actual105 accepted/export/no-warning lineage differs')
        report.own_final(job/'export/export.json',export=True,plan=plan,allowed=[job],accepted=True)
        ex.bound_material(exported['inputs'])
        pristine=support[{'selected':'selected','four-copper':'four','parent-class':'class'}[role]+'-pristine-delivery.json']
        require(pristine['job']==str(job) and pristine['role']==role
            and pristine['shared_reader_result']==row['original_GUI_shared_readback']
            and report.read(job/'verify_export.command.log')==pristine['shared_reader_result']
            and pristine['shared_reader_result']['current'] is True
            and pristine['shared_reader_result']['candidate_sha256']==data['candidate_sha256'],
            'actual105 pristine shared readback differs')
        if role=='selected':
            changed={name for name,pin in pristine['job_inventory'].items() if row['inventory'].get(name)!=pin}
            require(row['current_export_admitted'] is False and pristine['before_actual_KiCad_open'] is True
                and changed=={'export/validation/candidate/Stm32.kicad_pro','export/validation/candidate/Stm32.kicad_prl'}
                and 'export/validation/candidate/Stm32-backups/Stm32-2026-11-04_142424.zip' in row['inventory']
                and report.read(job/'inspect-export-57c2cd7167b74a8e88268b873ce23b74.command.log')['current'] is True
                and report.read(job/'inspect-export-352476fd677442748a10bed6c5936d98.command.log')==dict(current=False,reason='export inputs/runtime/evidence changed')
                and row['processes']['inspect-export-352476fd677442748a10bed6c5936d98.command.process.json']['exit_code']==2
                and ex.evidence(job/'export')!=exported['export_evidence']
                and row['stored_own_final']['protected_count']==274,
                'actual105 selected pristine/stale chronology differs')
        else:
            require(row['current_export_admitted'] is True and ex.evidence(job/'export')==exported['export_evidence'],
                'actual105 four/class current export material differs')
            if role=='four-copper':require(row['stored_own_final']['protected_count']==10,'actual105 four protection differs')
            else:
                require(type(data.get('protected_routes')) is int and data['protected_routes']==1
                    and data.get('strategy')=='native_validated_zone_net_pruning', 'actual105 Improve protection differs')
                plan.update(kind=CHOICE60_METHOD_KIND,improve_parent_class_policy='native-parent-dimensions-v1')
                require(report.improve_auxiliary(job/'route',data,plan)['protected_count']==1
                    and report.improve_auxiliary(job/'export/validation',exported,plan,export=True)['protected_count']==1,
                    'actual105 checked Improve dimensions/protection differ')
    extra=support['additional-control-source-preparation.json']['roles']
    require(io.inventory(Path(extra['cancel']['source']).parent)==extra['cancel']['source_hashes'],
        'actual105 cancellation source changed')
    job,row=by_role['cancel-unsupported-tuned-preset']
    unsupported=report.read(job/'preview.command.log')
    require(set(row['processes'])=={'preview.command.process.json'}
        and row['settings']['profile']=='tuned' and row['processes']['preview.command.process.json']['exit_code']==2
        and unsupported['status']=='rejected' and unsupported['reason'].startswith('unsupported:')
        and not (job/'route').exists(), 'actual105 unsupported preset outcome differs')
    job,row=by_role['active-cancel'];cancel=support['active-cancel-closure.json'];live=support['cancel-active-observation-corrected.json']
    data=report.read(job/'route/result.json');engine=[step for step in data['steps'] if step.get('name')=='engine']
    require(cancel['job']==live['job']==str(job) and live['active_observed'] is True
        and live['observation']['engine']['pid']==54241 and live['observation']['engine']['ppid']==live['observation']['CLI']['pid']
        and data['status']=='cancelled' and data['accepted'] is False
        and row['processes']['route.command.process.json']==cancel['CLI_process']
        and cancel['CLI_process']['cancel_requested'] is True and cancel['CLI_process']['exit_code']==2
        and len(engine)==1 and engine[0]['pid']==54241 and engine[0]['exit_code']==-9 and engine[0]['cleanup_complete'] is True
        and cancel['observed_group_remaining']==[] and all(value is False for value in cancel['downstream'].values())
        and not any((job/name).exists() for name in ('review','choice','export')), 'actual105 active cancellation differs')
    job,row=by_role['stale-source'];fault=support['stale-source-fault.json'];preview=report.read(job/'preview.command.log')
    current=dict(extra['stale-source']['source_hashes']);current[Path(fault['fault_copy']).name]=fault['after']
    require(fault['fault_copy']==extra['stale-source']['source'] and fault['before']!=fault['after']
        and fault['original_prepared_source_unchanged'] is True and preview['source_sha256']==fault['before']
        and io.inventory(Path(fault['fault_copy']).parent)==current
        and set(row['processes'])=={'preview.command.process.json'} and not (job/'route').exists(),
        'actual105 changed-source refusal chronology differs')
    return dict(path=str(path),sha256=ACTUAL_GUI_CLOSURE_SHA256,finite_core_controls_passed=True,
        actual_GUI_observed=True,full_GUI_qualified=False,job_count=8,unexercised=shape['unexercised'],
        skeptical_review_sha256=shape['supporting_sha256']['closure-skeptical-review.json'],
        selected_export_current=False,CLI_process_wall_sum_seconds=total_wall,compute_limit=obs['compute_limit'],
        scope=gui['large_CLI_only_prerequisite_scope'])

def required_actual_live_controls(runtime,manifest_pin,report,fixed):
    """Bind the completed current six-role continuation; no Native/GUI replay."""
    prefix='.runs/runtime074-warning-native-controls-continuation-001/'
    plan=fixed[prefix+'protocol.json'];outer=fixed[prefix+'enclosure/result.json']
    child=fixed['.runs/runtime074 fresh install 001/.runs/native7-comparison-live-warning074-continuation-001/result.json']
    public=fixed['evidence/runtime074-warning-native-controls-001.json']
    expected=['accept','reject','expire','cancel','stale-export','wrong-nonce']
    require(plan['runtime']==str(runtime) and plan['source_head']==HEAD and plan['runtime_manifest_sha256']==manifest_pin
        and plan['roles']==expected and plan['whole_wall_full_cpu_seconds']==424
        and outer['passed'] is True and outer['status']=='completed'
        and outer['process']['status']=='success' and outer['process']['exit_code']==0
        and outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False
        and max(outer['complete_wall_seconds'],outer['complete_full_CPU_seconds'])<=424
        and outer['protocol_sha256']==FIXED_JSON_SHA256[prefix+'protocol.json']
        and outer['child_sha256']==FIXED_JSON_SHA256['.runs/runtime074 fresh install 001/.runs/native7-comparison-live-warning074-continuation-001/result.json'],
        'actual074 live Native continuation binding differs')
    require(child['passed'] is True and child['controls_passed'] is True and child['all_roles_exercised'] is True
        and child['accepted'] is False and child['production_admitted'] is False
        and [row['role'] for row in child['rows']]==expected
        and all(row['passed'] is True and row['challenge_count']==1 and row['genuine_challenge_observed'] is True for row in child['rows'])
        and [row['export_accepted'] for row in child['rows']]==[True,False,False,False,False,False]
        and report.inventory(Path(child['ordinary_job_root']))==child['ordinary_evidence']
        and public['source_build']==HEAD and public['runtime_manifest_sha256']==manifest_pin
        and public['passed'] is True and public['all_six_real_challenges_observed'] is True
        and public['enclosure_sha256']==FIXED_JSON_SHA256[prefix+'enclosure/result.json']
        and public['aggregate_sha256']==outer['child_sha256'] and public['actual_GUI_qualified'] is False,
        'actual074 six-role Native/raw material/public facts differ')
    require(max(plan['prior_complete_wall_seconds']+outer['complete_wall_seconds'],
                plan['prior_complete_CPU_seconds']+outer['complete_full_CPU_seconds'])<=450,
        'failed first harness and continuation active cost exceed original450 allocation')
    return dict(roles=expected,headless_only=True,original_failure_retained=True,GUI_qualified=False)

def installed074_cohort_scope(qualified, runtime, manifest_pin, identity, manifest, version):
    """Replay one exact versioned installed13 lineage, never Native.

    An additional runtime/cohort needs its own reviewed adapter. The old
    seven/eleven+IR and042/050 contracts are deliberately not broadened.
    """
    _check_shared_helper_source()
    assert Path(_shared_metadata.__file__).absolute()==SHARED_HELPER_PATH
    assert Path(_shared_metadata.__file__).resolve(strict=True)==SHARED_HELPER_PATH
    from scripts import report_current_comparison as report
    from autorouter import local_settings
    series,full_number,head,expected_manifest,fixed_pins,reporter_pin,qualification_kind = installed_scope_contract(version)
    class_mode = version == FAMILY_CLASS_VERSION
    base = ROOT/('.runs/runtime'+series+'-installed-native-qualification-001')
    original = ROOT/('.runs/runtime-directory-'+series+'/runtime')
    invalid_prefix = '.runs/runtime'+series+'-native-controls-001/invalid'
    full_base = ROOT/('.runs/full-integration-'+full_number)
    require(runtime == ROOT/('.runs/runtime'+series+' fresh install 001')
        and identity.get('git_head') == head and identity.get('native_version') == '10.0.7'
        and manifest_pin == expected_manifest, 'exact installed'+series+' source/root/manifest required')
    dependencies = {}
    def bound(path, pin):
        path = pv.canonical(Path(path)); value = pinned_json(path,pin)[1]
        dependencies[str(path)] = pin
        return value
    fixed = {name:bound(ROOT/name,pin) for name,pin in fixed_pins.items()}
    frozen = fixed[str((base/'frozen.json').relative_to(ROOT))]
    batch = fixed[str((base/'batch-result.json').relative_to(ROOT))]
    invalid_plan = fixed[invalid_prefix+'/protocol.json']
    invalid = fixed[invalid_prefix+'/enclosure/result.json']
    require(qualified == frozen and frozen.get('runtime') == str(runtime)
        and frozen.get('source_head') == identity['git_head'] and frozen.get('runtime_manifest_sha256') == manifest_pin
        and frozen.get('source_runtime') == str(original) and frozen.get('installation_record_is_authoritative') is False
        and batch.get('passed') is True and batch.get('completed_cases') == 13 and batch.get('unstarted_cases') == 0
        and batch.get('frozen_sha256') == fixed_pins[str((base/'frozen.json').relative_to(ROOT))]
        and batch.get('full_CPU_complete') is True
        and all(type(batch.get(key)) in (int,float) and 0 <= batch[key] <= 900
                for key in ('wall_seconds','full_CPU_seconds')), 'exact completed installed13 cohort required')
    report_source = ROOT/'scripts/report_current_comparison.py'
    require(Path(report.__file__).resolve() == report_source
        and pv.file_digest(report_source)[0] == reporter_pin,
        'exact reviewed current40 stored-evidence helper required')
    pins = dict(frozen['prerequisite_sha256']);pins.update(ADDITIONAL_PREREQUISITE_SHA256)
    for path,pin in {
        ROOT/'.runs/runtime074-qualification-port-001/freeze.py':frozen['controller_sha256'],
        ROOT/'.runs/enclose-runtime044-workflow-001.py':frozen['enclosure_sha256'],
        ROOT/'scripts/qualify_runtime_workflow.py':frozen['driver_sha256'],
        Path(invalid_plan['controller']):invalid_plan['controller_sha256']}.items():
        require(pv.file_digest(path)[0] == pin, 'recorded Native controller/driver changed')
    def prior(path):
        return bound(path,pins[str(path)])
    implementation = {name:pin for name,pin in manifest['immutable_files_sha256'].items() if name.startswith('autorouter/')}
    current40_reserve(runtime,implementation)
    old = prior(original/pv.MANIFEST); prepared = prior(original.parent/'installed-setup.json')
    built = prior(original.parent/'build.log')
    require(pv._runtime_identity(original,implementation) == built['source_provenance']
        and built.get('root') == str(original) and built.get('local_engine_copied') is True
        and built.get('standalone') is False and built.get('published') is False
        and prepared.get('prepared') is True and prepared.get('qualified') is False
        and prepared.get('actual_GUI') is False and prepared.get('source_head') == identity['git_head']
        and prepared.get('runtime') == str(runtime)
        and prepared.get('kind') == 'runtime074-existing-local-installed-setup-v1'
        and prepared.get('source_manifest_sha256') == frozen['source_manifest_sha256'] == pins[str(original/pv.MANIFEST)]
        and prepared.get('manifest_sha256') == manifest_pin,
        'current original build/installed setup identity differs')
    receipt = prior(runtime/'.runs/install-existing-runtime-001.json')
    installed_root_binding(old,manifest,receipt,original,runtime,frozen['source_manifest_sha256'],manifest_pin)
    require(receipt['source_manifest_sha256'] == frozen['source_manifest_sha256']
        and receipt['destination_manifest_sha256'] == manifest_pin
        and pins[str(runtime/'.runs/install-existing-runtime-001.json')] == frozen['installation_receipt_sha256'],
        'installation/cohort pins differ')
    returned = prior(original.parent/'install.log')
    require(returned.get('root') == str(runtime) and returned.get('source_provenance') == identity
        and returned.get('installation_receipt_sha256') == frozen['installation_receipt_sha256']
        and returned.get('local_engine_copied') is True and returned.get('standalone') is False,
        'installer return binding differs')
    def success(value):
        return (value.get('status') == 'success' and type(value.get('exit_code')) is int
            and value['exit_code'] == 0 and value.get('cleanup_complete') is True and value.get('log_truncated') is False)
    full = prior(full_base/'execution.json')
    full_plan = prior(full_base/'protocol.json')
    require(prepared['full241']['execution_sha256'] == pins[str(full_base/'execution.json')]
        and prepared['full241']['tests'] == 2894 and prepared['full241']['skipped'] == 1
        and prepared['full241']['before_after_automatic_source_fence'] is True
        and prepared['full241']['sources_unchanged'] is True and prepared['full241']['cleanup_complete'] is True
        and len(full_plan['source_sha256']) == 365
        and full.get('passed') is True and full.get('sources_unchanged') is True and success(full['process'])
        and full_plan['tools']['git_head'] == identity['git_head']
        and all(full_plan['source_sha256'].get(name) == pin for name,pin in implementation.items()),
        'current full'+full_number+' source/process binding differs')
    timings=prior(full_base/'test-timings.json')
    require(pins[str(full_base/'test-timings.json')]==prepared['full241']['timings_sha256']
        and timings.get('successful') is True and timings.get('discovered')==timings.get('run')==2894
        and timings.get('failures')==timings.get('errors')==0 and timings.get('skipped')==1
        and type(timings.get('rows')) is list and len(timings['rows'])==2894,
        'actual full241 discovery/run/timing proof differs')
    venv = prior(original.parent/'venv-process.json')
    base_python_path = pv.canonical(Path(venv['argv'][len(f.SANDBOX)]))
    base_python = dict(path=str(base_python_path),sha256=pins[str(base_python_path)])
    require(success(venv) and venv.get('cwd') == str(runtime)
        and venv.get('argv') == [*f.SANDBOX,base_python['path'],'-B','-m','venv',
                                 '--copies','--without-pip',str(runtime/'.venv')]
        and pv.file_digest(runtime/'.venv/bin/python',pv.MAX_ENGINE_BYTES)[0] == base_python['sha256'],
        'actual copied interpreter/process differs')
    def cfg(root):
        path = root/'.venv/pyvenv.cfg'
        require(pv.file_digest(path,64*1024)[0] == pins[str(path)], 'copied environment configuration changed')
        return dict(line.strip().split(' = ',1) for line in pv.read_bytes(path,64*1024).decode().splitlines())
    current_cfg = cfg(runtime)
    require(not os.path.lexists(original/'.venv')
        and current_cfg.get('home') == str(base_python_path.parent)
        and current_cfg.get('executable') == str(base_python_path)
        and current_cfg.get('version') == '3.11.9' and current_cfg.get('include-system-site-packages') == 'false'
        and pv.file_digest(base_python_path,pv.MAX_ENGINE_BYTES)[0] == base_python['sha256'],
        'base interpreter/environment changed; original build has no venv')
    doctor = prior(original.parent/'doctor.log')
    require(success(prior(original.parent/'doctor-process.json')) and doctor.get('ready') is True
        and doctor.get('workspace') == str(runtime)
        and doctor['checks'].get('runtime_provenance') == dict(verified=True,identity=identity),
        'current installed doctor binding differs')
    tools = prior(base/'tools-defaults.json')['tools']
    require(tools.get('source_provenance') == identity and tools.get('implementation_sha256') == implementation
        and success(prior(base/'tools-defaults-process.json')), 'installed tools query differs')
    expected = dict(NATIVE_CASES,**HIGH_CASES,**{
        'improve-eeprom90-return':('improve',0),'ordinary-arcdice-admission':('route',0)})
    require(len(frozen['protocols']) == len(batch['rows']) == 13
        and {row['case'] for row in frozen['protocols']} == {row['case'] for row in batch['rows']} == set(expected),
        'complete unique thirteen-case population required')
    packets = []; proof_facts = []; plot_pairs = []
    workflows = [(item,row,base/item['case']/'protocol.json',False) for item,row in zip(frozen['protocols'],batch['rows'])]
    if class_mode:
        class_base = ROOT/'.runs/improve-parent-class-runtime074-native-qualification-001'
        master = fixed['.runs/runtime074 fresh install 001/.runs/native7-comparison-parent-class-qualification-001/result.json']
        class_plan = fixed[str((class_base/'protocol.json').relative_to(ROOT))]
        class_execution = fixed[str((class_base/'positive/execution.json').relative_to(ROOT))]
        public = fixed['evidence/runtime074-installed-native-milestone-001.json']
        class_outer = fixed[str((class_base/'enclosure/result.json').relative_to(ROOT))]
        control_root = runtime/'.runs/native7-comparison-parent-class-qualification-001'
        require(class_outer.get('passed') is True and class_outer.get('status') == 'completed'
            and success(class_outer['process'])
            and all(type(class_outer.get(key)) in (int,float) and 0 <= class_outer[key] <= 450
                for key in ('complete_wall_seconds','complete_full_CPU_seconds'))
            and class_outer['protocol_sha256'] == master['protocol_sha256']
            and class_plan['output'] == str(control_root) and class_outer['child_receipt'] == str(control_root/'result.json')
            and class_outer['child_sha256'] == fixed_pins[str((control_root/'result.json').relative_to(ROOT))]
            and report.inventory(control_root) == class_outer['completed_evidence'], 'class enclosure/raw proof seal differs')
        require(public.get('source_head') == head and public.get('installed_manifest_sha256') == manifest_pin
            and public.get('Native13',{}).get('passed') is True
            and public['Native13'].get('frozen_sha256') == fixed_pins['.runs/runtime074-installed-native-qualification-001/frozen.json']
            and public['Native13'].get('batch_sha256') == fixed_pins['.runs/runtime074-installed-native-qualification-001/batch-result.json']
            and public.get('actual_GUI_qualified') is False
            and public.get('matched_class',{}).get('passed') is True
            and public['matched_class'].get('enclosure_sha256') == fixed_pins[str((class_base/'enclosure/result.json').relative_to(ROOT))],
            'actual074 public headless fields differ; summary alone is never qualification')
        require(master.get('control_passed') is True and master.get('status') == 'completed'
            and master.get('accepted') is False and master.get('production_admitted') is False
            and type(master.get('completed_trial_count')) is int and master['completed_trial_count'] == ACTUAL_CLASS_COMPLETED_TRIALS
            and master.get('whole_wall_full_cpu_seconds') == 450 and master.get('own_wall_full_cpu_seconds') == 420
            and all(type(master.get(key)) in (int,float) and 0 <= master[key] <= 420
                for key in ('sampled_wall_seconds','sampled_full_cpu_seconds'))
            and master.get('unstarted') == [] and type(master.get('protected_count')) is int and master['protected_count'] == 1
            and master.get('protocol_sha256') == fixed_pins[str((class_base/'protocol.json').relative_to(ROOT))]
            and class_plan.get('runtime') == str(runtime) and class_plan.get('runtime_manifest_sha256') == manifest_pin
            and class_plan.get('source_head') == head and class_plan.get('tools') == tools
            and class_plan.get('source') == master.get('source') and class_plan.get('source_hashes') == master.get('source_hashes')
            and master.get('tools') == tools
            and success(master['positive_process']) and success(class_execution['process']), 'exact owned class control lineage required')
        positive_path = class_base/'positive/protocol.json'
        cp = bound(positive_path,class_plan['positive_protocol_sha256'])
        require(class_plan['positive_protocol'] == str(positive_path)
            and cp['settings'] == class_plan['settings'] == dict(pref.DEFAULTS,seconds=90,profile='tuned')
            and cp['method'] == 'improve' and cp['source'] == class_plan['source'] and cp['source_hashes'] == class_plan['source_hashes']
            and class_execution.get('controls_passed') is True and class_execution.get('workflow_delivered') is True,
            'class positive source/settings or delivery differs')
        item = dict(case='parent-class-positive',protocol_sha256=class_plan['positive_protocol_sha256'])
        row = dict(case=item['case'],passed=True,status='passed',execution_sha256=fixed_pins[str((class_base/'positive/execution.json').relative_to(ROOT))],
            Native_counts=class_execution['Native_counts'],ignored_check_count=2)
        workflows.append((item,row,positive_path,True))
    for item,row,path,is_class in workflows:
        label = item['case']; method,protected = ('improve',1) if is_class else expected[label]
        require(row['case'] == label and row.get('passed') is True and row.get('status') == 'passed', 'cohort row changed')
        plan = bound(path,item['protocol_sha256'])
        execution = bound(path.parent/'execution.json',row['execution_sha256'])
        process = execution['process'] if is_class else bound(path.parent/'batch-process.json',row['process_sha256'])
        require(plan.get('runtime') == str(runtime) and plan.get('runtime_manifest_sha256') == manifest_pin
            and plan.get('source_head') == identity['git_head'] and plan.get('tools') == tools and plan.get('method') == method
            and execution.get('controls_passed') is True and execution.get('workflow_delivered') is True
            and execution.get('protocol_sha256') == item['protocol_sha256'] and success(execution['process'])
            and success(process) and execution.get('protected_count') == protected
            and all(type(execution.get(key)) in (int,float) and 0 <= execution[key] <= 255
                for key in ('complete_wall_seconds','complete_full_CPU_seconds')),
            'actual installed workflow/process/cap differs')
        output = runtime/'.runs'/(label+'-001')
        require(plan.get('output') == str(output) and execution.get('child_receipt') == str(output/'result.json')
            and io.inventory(Path(plan['source']).parent) == plan['source_hashes'], 'registered source/output differs')
        child = bound(output/'result.json',execution['child_sha256'])
        workspace = Path(child['workspace']); route_path = workspace/'route/result.json'; export_path = workspace/'export/export.json'
        require(workspace.parent == output and re.fullmatch(r'autorouter-gui-[0-9a-f]{32}',workspace.name)
            and child.get('status') == 'completed' and child.get('workflow_delivered') is True
            and child.get('method') == method and child.get('settings') == plan['settings']
            and child.get('source_hashes') == plan['source_hashes'] and child.get('tools') == tools,
            'actual installed child identity/settings differ')
        parent = bound(route_path,child['route_receipt_sha256']); exported = report.read(export_path)
        if is_class:
            require(str(workspace) == master['positive_workspace']
                and child['route_receipt_sha256'] == master['route_receipt_sha256']
                and report.digest(export_path) == master['export_receipt_sha256'], 'class master own-final bridge differs')
        require(parent.get('accepted') is True and exported.get('export_accepted') is True
            and exported['inputs']['receipt'] == str(route_path)
            and exported['inputs']['receipt_sha256'] == child['route_receipt_sha256']
            and parent['candidate_sha256'] == exported['candidate_sha256'] == child['candidate_sha256'],
            'canonical parent/export lineage differs')
        delivery,pairs = report.installed_delivery(child,plan,output,workspace)
        proof_facts.append(delivery); plot_pairs.extend(pairs)
        allowed = [output]
        for receipt_path,is_export,data in ((route_path,False,parent),(export_path,True,exported)):
            own = report.own_final(receipt_path,export=is_export,plan=plan,allowed=allowed,accepted=True,public_sanitize=True)
            folder = receipt_path.parent/'validation' if is_export else receipt_path.parent
            audit = report.read(folder/'final-netclass-audit.json')
            require(audit.get('candidate_sha256') == own['candidate_sha256']
                and audit.get('project_sha256') == plan['source_hashes'][Path(plan['source']).with_suffix('.kicad_pro').name]
                and audit.get('native_map_file_sha256') == report.digest(folder/'final-netclasses.json')
                and audit.get('native',{}).get('passed') is True
                and audit.get('route_dimensions',{}).get('passed') is True
                and audit['route_dimensions']['checked']['protected'] == protected,
                'own class/dimension/original protection evidence differs')
            require(own['Native_counts'] == row['Native_counts']
                and own['ignored_check_count'] == row['ignored_check_count'], 'cohort warnings/ignored census differs')
            packets.append((folder,data)); proof_facts.append(dict(own_final=own,
                class_audit_sha256=report.digest(folder/'final-netclass-audit.json'),
                class_map_sha256=report.digest(folder/'final-netclasses.json')))
        if method == 'improve':
            # Exact stored producer receipts bind settings, selection and return
            # policy; shared reporting checks each child's own Native proof.
            require(parent.get('finalization_reserve_seconds') == parent.get('finalization_cpu_reserve_seconds') == 40
                and parent.get('budget_seconds') == parent.get('cpu_budget_seconds') == plan['settings']['seconds'],
                'current Improve return policy differs')
            # Reuse the versioned reporter's exact parent/context/incumbent
            # basis/worker/trial-selection lineage, not hashes first computed
            # during this admission. The frozen parent pins its incumbent.
            replay_plan = dict(plan,kind=CHOICE60_METHOD_KIND,improve_finalization_reserve_seconds=40)
            if is_class: replay_plan['improve_parent_class_policy'] = 'native-parent-dimensions-v1'
            facts = report.improve_facts(route_path,replay_plan,allowed,qualified_parent=True,
                public_sanitize=True,prerequisite_seconds=plan['settings']['seconds'])
            if is_class:
                require(len(facts['trials']) == master['completed_trial_count']
                    and all(row['Native_completion_qualified'] for row in facts['trials']), 'class completed trial proof differs')
                proof_facts.append(report.improve_auxiliary(export_path.parent/'validation',exported,replay_plan,export=True))
            proof_facts.append(facts)
            incumbent_path = route_path.parent/'incumbent/result.json'
            packets.append((incumbent_path.parent,report.read(incumbent_path)))
            for fact in facts['trials']:
                if fact['Native_completion_qualified']:
                    trial_path = Path(fact['receipt']); packets.append((trial_path.parent,report.read(trial_path)))
    require(invalid.get('passed') is True and invalid.get('status') == 'completed' and success(invalid['process'])
        and invalid_plan.get('runtime') == str(runtime) and invalid_plan.get('runtime_manifest_sha256') == manifest_pin
        and invalid.get('protocol_sha256') == fixed_pins[invalid_prefix+'/protocol.json'],
        'current installed invalid controls differ')
    negative = bound(Path(invalid['child_receipt']),invalid['child_sha256'])
    require(negative.get('control_passed') is True and negative.get('status') == 'completed'
        and negative.get('accepted') is False and negative.get('production_admitted') is False
        and [row.get('case') for row in negative['cases']] == ['short','protected-width','hole-clearance']
        and all(row.get('passed') is True for row in negative['cases']), 'three actual invalid controls required')
    invalid_output = Path(invalid_plan['output'])
    require(report.inventory(invalid_output) == invalid.get('completed_evidence'),
            'stored invalid-control material changed')
    if class_mode:
        require([row.get('case') for row in master['controls']] == ['width-target','class-source-PRO']
            and all(row.get('passed') is True for row in master['controls']), 'two exact class negatives required')
        for row in master['controls']:
            require(io.inventory(Path(row['candidate']).parent) == row['candidate_hashes']
                and io.inventory(Path(row['diagnostic_source']).parent) == row['diagnostic_hashes']
                and all(step.get('cleanup_complete') is True and step.get('log_truncated') is False
                    and step.get('name') != 'engine' for step in row['steps'])
                and report.native_application_policy(row['diagnostic_native'],cp)['accepted'] is True,
                'class invalid source/process/Native material changed')
            packets.append((Path(row['candidate']).parent.parent,row))
    if class_mode:
        require(report.inventory(control_root) == class_outer['completed_evidence'], 'class raw proof changed during replay')
    live_closure=required_actual_live_controls(runtime,manifest_pin,report,fixed)
    gui_closure=required_actual_gui_closure(runtime,manifest_pin,report,bound,dependencies)
    # Large proof closure is replayed here during preparation;
    # only its fixed top bindings enter the bounded32 child prerequisite map.
    closure = hashlib.sha256(f.canonical(dict(dependencies=dependencies,own_finals=proof_facts)).encode()).hexdigest()
    top = {str(ROOT/name):pin for name,pin in fixed_pins.items()}
    top[str(report_source)] = reporter_pin
    top[str(SHARED_HELPER_PATH)] = SHARED_HELPER_SHA256
    top[str(Path(__file__).resolve())] = SOURCE_IDENTITY['files']['scripts/qualification_runtime074.py']
    top[str(ROOT/ACTUAL_GUI_CLOSURE_PATH)] = ACTUAL_GUI_CLOSURE_SHA256
    cli = [Path(name) for name in tools['files'] if Path(name).name == 'kicad-cli']
    require(len(cli) == 1, 'unique actual pinned Native CLI required')
    _check_shared_helper_source()  # Source reads precede every final PRL metadata replay.
    local_settings.check_final_events(packets,cli[0],pairs=plot_pairs)
    for name in invalid['completed_evidence']:
        if name.endswith('.kicad_prl'):
            require(local_settings.check_current_metadata(invalid_output/name) is True,
                    'invalid-control PRL metadata changed')
    result = dict(kind=qualification_kind,Native_cohort_only=True,
        runtime=str(runtime),source_head=identity['git_head'],runtime_manifest_sha256=manifest_pin,
        actual_GUI_qualified=False,full_GUI_claim=False,tools_files_sha256=tools['files'],
        finalization_reserve_seconds=40,cohort_cases=13,stored_proof_closure_sha256=closure,
        scope=('Exact installed074/current40 Native CLI prerequisite only; no GUI/electrical/holdout qualification.'
            if not class_mode else 'Exact installed074 parent-class Native CLI follow-up only; no GUI/electrical/holdout qualification.'))
    if class_mode: result.update(parent_class_completed_trials=ACTUAL_CLASS_COMPLETED_TRIALS,parent_class_invalid_controls=2)
    result['required_actual_GUI_closure']=gui_closure
    result['required_actual_live_controls']=live_closure
    result.update(handoff_stage_policy='bounded-review60-choice60-v3',delivery_stage_seconds=dict(review=60,choice=60))
    return result,top
