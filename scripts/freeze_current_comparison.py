#!/usr/bin/env python3
"""Freeze 1–4 explicitly exposed local families before any comparison arm runs.

Mac/selected7 only. All six arms use 420 routing / 450 method / 600 complete
wall+CPU seconds and 120 export seconds. This performs one bounded tools query, never Native routing, a
board preflight, source scripts, downloads or publication. Explicit rights are
caller declarations, not legal clearance or independent/untouched pedigree.
Keep administration HEAD and all inputs fixed while running each protocol with
scripts/enclose_current_comparison.py. Record complete external costs/failures;
setup costs are additional. Four GiB startup headroom is not a future job quota.
A failure retains its partial new namespace; never delete/reuse it automatically.
"""
from pathlib import Path
import argparse
import ast
import copy
import hashlib
import json
import os
import re
import resource
import shutil
import sys
import time

START = time.monotonic()
def cpu():
    return sum(row.ru_utime + row.ru_stime for row in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import provenance as pv, handoff as h, placement_clearance as io
from autorouter import floor_route as f, preferences as pref, pipeline as p
from autorouter.gui import child_environment
from autorouter.runner import run

POPULATION = ('B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cthermal')
ARM_ORDER = ('Cdefault', 'B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cthermal')
VARIANTS = ('via_default', 'via_low', 'via_high')
LIMITS = dict(routing_seconds=420, method_wall_cpu_cap_seconds=450,
              delivery_wall_cpu_cap_seconds=600, export_validation_seconds=120)
ADMIN_FILES = ('scripts/qualify_comparison_portfolio.py', 'scripts/experiment_portfolio.py',
    'scripts/experiment_quality.py', 'scripts/qualify_installed_workflow.py',
    'scripts/qualify_current_method.py', 'scripts/freeze_current_comparison.py',
    'scripts/enclose_current_comparison.py')
LEGACY_ENCLOSURE_SHA = 'a441b05adc76deb55e75b809c0d6ec39f3d6a6ee7d700cf545c8f893d5e0dc34'
ENCLOSURE_SHA = '2c0a80af01f20f8985f1560cf6c10fb4a707bd4784832b963d6918858c44219b'
QUALIFICATION_KIND = 'runtime042-install-existing-actual-Native-and-single-GUI-vertical-slice-v1'
IMPROVE_POPULATION = ('B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cimprove')
IMPROVE_ARM_ORDER = ('Cdefault', 'B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cimprove')
IMPROVE_POPULATION_KIND = 'frozen-current-improve-six-arm-exposed-development-v2'
IMPROVE_METHOD_KIND = 'installed-native7-current-method-v2'
IMPROVE_QUALIFICATION_KIND = 'runtime050-install-existing-actual-Native-CLI-prepared-GUI-only-v1'
CURRENT40_VERSION = 'improve-v3-current40'
CURRENT40_POPULATION_KIND = 'frozen-current-improve-six-arm-exposed-development-v3-current40'
CURRENT40_METHOD_KIND = 'installed-native7-current-method-v3-current40'
CURRENT40_QUALIFICATION_KIND = 'runtime060-fresh-installed-thirteen-current40-CLI-only-v1'
CURRENT40_REPORTER_SHA = 'a0a925ad9c03602f34efdcc0a249e81729effb9231576b62977f35801a809f13'
CURRENT40_HEAD = '972b395878b734ccf47c7691d66435c42c032634'
# This finite adapter admits these completed receipts, not arbitrary future
# cohorts or a sanitized summary. Relative paths contain no foreign source.
CURRENT40_060_PINS = {
    '.runs/runtime060-installed-native-qualification-001/frozen.json': '907b271df390469c81df035986970deba28e9289ae43e1f5c32c59f6c363ea1d',
    '.runs/runtime060-installed-native-qualification-001/batch-result.json': 'b2fa39d3955f99ad73cf5fadda9fc7b9dd67011a2d2080a7f89452880b0c474c',
    '.runs/runtime060-native-controls-001/invalid/protocol.json': 'e533ee37df9a36cc3cf8bad61a71c8242c2b41b3798d68ced2741e6c842924bd',
    '.runs/runtime060-native-controls-001/invalid/enclosure/result.json': '5f2592c22367d0bb879b92739733bf9c70ba4d899982f10a29e96bd007b2ced6',
}
PARENT_CLASS_VERSION = 'improve-v4-parent-class062'
PARENT_CLASS_POPULATION_KIND = 'frozen-current-improve-six-arm-exposed-development-v4-parent-class062'
PARENT_CLASS_QUALIFICATION_KIND = 'runtime062-fresh-installed-thirteen-parent-class-CLI-only-v1'
PARENT_CLASS_HEAD = 'a048279c066fa96e7837f2beb48d579ddf7faf2d'
PARENT_CLASS_MANIFEST = '91ac790f38cd34c2842fb6d4208f13bf1a289fbcc15bc3b5b9048eaa5ef070d9'
PARENT_CLASS_REPORTER_SHA = 'ff19663cf3c0c24a4544d5f2c84c6fa2eac511d11aa65fd7df92346b9aeb8011'
PARENT_CLASS_062_PINS = {
    '.runs/runtime062-installed-native-qualification-001/frozen.json': 'ab44878f32aecf40bdea693044ddfa3ecf58e0636abb5533256db87b527461a0',
    '.runs/runtime062-installed-native-qualification-001/batch-result.json': '92e15267132b5f3c925723248edb481992014155a7ae800a663bc11824d2158b',
    '.runs/runtime062-native-controls-001/invalid/protocol.json': '7a2b6a17e509cd149eb418856f41a0941fe6c2ab30cd8cf698aa2e2ecbbda3be',
    '.runs/runtime062-native-controls-001/invalid/enclosure/result.json': 'c6a843368eaa32f44d8f4e40fe7ec3774c369ada7c3c0677de5a369c6aafd598',
    '.runs/improve-parent-class-runtime062-native-qualification-001/protocol.json': '4ebd5b1797b09d32b4c0f57ddf831d0094022e9387f95fa752dc12f7502cba7e',
    '.runs/improve-parent-class-runtime062-native-qualification-001/positive/execution.json': 'f313d4a73a1301d4047863e526895102aeffe77d21542a70e1826bae0e4873e3',
    '.runs/runtime062 fresh install 001/.runs/native7-comparison-parent-class-qualification-001/result.json': 'e11ab2dfe068d76535e4bc7c50e5963d41745b55ce24ff6d74619acdfe0c207e',
    '.runs/full-integration-218/execution.json': '65985f8f2478ed471466387854a85cbdbc3f36e57d8a1aba9cab61f67cd7f057',
    '.runs/full-integration-218/protocol.json': '16c36084ac79793d96b54caf7c7274f25bab0e88e91cb3ebf20a3f0214bbb66c',
    'evidence/runtime062-installed-native-milestone-001.json': '9f5aa457b09b7fc9edfe575a574e6704d4d365a419a30f174cb729c80710430c',
    '.runs/improve-parent-class-runtime062-native-qualification-001/enclosure/result.json': '7aa33516bd7b64a0f511a8b3d82e6619c10c049b72a8bc0bf05ab3c347fa4fd7',
}
REVIEW60_VERSION = 'improve-v5-review60'
REVIEW60_POPULATION_KIND = 'frozen-current-improve-six-arm-exposed-development-v5-review60'
REVIEW60_METHOD_KIND = 'installed-native7-current-method-v4-review60'
REVIEW60_PORTFOLIO_KIND = 'installed-native7-comparison-portfolio-functional-v2-review60'
REVIEW60_QUALIFICATION_KIND = 'runtime068-fresh-installed-review60-native-CLI-only-v1'
REVIEW60_STAGE_POLICY = 'bounded-review60-choice30-v2'
REVIEW60_STAGE_SECONDS = dict(review=60,choice=30)
REVIEW60_ENCLOSURE_SHA = '17a17b0c0e92a30377a0cbff8693791d878c5abbc51dbaf8ce36a7bfef580629'
# No invented source/manifest/Native success. The reviewed exact proof adapter
# must be ported after a real068 milestone before this version can freeze.
REVIEW60_HEAD = None
REVIEW60_MANIFEST = None
REVIEW60_INSTALLED_ROOT = None
REVIEW60_REPORTER_SHA = 'f41b9edc1fb3b89e94bae3c9210d183bffa86b48f58f2db41219129bb65e906d'
CHOICE60_VERSION = 'improve-v6-review60-choice60'
CHOICE60_POPULATION_KIND = 'frozen-current-improve-six-arm-exposed-development-v6-review60-choice60'
CHOICE60_METHOD_KIND = 'installed-native7-current-method-v5-review60-choice60'
CHOICE60_PORTFOLIO_KIND = 'installed-native7-comparison-portfolio-functional-v3-review60-choice60'
CHOICE60_QUALIFICATION_KIND = 'runtime069-fresh-installed-review60-choice60-native-CLI-only-v1'
CHOICE60_STAGE_POLICY = 'bounded-review60-choice60-v3'
CHOICE60_STAGE_SECONDS = dict(review=60,choice=60)
CHOICE60_ENCLOSURE_SHA = '77c50a3a1b152207619ba26642fba116b577c2d5313aa5168c6b2c4f5c588bfe'
CHOICE60_REPORTER_SHA = '8e927b0ed08752a36aa1c8368d038136bc821a2f816f9e1da86b8bc388793365'
CHOICE60_HEAD = None
CHOICE60_MANIFEST = None
CHOICE60_INSTALLED_ROOT = None
NATIVE_COHORT_QUALIFICATION_KIND = 'current-selected-native7-positive-cohort-CLI-only-v1'
NATIVE_CASES = {'ordinary-npth2Cu': ('route', 1), 'improve-pour-only': ('improve', 1),
    'improve-fractional': ('improve', 1), 'improve-floor2Cu': ('improve', 1),
    'ordinary-alias2Cu': ('route', 4), 'ordinary-whole4Cu': ('route', 10),
    'ordinary-hierarchy2Cu': ('route', 0)}
HIGH_CASES = {'via-high-whole2Cu': ('route', 1), 'via-high-partial2Cu': ('route', 4),
    'via-high-whole4Cu': ('route', 10), 'via-high-partial4Cu': ('route', 10)}
MAX_PROJECT_FILES = 2000
# The unchanged arm controllers use the shared 32 MiB source census.
MAX_PROJECT_BYTES = 32 * 1024**2


def require(ok, message):
    if not ok: raise ValueError(message)


def contract(version):
    if version == CHOICE60_VERSION:
        return IMPROVE_POPULATION, IMPROVE_ARM_ORDER, CHOICE60_POPULATION_KIND, CHOICE60_METHOD_KIND, 'qualify-current-method-005.py'
    if version == REVIEW60_VERSION:
        return IMPROVE_POPULATION, IMPROVE_ARM_ORDER, REVIEW60_POPULATION_KIND, REVIEW60_METHOD_KIND, 'qualify-current-method-004.py'
    if version == 'legacy-v1':
        return POPULATION, ARM_ORDER, 'frozen-current-six-arm-exposed-development-v1', 'installed-native7-current-method-v1', 'qualify-current-method-001.py'
    if version == CURRENT40_VERSION:
        return IMPROVE_POPULATION, IMPROVE_ARM_ORDER, CURRENT40_POPULATION_KIND, CURRENT40_METHOD_KIND, 'qualify-current-method-003.py'
    if version == PARENT_CLASS_VERSION:
        return IMPROVE_POPULATION, IMPROVE_ARM_ORDER, PARENT_CLASS_POPULATION_KIND, CURRENT40_METHOD_KIND, 'qualify-current-method-003.py'
    require(version == 'improve-v2', 'unknown comparison population version')
    return IMPROVE_POPULATION, IMPROVE_ARM_ORDER, IMPROVE_POPULATION_KIND, IMPROVE_METHOD_KIND, 'qualify-current-method-002.py'


def qualification_scope(qualified, runtime, manifest_pin, identity, manifest, version):
    """Keep historical gates separate from the exact installed060/current40 gate."""
    if version == CHOICE60_VERSION:
        return choice60_installed_scope(qualified,runtime,manifest_pin,identity,manifest)
    if version == REVIEW60_VERSION:
        return review60_installed_scope(qualified,runtime,manifest_pin,identity,manifest)
    if version == CURRENT40_VERSION:
        return current40_installed_scope(qualified, runtime, manifest_pin, identity, manifest)
    if version == PARENT_CLASS_VERSION:
        return parent_class_installed_scope(qualified, runtime, manifest_pin, identity, manifest)
    if type(qualified.get('kind')) is str and re.fullmatch(
            r'runtime[0-9]{3}-(seven|eleven)-completed-native-workflows-v1', qualified['kind']):
        return native_cohort_scope(qualified, runtime, manifest_pin, identity, manifest, version)
    native = qualified.get('Native')
    require(type(qualified.get('schema')) is int and qualified['schema'] == 1
        and type(native) is dict and qualified.get('runtime') == str(runtime)
        and qualified.get('runtime_manifest_sha256') == manifest_pin and qualified.get('source_head') == identity['git_head']
        and qualified.get('immutable_map_build_lock_version_unchanged') is True
        and type(qualified.get('immutable_files')) is int and qualified['immutable_files'] == len(manifest['immutable_files_sha256'])
        and qualified.get('accepted') is False and native.get('doctor_ready') is True
        and native.get('six_stage_delivery') is True and native.get('counts') == [0,0,0,0]
        and all(type(v) is int for v in native['counts'])
        and identity.get('native_version') == '10.0.7' and manifest['local_engine'] is not None,
        'exact qualified root/source/manifest/map required')
    if version == 'legacy-v1':
        require(qualified.get('kind') == QUALIFICATION_KIND and qualified.get('actual_newroot_GUI_vertical_slice') is True
            and type(qualified.get('full188')) is dict and qualified['full188'].get('passed') is True
            and native.get('protected4') is True, 'exact042 GUI qualification required; no historical GUI transfer')
        return dict(kind=QUALIFICATION_KIND, full_GUI_claim=False), {}
    require(version == 'improve-v2' and qualified.get('kind') == IMPROVE_QUALIFICATION_KIND
        and qualified.get('workflow_CLI') is True and qualified.get('workflow_delivered') is True
        and qualified.get('production_admitted') is False and qualified.get('actual_GUI') is False
        and qualified.get('full_GUI_claim') is False and qualified.get('installation_record_is_authoritative') is False
        and type(native.get('protected_routes')) is int and native['protected_routes'] == 4
        and type(qualified.get('GUI087')) is dict and qualified['GUI087'].get('actual_GUI') is False
        and qualified['GUI087'].get('state') == 'PREPARED_ONLY_NOT_EXECUTED',
        'exact050 installed CLI/prepared-only GUI qualification required')
    dependency = ROOT/'evidence/runtime050-native-milestone-002.json'
    rows = qualified.get('dependencies')
    require(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict
        and rows[0].get('path') == str(dependency.relative_to(ROOT)), 'exact050 Native prerequisite required')
    _, proof = pinned_json(dependency, rows[0].get('sha256'))
    expected = {'ordinary-whole4Cu','improve-floor2Cu','ordinary-hierarchy2Cu','ordinary-npth2Cu',
                'improve-pour-only','ordinary-alias2Cu','improve-fractional'}
    require(type(proof.get('schema')) is int and proof['schema'] == 1
        and proof.get('kind') == 'runtime050-seven-completed-native-workflows-v1'
        and proof.get('source_head') == identity['git_head']
        and proof.get('runtime_manifest_sha256') == qualified.get('original_runtime_manifest_sha256')
        and proof.get('Native_cohort_passed') is True and proof.get('full199',{}).get('passed') is True
        and proof.get('invalid_controls',{}).get('passed') is True and type(proof.get('cases')) is list
        and len(proof['cases']) == 7 and {row.get('case') for row in proof['cases']} == expected,
        'completed050 full199/Native/invalid prerequisite differs')
    return dict(kind=IMPROVE_QUALIFICATION_KIND, actual_GUI_qualified=False, full_GUI_claim=False,
        scope='Installed Native CLI prerequisite; GUI087 prepared only, no current graphical qualification.'), {str(dependency): rows[0]['sha256']}



def review60_stage_fields(record):
    """Typed fixed policy fields shared by freezer and stored-facts reporting."""
    stages=record.get('delivery_stage_seconds')
    require(record.get('handoff_stage_policy') == REVIEW60_STAGE_POLICY
        and type(stages) is dict and stages == REVIEW60_STAGE_SECONDS
        and all(type(value) is int for value in stages.values()),
        'exact prospective review60/choice30 stage fields required')
    return dict(stages)


def review60_installed_scope(qualified,runtime,manifest_pin,identity,manifest):
    """Deliberately closed pending real068 proof; never substitute old062/067.

    Port installed_cohort_scope's actual full/source/install/doctor/13Native/
    invalid3/class-positive-and2negative/PRL proof replay with exact068 pins.
    No owner declaration or summary booleans can open this qualification gate.
    """
    raise ValueError('review60 qualification gate: actual runtime068 Native/install/full-proof adapter is not yet qualified')


def review60_qualification_summary(q,source_head,runtime,manifest_pin):
    """Stored summary identity only; cannot create or replace Native admission."""
    require(type(REVIEW60_HEAD) is str and pv._HEAD.fullmatch(REVIEW60_HEAD)
        and type(REVIEW60_MANIFEST) is str and pv._DIGEST.fullmatch(REVIEW60_MANIFEST)
        and type(REVIEW60_INSTALLED_ROOT) is str,
        'review60 qualification bindings remain pending the real milestone')
    review60_stage_fields(q)
    require(q.get('kind') == REVIEW60_QUALIFICATION_KIND and q.get('Native_cohort_only') is True
        and q.get('source_head') == source_head == REVIEW60_HEAD
        and q.get('runtime') == str(runtime) == REVIEW60_INSTALLED_ROOT
        and q.get('runtime_manifest_sha256') == manifest_pin == REVIEW60_MANIFEST
        and type(q.get('cohort_cases')) is int and q['cohort_cases'] == 13
        and type(q.get('parent_class_completed_trials')) is int and q['parent_class_completed_trials'] == 1
        and type(q.get('parent_class_invalid_controls')) is int and q['parent_class_invalid_controls'] == 2
        and type(q.get('finalization_reserve_seconds')) is int and q['finalization_reserve_seconds'] == 40
        and q.get('actual_GUI_qualified') is False and q.get('full_GUI_claim') is False,
        'exact prospective installed Native-only summary required')


def choice60_stage_fields(record):
    """Typed fixed policy fields shared by freezer and stored-facts reporting."""
    stages=record.get('delivery_stage_seconds')
    require(record.get('handoff_stage_policy') == CHOICE60_STAGE_POLICY
        and type(stages) is dict and stages == CHOICE60_STAGE_SECONDS
        and all(type(value) is int for value in stages.values()),
        'exact prospective choice60/choice60 stage fields required')
    return dict(stages)


def choice60_installed_scope(qualified,runtime,manifest_pin,identity,manifest):
    """Deliberately closed pending real069 proof; never substitute old062/067.

    Port installed_cohort_scope's actual full/source/install/doctor/13Native/
    invalid3/class-positive-and2negative/PRL proof replay with exact069 pins.
    No owner declaration or summary booleans can open this qualification gate.
    """
    raise ValueError('choice60 qualification gate: actual runtime069 Native/install/full-proof adapter is not yet qualified')


def choice60_qualification_summary(q,source_head,runtime,manifest_pin):
    """Stored summary identity only; cannot create or replace Native admission."""
    require(type(CHOICE60_HEAD) is str and pv._HEAD.fullmatch(CHOICE60_HEAD)
        and type(CHOICE60_MANIFEST) is str and pv._DIGEST.fullmatch(CHOICE60_MANIFEST)
        and type(CHOICE60_INSTALLED_ROOT) is str,
        'choice60 qualification bindings remain pending the real milestone')
    choice60_stage_fields(q)
    require(q.get('kind') == CHOICE60_QUALIFICATION_KIND and q.get('Native_cohort_only') is True
        and q.get('source_head') == source_head == CHOICE60_HEAD
        and q.get('runtime') == str(runtime) == CHOICE60_INSTALLED_ROOT
        and q.get('runtime_manifest_sha256') == manifest_pin == CHOICE60_MANIFEST
        and type(q.get('cohort_cases')) is int and q['cohort_cases'] == 13
        and type(q.get('parent_class_completed_trials')) is int and q['parent_class_completed_trials'] == 1
        and type(q.get('parent_class_invalid_controls')) is int and q['parent_class_invalid_controls'] == 2
        and type(q.get('finalization_reserve_seconds')) is int and q['finalization_reserve_seconds'] == 40
        and q.get('actual_GUI_qualified') is False and q.get('full_GUI_claim') is False,
        'exact prospective installed Native-only summary required')


def native_cohort_accepted(native, implementation):
    """Use the recorded product policy, never a second counts-only policy."""
    from autorouter import schematic_field_evidence, schematic_fields, sexpr
    pins = {}
    for module in (p, schematic_field_evidence, schematic_fields, sexpr):
        path = pv.canonical(Path(module.__file__)); name = 'autorouter/'+path.name
        require(path.parent == Path(p.__file__).parent and implementation.get(name) == pv.file_digest(path)[0],
                'Native application-policy implementation differs')
        pins[path] = implementation[name]
    accepted = p.native_accepted(native); reasons = p.native_rejection_reasons(native)
    require(type(accepted) is bool and accepted is (not reasons), 'Native policy predicates disagree')
    for path, pin in pins.items(): require(pv.file_digest(path)[0] == pin, 'Native policy source changed')
    return accepted


def native_cohort_scope(proof, runtime, manifest_pin, identity, manifest, version):
    """Consume a sealed metadata cohort, not replace any Native child validator.

    These summaries lack a root/map field: bind their indexed original manifest
    and build/full-suite lineage to the actual requested immutable root. Recheck
    these retained bytes at final freeze; an index hash alone is not their bytes.
    Warnings remain visible and do not establish electrical/whole-project clean.
    """
    match = re.fullmatch(r'runtime([0-9]{3})-(seven|eleven)-completed-native-workflows-v1', proof['kind'])
    require(version == 'improve-v2' and match is not None and runtime.is_relative_to(ROOT)
        and type(proof.get('schema')) is int and proof['schema'] == 1
        and proof.get('source_head') == identity['git_head'] and proof.get('runtime_manifest_sha256') == manifest_pin
        and identity.get('native_version') == '10.0.7' and manifest['local_engine'] is not None
        and proof.get('Native_cohort_passed') is True and proof.get('accepted') is False
        and proof.get('actual_GUI') is False and proof.get('project_complete') is False
        and proof.get('full_GUI_claim', False) is False and proof.get('release_qualified') is False
        and type(proof.get('invalid_controls')) is dict and proof['invalid_controls'].get('passed') is True,
        'positive current Native cohort required; no GUI/thermal admission')
    dependencies = {}; material = {}
    def public_path(name):
        require(type(name) is str and name.startswith('evidence/') and str(Path(name)) == name
            and not ({'.', '..', '.runs'} & set(name.split('/'))), 'canonical retained evidence path required')
        return pv.canonical(ROOT/name)
    def index(binding):
        require(type(binding) is dict and set(binding) == {'path', 'sha256'}, 'pinned retained index required')
        path = public_path(binding['path']); _, data = pinned_json(path, binding['sha256'])
        dependencies[str(path)] = binding['sha256']
        require(type(data.get('schema')) is int and data['schema'] == 1
            and type(data.get('material')) is list and 1 <= len(data['material']) <= 4000, 'bounded material index required')
        for row in data['material']:
            require(type(row) is dict and type(row.get('original')) is str
                and not Path(row['original']).is_absolute() and str(Path(row['original'])) == row['original']
                and not ({'.', '..'} & set(row['original'].split('/')))
                and type(row.get('bytes')) is int and 0 <= row['bytes'] <= 4*1024**2
                and type(row.get('sha256')) is str and pv._DIGEST.fullmatch(row['sha256']), 'malformed retained material')
            public_path(row.get('retained'))
            old = material.get(row['original'])
            require(old is None or (old['sha256'], old['bytes']) == (row['sha256'], row['bytes']), 'conflicting retained material')
            material[row['original']] = row
    def retained(original, pin=None):
        require(original.is_relative_to(ROOT), 'original proof escaped administration/runtime')
        row = material.get(str(original.relative_to(ROOT)))
        require(row is not None and (pin is None or row['sha256'] == pin), 'missing or differently pinned retained proof')
        raw, value = pinned_json(public_path(row['retained']), row['sha256'])
        require(len(raw) == row['bytes'], 'retained proof size differs')
        return value
    def success(process):
        return (type(process) is dict and process.get('status') == 'success'
            and type(process.get('exit_code')) is int and process['exit_code'] == 0
            and process.get('cleanup_complete') is True and process.get('log_truncated') is False)
    def counts(value):
        return (type(value) is list and len(value) == 4 and all(type(n) is int and n >= 0 for n in value)
            and value[0] == value[1] == value[3] == 0)
    index(proof.get('files_index'))
    ir_kinds = {'IR_repair': 'delivery-repair-regression-v1',
                'IR_delivery': 'delivery-regression-v1'}
    ir_keys = [key for key in proof if type(key) is str and key.startswith('IR_')]
    require(len(ir_keys) == 1 and ir_keys[0] in ir_kinds,
        'exactly one known current IR delivery dependency required')
    link = proof[ir_keys[0]]
    require(type(link) is dict, 'current IR delivery dependency required')
    ir_path = public_path(link.get('path')); _, ir = pinned_json(ir_path, link.get('sha256'))
    dependencies[str(ir_path)] = link['sha256']
    delivery = ir.get('single_fresh_exposed_IR_Improve')
    classification = delivery.get('classification') if type(delivery) is dict else None
    delivered = type(delivery) is dict and (
        (ir_keys[0] == 'IR_repair' and delivery.get('delivered') is True and 'classification' not in delivery)
        or (ir_keys[0] == 'IR_delivery' and 'delivered' not in delivery and type(classification) is dict
            and classification.get('evidence_classification') == 'validated_delivery'
            and all(classification.get(key) is True for key in
                    ('attempt_qualified','workflow_delivered','complete_external_cap_ok','method_cap_ok'))
            and classification.get('validated_completed_negative') is False))
    require(ir.get('kind') == 'runtime'+match[1]+'-single-fresh-exposed-IR-Improve-'+ir_kinds[ir_keys[0]]
        and type(ir.get('schema')) is int and ir['schema'] == 1 and ir.get('source_head') == identity['git_head']
        and ir.get('runtime_manifest_sha256') == manifest_pin and ir.get('workflow_delivered') is True
        and ir.get('attempt_qualified') is True and ir.get('accepted') is False and ir.get('actual_GUI') is False
        and ir.get('project_complete') is False and ir.get('not_a_comparison') is True
        and ir.get('full_GUI_claim', False) is False
        and ir.get('files_index') == link.get('files_index')
        and delivered and counts(delivery.get('Native_counts')), 'current pinned IR delivery differs')
    index(ir['files_index'])
    require(retained(runtime/pv.MANIFEST, manifest_pin) == manifest, 'retained original runtime/map differs')
    prepared = retained(runtime.parent/'preparation.json')
    full_keys = [key for key in prepared if re.fullmatch(r'full[0-9]+_execution_sha256', key)]
    require(prepared.get('prepared') is True and prepared.get('source_head') == identity['git_head']
        and prepared.get('runtime') == str(runtime) and prepared.get('manifest_sha256') == manifest_pin
        and type(prepared.get('recipe')) is dict and prepared['recipe'].get('source_provenance') == identity
        and len(full_keys) == 1, 'current build lineage differs')
    full_name = full_keys[0].split('_')[0]; full_dir = ROOT/'.runs'/('full-integration-'+full_name[4:])
    full = retained(full_dir/'execution.json', prepared[full_keys[0]]); plan = retained(full_dir/'protocol.json')
    require(type(ir.get(full_name)) is dict and ir[full_name].get('passed') is True
        and full.get('passed') is True and full.get('sources_unchanged') is True and success(full.get('process'))
        and type(plan.get('tools')) is dict and plan['tools'].get('git_head') == identity['git_head']
        and type(plan.get('source_sha256')) is dict
        and all(plan.get('source_sha256', {}).get(name) == pin for name, pin in manifest['immutable_files_sha256'].items()
                if name.startswith('autorouter/'))
        and success(retained(runtime.parent/'venv-process.json', prepared.get('venv_process_sha256'))), 'full/build process proof differs')
    doctors = [ROOT/name for name in material if Path(name).name == 'doctor.json']
    require(len(doctors) == 1, 'unique current doctor proof required')
    doctor = retained(doctors[0]); doctor_process = retained(doctors[0].with_name('doctor-process.json'))
    require(doctor.get('ready') is True and doctor.get('workspace') == str(runtime)
        and type(doctor.get('checks')) is dict
        and doctor['checks'].get('runtime_provenance') == dict(verified=True, identity=identity)
        and success(doctor_process), 'current doctor proof differs')
    expected = dict(NATIVE_CASES, **HIGH_CASES) if match[2] == 'eleven' else NATIVE_CASES
    rows = proof.get('cases')
    require(type(rows) is list and len(rows) == len(expected)
        and all(type(row) is dict and type(row.get('case')) is str for row in rows)
        and {row.get('case') for row in rows} == set(expected), 'complete unique registered Native population required')
    tool_files = None
    for row in rows:
        label = row['case']; method, protected = expected[label]; finals = row.get('own_finals')
        trials = row.get('trials'); trial_names = []
        if method == 'improve':
            require(type(trials) is list and len(trials) <= 32, 'bounded Improve trial census required')
            trial_names = ['trial-%04d' % n for n in range(len(trials))]
            require([trial.get('id') for trial in trials if type(trial) is dict] == trial_names, 'trial census differs')
        require(row.get('method') == method and row.get('controls_passed') is True and row.get('workflow_delivered') is True
            and row.get('source_unchanged') is True and row.get('actual_GUI') is False and counts(row.get('Native_counts'))
            and type(row.get('protected_count')) is int and row['protected_count'] == protected
            and row.get('scoring_preference') == ('via_high' if label in HIGH_CASES else None)
            and type(row.get('source_hashes')) is dict and 1 <= len(row['source_hashes']) <= MAX_PROJECT_FILES
            and all(type(pin) is str and pv._DIGEST.fullmatch(pin) for pin in row['source_hashes'].values())
            and type(finals) is dict and all(type(value) is dict and type(value.get('own_final')) is dict for value in finals.values())
            and set(finals) == {'parent', 'export', *(['incumbent', *trial_names] if method == 'improve' else [])}
            and all(type(row.get(key)) is str and pv._DIGEST.fullmatch(row[key]) for key in ('route_sha256','export_sha256')),
            'positive registered workflow/final census required; counts alone are insufficient')
        parent = finals['parent']['own_final']
        require(type(parent.get('cwd')) is str, 'own final directory required')
        directory = Path(parent['cwd'])
        require(directory.name == 'route' and directory.parent.parent == runtime/'.runs'/(label+'-001')
            and re.fullmatch(r'autorouter-gui-[0-9a-f]{32}', directory.parent.name), 'own proof runtime/root differs')
        route = retained(directory/'result.json', row.get('route_sha256'))
        exported = retained(directory.parent/'export/export.json', row.get('export_sha256'))
        require(route.get('accepted') is True and exported.get('export_accepted') is True
            and route.get('invariants_unchanged') is True
            and type(route.get('source')) is str and Path(route['source']).suffix == '.kicad_pcb'
            and type(route.get('tools')) is dict and route['tools'].get('source_provenance') == identity
            and route['tools'].get('git_head') == identity['git_head'] and route['tools'].get('kicad') == '10.0.7'
            and route['tools'].get('implementation_sha256') == {name: pin for name, pin in manifest['immutable_files_sha256'].items() if name.startswith('autorouter/')}
            and exported.get('tools') == route['tools']
            and route.get('source_hashes') == exported.get('source_hashes') == row.get('source_hashes')
            and exported.get('original_geometry_and_routing_unchanged') is True
            and type(exported.get('inputs')) is dict and exported['inputs'].get('receipt') == str(directory/'result.json')
            and exported['inputs'].get('receipt_sha256') == row['route_sha256'], 'retained route/export lineage differs')
        scope = 'partial_completion' if label in {'ordinary-alias2Cu','via-high-partial2Cu','via-high-partial4Cu'} else 'whole_board_unlocked_routing'
        profile = 'tuned' if method == 'improve' else 'standard'; score = 'via_high' if label in HIGH_CASES else None
        settings = dict(schema=1,scope=scope,profile=profile,scoring_preference=score,
            seconds=120 if label.endswith('4Cu') else 90,adapter='both',guidance='native',layers='source_all')
        require(type(row.get('child_sha256')) is str and pv._DIGEST.fullmatch(row['child_sha256']), 'actual workflow child required')
        workflow = retained(directory.parent.parent/'result.json', row['child_sha256'])
        choice = route.get('pruning_preferences' if method == 'improve' else 'routing_preferences')
        require(workflow.get('method') == method and workflow.get('settings') == settings
            and workflow.get('status') == 'completed' and workflow.get('workflow_delivered') is True
            and route.get('scope') == scope and route.get('engine_profile') == profile and route.get('adapter') == 'both'
            and route.get('input_policy','native') == 'native' and type(choice) is dict and choice.get('effective') == settings
            and (route.get('strategy') == 'native_validated_zone_net_pruning'
                 and route.get('scoring_variant') is None and 'incumbent_scoring_variant' not in route
                 if method == 'improve' else route.get('strategy') is None and 'scoring_variant' in route and route['scoring_variant'] == score),
            'registered method/scope/profile/scoring differs from retained workflow')
        if method == 'route':
            budget = route.get('engine_budget'); engine = retained(directory/'engine-process.json')
            require(type(budget) is dict and budget.get('profile') == profile
                and budget.get('scoring') == p.engine_scoring_settings(score)
                and type(budget.get('argv')) is list and budget['argv'] and all(type(arg) is str for arg in budget['argv'])
                and type(engine.get('argv')) is list and all(type(arg) is str for arg in engine['argv'])
                and engine['argv'][-4:] == ['-de',str(directory/'task.dsn'),'-do',str(directory/'routes.ses')]
                and engine['argv'][-len(budget['argv'])-4:-4] == budget['argv'] and engine.get('cwd') == str(directory)
                and success(engine), 'ordinary engine scoring/configuration journal differs')
            prefixes = ('--router.scoring.via_costs','--router.scoring.plane_via_costs')
            require([arg for arg in engine['argv'] if arg.startswith(prefixes)] == p.engine_scoring_settings(score)['argv']
                and type(route.get('steps')) is list
                and [step for step in route['steps'] if type(step) is dict and step.get('name') == 'engine'] == [engine],
                'actual engine scoring flags or unique journal differ')
        files = route['tools'].get('files')
        require(type(files) is dict and 1 <= len(files) <= 8
            and all(type(name) is str and type(pin) is str and pv._DIGEST.fullmatch(pin) for name, pin in files.items())
            and (tool_files is None or files == tool_files), 'cohort tool pins differ')
        tool_files = files
        cli = [name for name in files if Path(name).name == 'kicad-cli']
        require(len(cli) == 1, 'unique pinned Native CLI required')
        for name, final in finals.items():
            own = final.get('own_final', {}); folder = directory if name == 'parent' else directory.parent/'export/validation' if name == 'export' else directory/'incumbent' if name == 'incumbent' else directory/'trials'/name
            require(final.get('accepted') is True and counts(final.get('Native_counts'))
                and own.get('cwd') == str(folder) and own.get('output') == str(folder/'final-drc.json')
                and own.get('full_schematic_flag') is True and type(final.get('candidate_sha256')) is str
                and pv._DIGEST.fullmatch(final['candidate_sha256'])
                and all(type(own.get(key)) is str and pv._DIGEST.fullmatch(own[key])
                        for key in ('report_sha256','process_sha256','binding_sha256')), 'positive own final Native proof required')
            report = retained(folder/'final-drc.json', own['report_sha256'])
            process = retained(folder/'final-drc-process.json', own['process_sha256'])
            binding = retained(folder/'final-drc-binding.json', own['binding_sha256'])
            data = route if name == 'parent' else exported if name == 'export' else retained(folder/'result.json')
            require(data.get('export_accepted' if name == 'export' else 'accepted') is True
                and data.get('candidate_sha256') == final['candidate_sha256']
                and data.get('native_report_sha256') == own['report_sha256']
                and (data.get('invariants_unchanged') is True if name == 'incumbent' else data.get('invariants_unchanged',True) is True),
                'actual final acceptance/original invariant header differs')
            if name == 'incumbent':
                require(data.get('scope') == 'whole_board_unlocked_routing' and data.get('engine_profile') == 'tuned'
                    and data.get('adapter') == 'both' and 'scoring_variant' in data and data['scoring_variant'] is None,
                    'Improve incumbent settings differ')
            families = [report.get(key) for key in ('unconnected_items','violations','schematic_parity')]
            require(all(type(items) is list and all(type(item) is dict for item in items) for items in families), 'malformed final Native finding families')
            findings = families[1]+families[0]+families[2]
            native = data.get('native')
            actual = [len(families[0]), sum(item.get('severity') == 'error' for item in families[1]+families[2]),
                sum(item.get('severity') == 'warning' for item in findings),
                sum(item.get('severity') == 'exclusion' or item.get('excluded', False) for item in findings)]
            require(report.get('kicad_version') == '10.0.7' and report.get('source') == Path(route['source']).name
                and report.get('$schema') == 'https://schemas.kicad.org/drc.v1.json'
                and type(report.get('included_severities')) is list
                and all(type(value) is str for value in report['included_severities'])
                and set(report['included_severities']) == {'error','warning','exclusion'}
                and all(item.get('severity') in {'error','warning','exclusion'} for item in findings)
                and actual == final['Native_counts']
                and report.get('ignored_checks') == final.get('ignored_checks')
                and type(process.get('argv')) is list and process.get('cwd') == str(folder)
                and (process['argv'][:3] == [cli[0],'pcb','drc'] or process['argv'][:len(f.SANDBOX)+3] == [*f.SANDBOX,cli[0],'pcb','drc'])
                and process['argv'][-1:] == [str(folder/'final-drc-input'/Path(route['source']).name)]
                and str(folder/'final-drc.json') in process['argv']
                and all(flag in process['argv'] for flag in ('--schematic-parity','--all-track-errors','--refill-zones','--exit-code-violations'))
                and type(process.get('exit_code')) is int and process['exit_code'] == (5 if findings else 0)
                and process.get('status') == ('nonzero_exit' if findings else 'success') and process.get('cleanup_complete') is True
                and binding.get('source') == str(folder/'candidate'/Path(route['source']).name) and binding.get('saved') is False
                and binding.get('before') == dict(row['source_hashes'], **{Path(route['source']).name: final['candidate_sha256']}),
                'retained own Native counts/process/input binding differs')
            require(type(native) is dict and [native.get(key) for key in ('opens','blocking','warnings','exclusions')] == actual
                and native.get('findings') == findings and native.get('ignored_checks') == report['ignored_checks']
                and native_cohort_accepted(native,route['tools']['implementation_sha256']),
                'retained final Native evidence rejected by immutable product policy')
        require(finals['parent']['Native_counts'] == finals['export']['Native_counts'] == row['Native_counts']
            and finals['parent']['candidate_sha256'] == finals['export']['candidate_sha256'] == route.get('candidate_sha256') == exported.get('candidate_sha256'),
            'delivered candidate/counts differ')
    return dict(kind=NATIVE_COHORT_QUALIFICATION_KIND, evidence_kind=proof['kind'], Native_cohort_only=True,
        runtime=str(runtime), source_head=identity['git_head'], runtime_manifest_sha256=manifest_pin,
        actual_GUI_qualified=False, full_GUI_claim=False, tools_files_sha256=tool_files,
        scope='Current positive Native/CLI cohort and linked Improve delivery; no GUI/thermal/electrical qualification.'), dependencies


def current40_reserve(runtime, implementation):
    """Read a pinned immutable declaration without executing runtime modules."""
    path = runtime/'autorouter/_improve_context.py'
    raw = pv.read_bytes(path)
    require(hashlib.sha256(raw).hexdigest() == implementation.get('autorouter/_improve_context.py'),
            'current40 reserve declaration differs from immutable map')
    values = [ast.literal_eval(node.value) for node in ast.parse(raw).body
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
            and target.id == 'RESERVE_SECONDS' for target in node.targets)]
    require(len(values) == 1 and type(values[0]) is int and values[0] == 40,
            'current40 requires the exact40-second return policy')
    return values[0]


def installed_root_binding(old, new, receipt, original, runtime, source_pin, destination_pin):
    """Installation records describe a copy; immutable maps remain authority."""
    require(old.get('root') == str(original) and new == dict(old, root=str(runtime))
        and type(old.get('immutable_files_sha256')) is dict and len(old['immutable_files_sha256']) == 54
        and old.get('native_version') == '10.0.7' and old.get('local_engine') is not None
        and receipt.get('schema') == 1 and receipt.get('kind') == 'existing-runtime-installation-record-v1'
        and receipt.get('source_root') == str(original)
        and receipt.get('source_manifest_sha256') == source_pin
        and receipt.get('destination_manifest_sha256') == destination_pin
        and receipt.get('destination_root') == str(runtime)
        and receipt.get('immutable_files') == 54 and receipt.get('local_engine') == new['local_engine']
        and receipt.get('record_is_authoritative') is False
        and receipt.get('receipt_may_remain_on_refusal') is True
        and receipt.get('same_mac_dependency_locations_required') is True
        and all(receipt.get(key) is False for key in ('mutable_state_copied','venv_created',
            'launcher_created','native_qualification_performed','standalone','published')),
        'exact nonauthoritative root-only installation binding required')


def installed_scope_contract(version):
    """Finite reviewed identities; callers cannot choose a cohort or reserve."""
    if version == CURRENT40_VERSION:
        return ('060','212',CURRENT40_HEAD,
            '8f385b397ddb6379ce35bab92d62ceff55029c6a796f7d3269c5c5b34ed1ba30',
            CURRENT40_060_PINS,CURRENT40_REPORTER_SHA,CURRENT40_QUALIFICATION_KIND)
    require(version == PARENT_CLASS_VERSION, 'unknown installed cohort contract')
    return ('062','218',PARENT_CLASS_HEAD,PARENT_CLASS_MANIFEST,
        PARENT_CLASS_062_PINS,PARENT_CLASS_REPORTER_SHA,PARENT_CLASS_QUALIFICATION_KIND)


def current40_installed_scope(qualified, runtime, manifest_pin, identity, manifest):
    return installed_cohort_scope(qualified,runtime,manifest_pin,identity,manifest,CURRENT40_VERSION)


def parent_class_installed_scope(qualified, runtime, manifest_pin, identity, manifest):
    return installed_cohort_scope(qualified,runtime,manifest_pin,identity,manifest,PARENT_CLASS_VERSION)


def installed_cohort_scope(qualified, runtime, manifest_pin, identity, manifest, version):
    """Replay one exact versioned installed13 lineage, never Native.

    An additional runtime/cohort needs its own reviewed adapter. The old
    seven/eleven+IR and042/050 contracts are deliberately not broadened.
    """
    from scripts import report_current_comparison as report
    from autorouter import local_settings
    series,full_number,head,expected_manifest,fixed_pins,reporter_pin,qualification_kind = installed_scope_contract(version)
    class_mode = version == PARENT_CLASS_VERSION
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
    pins = frozen['prerequisite_sha256']
    for path,pin in {
        ROOT/('.runs/freeze-runtime'+series+'-installed-native-draft-001.py'):frozen['controller_sha256'],
        ROOT/'.runs/enclose-runtime044-workflow-001.py':frozen['enclosure_sha256'],
        ROOT/'scripts/qualify_runtime_workflow.py':frozen['driver_sha256'],
        Path(invalid_plan['controller']):invalid_plan['controller_sha256']}.items():
        require(pv.file_digest(path)[0] == pin, 'recorded Native controller/driver changed')
    def prior(path):
        return bound(path,pins[str(path)])
    implementation = {name:pin for name,pin in manifest['immutable_files_sha256'].items() if name.startswith('autorouter/')}
    current40_reserve(runtime,implementation)
    old = prior(original/pv.MANIFEST); prepared = prior(original.parent/'preparation.json')
    require(pv._runtime_identity(original,implementation) == prepared['recipe']['source_provenance']
        and prepared.get('prepared') is True and prepared.get('source_head') == identity['git_head']
        and prepared.get('runtime') == str(original)
        and prepared.get('manifest_sha256') == frozen['source_manifest_sha256'] == pins[str(original/pv.MANIFEST)],
        'current original build identity differs')
    receipt = prior(runtime/'.runs/install-existing-runtime-001.json')
    installed_root_binding(old,manifest,receipt,original,runtime,frozen['source_manifest_sha256'],manifest_pin)
    require(receipt['source_manifest_sha256'] == frozen['source_manifest_sha256']
        and receipt['destination_manifest_sha256'] == manifest_pin
        and pins[str(runtime/'.runs/install-existing-runtime-001.json')] == frozen['installation_receipt_sha256'],
        'installation/cohort pins differ')
    returned = prior(ROOT/('.runs/runtime'+series+'-install-existing-copy-001.log'))
    require(returned.get('root') == str(runtime) and returned.get('source_provenance') == identity
        and returned.get('installation_receipt_sha256') == frozen['installation_receipt_sha256']
        and returned.get('local_engine_copied') is True and returned.get('standalone') is False,
        'installer return binding differs')
    def success(value):
        return (value.get('status') == 'success' and type(value.get('exit_code')) is int
            and value['exit_code'] == 0 and value.get('cleanup_complete') is True and value.get('log_truncated') is False)
    full = prior(full_base/'execution.json')
    full_plan = prior(full_base/'protocol.json')
    require(prepared.get('full'+full_number+'_execution_sha256') == pins[str(full_base/'execution.json')]
        and full.get('passed') is True and full.get('sources_unchanged') is True and success(full['process'])
        and full_plan['tools']['git_head'] == identity['git_head']
        and all(full_plan['source_sha256'].get(name) == pin for name,pin in implementation.items()),
        'current full'+full_number+' source/process binding differs')
    venv = prior(ROOT/('.runs/runtime'+series+'-install-existing-venv-process-001.json'))
    require(success(venv) and venv.get('cwd') == str(runtime)
        and venv.get('argv') == [*f.SANDBOX,prepared['base_python']['path'],'-B','-m','venv',
                                 '--copies','--without-pip',str(runtime/'.venv')]
        and pv.file_digest(runtime/'.venv/bin/python',pv.MAX_ENGINE_BYTES)[0] == prepared['base_python']['sha256'],
        'actual copied interpreter/process differs')
    def cfg(root):
        path = root/'.venv/pyvenv.cfg'
        require(pv.file_digest(path,64*1024)[0] == pins[str(path)], 'copied environment configuration changed')
        return dict(line.strip().split(' = ',1) for line in pv.read_bytes(path,64*1024).decode().splitlines())
    source_cfg,current_cfg = cfg(original),cfg(runtime)
    require(all(current_cfg.get(key) == source_cfg.get(key) for key in
                ('home','version','executable','include-system-site-packages'))
        and current_cfg.get('version') == '3.11.9' and current_cfg.get('include-system-site-packages') == 'false',
        'base interpreter/environment changed')
    doctor = prior(base/'doctor.json')
    require(success(prior(base/'doctor-process.json')) and doctor.get('ready') is True
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
        class_base = ROOT/'.runs/improve-parent-class-runtime062-native-qualification-001'
        master = fixed['.runs/runtime062 fresh install 001/.runs/native7-comparison-parent-class-qualification-001/result.json']
        class_plan = fixed[str((class_base/'protocol.json').relative_to(ROOT))]
        class_execution = fixed[str((class_base/'positive/execution.json').relative_to(ROOT))]
        public = fixed['evidence/runtime062-installed-native-milestone-001.json']
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
            and public.get('qualification',{}).get('passed') is True
            and public['qualification'].get('actual_GUI_qualified') is False
            and public.get('parent_class_control',{}).get('master_sha256') == fixed_pins['.runs/runtime062 fresh install 001/.runs/native7-comparison-parent-class-qualification-001/result.json'],
            'pinned062 public facts differ; summary alone is never qualification')
        require(master.get('control_passed') is True and master.get('status') == 'completed'
            and master.get('accepted') is False and master.get('production_admitted') is False
            and type(master.get('completed_trial_count')) is int and master['completed_trial_count'] == 1
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
            replay_plan = dict(plan,kind=CURRENT40_METHOD_KIND,improve_finalization_reserve_seconds=40)
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
    # Large proof closure is replayed by this adapter before/after the query;
    # only its fixed top bindings enter the bounded32 child prerequisite map.
    closure = hashlib.sha256(f.canonical(dict(dependencies=dependencies,own_finals=proof_facts)).encode()).hexdigest()
    top = {str(ROOT/name):pin for name,pin in fixed_pins.items()}
    top[str(report_source)] = reporter_pin
    cli = [Path(name) for name in tools['files'] if Path(name).name == 'kicad-cli']
    require(len(cli) == 1, 'unique actual pinned Native CLI required')
    local_settings.check_final_events(packets,cli[0],pairs=plot_pairs)
    for name in invalid['completed_evidence']:
        if name.endswith('.kicad_prl'):
            require(local_settings.check_current_metadata(invalid_output/name) is True,
                    'invalid-control PRL metadata changed')
    result = dict(kind=qualification_kind,Native_cohort_only=True,
        runtime=str(runtime),source_head=identity['git_head'],runtime_manifest_sha256=manifest_pin,
        actual_GUI_qualified=False,full_GUI_claim=False,tools_files_sha256=tools['files'],
        finalization_reserve_seconds=40,cohort_cases=13,stored_proof_closure_sha256=closure,
        scope=('Exact installed060/current40 Native CLI prerequisite only; no GUI/electrical/holdout qualification.'
            if not class_mode else 'Exact installed062 parent-class Native CLI follow-up only; no GUI/electrical/holdout qualification.'))
    if class_mode: result.update(parent_class_completed_trials=1,parent_class_invalid_controls=2)
    return result,top


def pinned_json(path, digest):
    require(type(digest) is str and pv._DIGEST.fullmatch(digest), 'exact lowercase SHA256 required')
    path = pv.canonical(Path(path)); raw = pv.read_bytes(path, 4 * 1024**2)
    require(hashlib.sha256(raw).hexdigest() == digest, 'pinned JSON changed: ' + str(path))
    def nonfinite(_): raise ValueError('nonfinite JSON refused')
    value = json.loads(raw, object_pairs_hook=pv._strict_object, parse_constant=nonfinite)
    require(type(value) is dict, 'JSON object required')
    return raw, value


def qualification_dependency(path, pin, version):
    """The current40 closure also pins one Python reporter, not JSON."""
    path = Path(path)
    if version in (CURRENT40_VERSION,PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION) and path == ROOT/'scripts/report_current_comparison.py':
        expected = (CHOICE60_REPORTER_SHA if version == CHOICE60_VERSION else
            REVIEW60_REPORTER_SHA if version == REVIEW60_VERSION else
            PARENT_CLASS_REPORTER_SHA if version == PARENT_CLASS_VERSION else CURRENT40_REPORTER_SHA)
        require(pin == expected and pv.file_digest(path,4*1024**2)[0] == pin,
                'current40 reporter dependency changed')
        return
    pinned_json(path,pin)


def administration(head):
    require(type(head) is str and pv._HEAD.fullmatch(head), 'exact administration HEAD required')
    require(pv.git_head(ROOT) == head, 'administration HEAD changed')
    options = ('-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '--literal-pathspecs')
    names = sorted(ADMIN_FILES)
    require(not pv._git(ROOT, *options, 'status', '--porcelain=v1', '--untracked-files=all', '--', *names),
            'commit exact administration files before freezing')
    rows = pv._git(ROOT, *options, 'ls-tree', '-r', '-l', '-z', head, '--', *names).split(b'\0')
    blobs = {}
    for row in filter(None, rows):
        metadata, name = row.split(b'\t', 1); mode, kind, oid, size = metadata.split()
        require(mode in (b'100644', b'100755') and kind == b'blob' and size.isdigit(), 'ordinary committed administration required')
        blobs[name.decode()] = (oid.decode(), int(size))
    require(set(blobs) == set(names), 'incomplete administration population')
    pins = {}
    for name, (oid, size) in blobs.items():
        raw = pv.read_bytes(ROOT / name)
        require(size == len(raw) and pv._git(ROOT, *options, 'cat-file', 'blob', oid, limit=pv.MAX_FILE_BYTES) == raw,
                'administration differs from committed HEAD: ' + name)
        pins[name] = hashlib.sha256(raw).hexdigest()
    require(pv.git_head(ROOT) == head, 'administration HEAD changed during checks')
    return pins


def sources(spec, runtime):
    require(set(spec) == {'schema', 'split', 'families'} and type(spec['schema']) is int and spec['schema'] == 1
        and spec['split'] == 'development-exposed' and type(spec['families']) is dict
        and 1 <= len(spec['families']) <= 4, 'exact exposed-development source schema required')
    seen = set(); boards = set(); families = set()
    for slug, row in spec['families'].items():
        require(type(slug) is str and re.fullmatch('[a-z][a-z0-9-]{0,31}', slug), 'canonical family slug required')
        require(type(row) is dict and set(row) == {'source', 'source_hashes', 'source_rights', 'publication'}
            and row['publication'] == 'hashes_only' and type(row['source']) is str, 'exact local hashes-only family entry required')
        board = pv.canonical(Path(row['source'])); pv._directory(board.parent)
        require(board.suffix == '.kicad_pcb' and runtime not in board.parents and board.parent.stat().st_uid == os.getuid(),
                'complete owned external PCB project required')
        hashes = row['source_hashes']; rights = row['source_rights']
        require(type(hashes) is dict and 1 <= len(hashes) <= MAX_PROJECT_FILES, 'bounded source population required')
        for name, digest in hashes.items():
            require(type(name) is str and len(name) <= 1024 and '\\' not in name and str(Path(name)) == name
                and not Path(name).is_absolute() and not any(part in ('', '.', '..') for part in name.split('/'))
                and type(digest) is str and pv._DIGEST.fullmatch(digest), 'canonical source path/hash required')
        require(all(board.with_suffix(suffix).name in hashes for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch')),
                'paired complete PCB/PRO/SCH required')
        require(io.inventory(board.parent, max_bytes=MAX_PROJECT_BYTES, max_files=MAX_PROJECT_FILES, max_entries=4000) == hashes,
                'source inventory changed or incomplete')
        require(all((board.parent / name).stat().st_uid == os.getuid() and (board.parent / name).stat().st_nlink == 1
                    for name in hashes), 'owned single-link source files required')
        require(type(rights) is dict and set(rights) == {'family', 'license', 'provenance'}
            and all(type(rights[key]) is str and 1 <= len(rights[key]) <= (256 if key == 'family' else 8192) for key in rights),
                'bounded explicit rights declarations required; not automated clearance')
        require(str(board) not in seen and hashes[board.name] not in boards and rights['family'] not in families,
                'duplicate board or family population')
        seen.add(str(board)); boards.add(hashes[board.name]); families.add(rights['family'])
    return copy.deepcopy(dict(sorted(spec['families'].items())))


def save_new(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    require(len(raw) <= 4 * 1024**2, 'frozen metadata file ceiling')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def query_runtime(runtime, output):
    python = runtime / '.venv/bin/python'; pv.file_digest(python, pv.MAX_ENGINE_BYTES)
    require(os.access(python, os.X_OK), 'copied runtime interpreter required')
    code = ('import json,sys;sys.path.insert(0,' + repr(str(runtime)) + ');'
        'from autorouter import pipeline as p,preferences as pref,handoff as h;'
        'print(json.dumps(dict(runtime=str(p.c.ROOT),interpreter=sys.executable,prefix=sys.prefix,'
        'tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS),handoff_stage_policy=getattr(h,"STAGE_POLICY",None),'
        'delivery_stage_seconds=(dict(review=h.REVIEW_SECONDS,choice=h.CHOICE_SECONDS) if hasattr(h,"STAGE_POLICY") else None)),sort_keys=True))')
    process = run([*f.SANDBOX, str(python), '-B', '-c', code], cwd=output, env=child_environment(),
        log=output/'tools-defaults.json', timeout=30, max_log_bytes=512*1024,
        max_group_rss_bytes=1024**3, max_workdir_bytes=16*1024**2)
    process_pin = save_new(output/'tools-defaults-process.json', process)
    require(process['status'] == 'success' and process['exit_code'] == 0 and process['cleanup_complete'] is True
        and process['log_truncated'] is False and process['log'] == str(output/'tools-defaults.json'), 'runtime query failed/incomplete')
    raw = pv.read_bytes(output/'tools-defaults.json', 512*1024)
    require(type(process['log_bytes']) is int and len(raw) == process['log_bytes'], 'runtime query log size differs')
    log_pin = hashlib.sha256(raw).hexdigest()
    return pinned_json(output/'tools-defaults.json', log_pin)[1], {
        str(output/'tools-defaults.json'): log_pin, str(output/'tools-defaults-process.json'): process_pin}


def freeze(*, runtime, expected_manifest_sha256, sources_path, sources_sha256, qualification,
           qualification_sha256, expected_administration_head, output, enclosure, enclosure_sha256,
           population_version='legacy-v1'):
    population_names, arm_order, population_kind, method_kind, child_name = contract(population_version)
    require(sys.platform == 'darwin', 'this freezer qualifies Mac/selected7 only')
    runtime = pv._directory(Path(runtime)); output = pv.canonical(Path(output)); enclosure = pv.canonical(Path(enclosure))
    require(Path(__file__).resolve() == ROOT/'scripts/freeze_current_comparison.py', 'exact public freezer required')
    require(output.parent == ROOT/'.runs' and output.parent.stat().st_uid == os.getuid()
        and re.fullmatch('[a-z][a-z0-9-]{0,63}', output.name) and not os.path.lexists(output)
        and runtime != output and runtime not in output.parents and output not in runtime.parents, 'fresh canonical administration namespace required')
    expected_enclosure = CHOICE60_ENCLOSURE_SHA if population_version == CHOICE60_VERSION else REVIEW60_ENCLOSURE_SHA if population_version == REVIEW60_VERSION else ENCLOSURE_SHA
    require(enclosure == ROOT/'scripts/enclose_current_comparison.py' and enclosure_sha256 == expected_enclosure
        and pv.file_digest(enclosure)[0] == enclosure_sha256, 'exact public reviewed enclosure required')
    require(pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'owned runtime work directory required')
    raw_sources, spec = pinned_json(sources_path, sources_sha256)
    raw_qualification, qualified = pinned_json(qualification, qualification_sha256)
    manifest_raw, manifest = pinned_json(runtime/pv.MANIFEST, expected_manifest_sha256)
    implementation = {name: pin for name, pin in pv._file_map(manifest.get('immutable_files_sha256')).items() if name.startswith('autorouter/')}
    identity = pv._runtime_identity(runtime, implementation); source_head = identity['git_head']
    qualification_record, qualification_dependencies = qualification_scope(
        qualified, runtime, expected_manifest_sha256, identity, manifest, population_version)
    families = sources(spec, runtime); tracked = administration(expected_administration_head)
    require(shutil.disk_usage(ROOT).free >= 4*1024**3, 'at least4GiB startup headroom required; future jobs have no aggregate quota')
    outputs = {slug: {arm: str(runtime/'.runs'/(
        ('native7-comparison-' if arm.startswith('B') else 'native7-method-') + output.name + '-' + slug + '-' + arm))
        for arm in population_names} for slug in families}
    roots = [Path(value) for row in outputs.values() for value in row.values()]
    extras = {slug: [Path(outputs[slug]['B2_portfolio']+'-portfolio'), *[Path(outputs[slug]['B2_portfolio']+'-portfolio-'+f'{i:02d}-'+v)
        for i,v in enumerate(VARIANTS,1)]] for slug in families}
    roots += [path for row in extras.values() for path in row]
    require(len(set(roots)) == len(roots) and not any(os.path.lexists(pv.canonical(path)) for path in roots), 'fresh distinct population and portfolio roots required')
    child = runtime/'.runs'/child_name; payload = pv.read_bytes(ROOT/'scripts/qualify_current_method.py')
    if os.path.lexists(child):
        require(child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'existing copied controller differs, is unowned or linked')
    output.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, output)
    query, query_pins = query_runtime(runtime, output); tools = query['tools']
    require(query['runtime'] == str(runtime) and query['interpreter'] == str(runtime/'.venv/bin/python')
        and query['prefix'] == str(runtime/'.venv') and query['defaults'] == dict(pref.DEFAULTS)
        and tools['source_provenance'] == identity and tools['implementation_sha256'] == implementation
        and tools['git_head'] == source_head and tools['kicad'] == '10.0.7'
        and tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2', 'actual runtime query/defaults differ')
    require(type(tools.get('files')) is dict and 1 <= len(tools['files']) <= 8, 'bounded actual tool pins required')
    if qualification_record.get('Native_cohort_only') is True:
        require(qualification_record['tools_files_sha256'] == tools['files'], 'Native cohort tools differ from current runtime query')
    if population_version in (PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION):
        from scripts import report_current_comparison as report
        for entry in families.values():
            report.parent_class_source(dict(source=entry['source'],source_hashes=entry['source_hashes'],tools=tools))
    def fresh():
        require(h.owned_destination(owner) == output and administration(expected_administration_head) == tracked, 'administration changed')
        require(pinned_json(sources_path, sources_sha256)[0] == raw_sources and pinned_json(qualification, qualification_sha256)[0] == raw_qualification
            and pv.read_bytes(runtime/pv.MANIFEST, pv.MAX_MANIFEST_BYTES) == manifest_raw
            and pv._runtime_identity(runtime, implementation) == identity and sources(spec, runtime) == families, 'source/qualification/runtime changed')
        require(pv._directory(runtime/'.runs').stat().st_uid == os.getuid(), 'runtime work directory ownership changed')
        for path, pin in query_pins.items(): require(pv.file_digest(Path(path),512*1024)[0] == pin, 'runtime query proof changed')
        for name, pin in tools['files'].items(): require(pv.file_digest(pv.canonical(Path(name)), pv.MAX_ENGINE_BYTES)[0] == pin, 'queried tool bytes changed')
        for name, pin in qualification_dependencies.items(): qualification_dependency(Path(name),pin,population_version)
        if qualification_record.get('Native_cohort_only') is True:
            require(qualification_scope(qualified, runtime, expected_manifest_sha256, identity, manifest, population_version)
                    == (qualification_record, qualification_dependencies), 'Native cohort dependencies changed')
        require(not any(os.path.lexists(path) for path in roots), 'Native outputs appeared before population frozen')
    fresh()
    if not os.path.lexists(child):
        with child.open('xb') as stream: stream.write(payload)
    require(child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'copied controller changed or unowned')
    inputs = {'sources.json': raw_sources, 'qualification.json': raw_qualification}
    for name, raw in inputs.items():
        with (output/name).open('xb') as stream: stream.write(raw)
    defaults = pref.validate(dict(query['defaults'], seconds=420))
    improve_settings = pref.validate(dict(defaults, profile='tuned'))
    population = dict(schema=1, kind=population_kind, population=list(population_names),
        planned_family_order=list(families), planned_arm_order=list(arm_order), runtime=str(runtime),
        runtime_manifest_sha256=expected_manifest_sha256, source_head=source_head, administration_head=expected_administration_head,
        families=families, outputs=outputs, limits=LIMITS, default_settings=defaults, tracked_administration_files_sha256=tracked,
        qualification=dict(path=str(qualification),sha256=qualification_sha256,**qualification_record),
        freezer_sha256=tracked['scripts/freeze_current_comparison.py'], enclosure_sha256=enclosure_sha256,
        policy='B1 corrected standard remains default. Fixed one tuned attempt plus ordered via_default/via_low/via_high balanced portfolio;30inside each trial and15root reserve, no extra budget or board tuning.',
        caveats='All exposed families/failures/warnings retained; rights are declarations, not legal clearance/holdout/independent pedigree. B0 shares fidelity safeguards, not untouched vanilla. API baselines versus actual default/recoverCLI startup differ. Recover420 is whole-method allocation. Every actual outer wall/fullCPU cost includes all startup/conversion/selection/Native/delivery/readback; setup separate. All raw local, publication hashes_only; no publication function or aggregate future-job quota.',
        Native_executed=False,actual_GUI=False,project_complete=False)
    if population_version in ('improve-v2', CURRENT40_VERSION, PARENT_CLASS_VERSION, REVIEW60_VERSION, CHOICE60_VERSION):
        population.update(improve_settings=copy.deepcopy(improve_settings),
            policy='B1 corrected standard remains default. Cimprove uses the shipped single tuned Improve preset;420 includes incumbent/trials and'+str(40 if population_version in (CURRENT40_VERSION,PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION) else 25)+' finalization reserve. Baselines and portfolio policy unchanged.',
            caveats=population['caveats'].replace('Recover420 is whole-method allocation.',
                'Improve420 is whole-method allocation including its incumbent and'+str(40 if population_version in (CURRENT40_VERSION,PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION) else 25)+'-second return reserve; no extra incumbent budget. CLI-installed qualification has no current GUI outcome.'))
    if population_version in (CURRENT40_VERSION,PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION):
        population['improve_finalization_reserve_seconds'] = current40_reserve(runtime,implementation)
    if population_version in (PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION):
        population['improve_parent_class_policy'] = 'native-parent-dimensions-v1'
    if population_version in (REVIEW60_VERSION,CHOICE60_VERSION):
        fields=choice60_stage_fields if population_version == CHOICE60_VERSION else review60_stage_fields
        fields(query)
        population.update(handoff_stage_policy=query['handoff_stage_policy'],delivery_stage_seconds=dict(query['delivery_stage_seconds']))
    population_pin = save_new(output/'population.json', population)
    prerequisite_paths = [Path(sources_path), Path(qualification), runtime/pv.MANIFEST, output/'sources.json', output/'qualification.json',
        output/'population.json', output/'tools-defaults.json', output/'tools-defaults-process.json', child, *[ROOT/name for name in tracked]]
    prerequisites = {str(path): pv.file_digest(path,4*1024**2)[0] for path in prerequisite_paths}
    prerequisites.update(qualification_dependencies)
    require(0 < len(prerequisites) <= 32, 'current prerequisite ceiling exceeded')
    children = {}; admin = {name: tracked[name] for name in ADMIN_FILES[:3]}
    for slug, entry in families.items():
        children[slug] = {}
        for arm in arm_order:
            folder = output/slug/arm; folder.mkdir(parents=True)
            common = dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=expected_manifest_sha256,source_head=source_head,
                tools=copy.deepcopy(tools),source=entry['source'],source_hashes=copy.deepcopy(entry['source_hashes']),source_rights=copy.deepcopy(entry['source_rights']),
                output=outputs[slug][arm],administration_root=str(ROOT),whole_wall_full_cpu_seconds=600,pass_key='controls_passed',
                controller_args=['--runtime',str(runtime)],enclosure_sha256=enclosure_sha256,
                population_protocol_path=str(output/'population.json'),population_protocol_sha256=population_pin,
                scope='Predeclared exposed '+slug+'/'+arm+':420allocation/450method/600completewall+fullCPU/export120; every failure/warning/cost retained, no superiority/GUI/human/electrical claim.')
            if population_version in (REVIEW60_VERSION,CHOICE60_VERSION):
                common.update(handoff_stage_policy=population['handoff_stage_policy'],delivery_stage_seconds=dict(population['delivery_stage_seconds']))
            if arm == 'B2_portfolio':
                plan = dict(common,kind=CHOICE60_PORTFOLIO_KIND if population_version == CHOICE60_VERSION else REVIEW60_PORTFOLIO_KIND if population_version == REVIEW60_VERSION else 'installed-native7-comparison-portfolio-functional-v1',**LIMITS,variants=list(VARIANTS),allocation='balanced',
                    trial_readback_reserve_seconds=30,root_finalization_reserve_seconds=15,installed_trial_accounting_policy='installed-route-readback-reserve-v1',
                    comparison_api_policy='installed-native7-scored-portfolio-api-v2',administration_head=expected_administration_head,administration_files_sha256=admin,
                    family=entry['source_rights']['family'],controller=str(ROOT/ADMIN_FILES[0]),controller_sha256=admin[ADMIN_FILES[0]],
                    portfolio_output=str(extras[slug][0]),material_roots=[str(path) for path in extras[slug]])
            else:
                plan = dict(common,kind=method_kind,arm=arm,population=list(population_names),outputs=outputs[slug],
                    controller=str(child),controller_sha256=tracked['scripts/qualify_current_method.py'],qualifier_sha256=tracked['scripts/qualify_installed_workflow.py'],
                    source_inventory_sha256=hashlib.sha256((f.canonical(entry['source_hashes'])+'\n').encode()).hexdigest(),
                    source_rights_sha256=hashlib.sha256(f.canonical(entry['source_rights']).encode()).hexdigest(),
                    prerequisite_sha256=prerequisites,default_settings=copy.deepcopy(defaults),limits=dict(LIMITS))
                if population_version in ('improve-v2', CURRENT40_VERSION, PARENT_CLASS_VERSION, REVIEW60_VERSION, CHOICE60_VERSION): plan['improve_settings'] = copy.deepcopy(improve_settings)
                if population_version in (CURRENT40_VERSION,PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION): plan['improve_finalization_reserve_seconds'] = 40
            if population_version in (PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION) and arm != 'B2_portfolio':
                plan['improve_parent_class_policy'] = 'native-parent-dimensions-v1'
            path = folder/'protocol.json'; children[slug][arm] = dict(path=str(path),sha256=save_new(path,plan))
    fresh(); require(child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'copied controller changed or unowned at final freeze')
    for rows in children.values():
        for item in rows.values(): require(pv.file_digest(Path(item['path']),4*1024**2)[0] == item['sha256'], 'derived protocol changed')
    for path,pin in prerequisites.items(): require(pv.file_digest(Path(path),4*1024**2)[0] == pin, 'frozen prerequisite changed')
    record = dict(schema=1,population_path=str(output/'population.json'),population_sha256=population_pin,protocols=children,
        administration_head=expected_administration_head,policy_or_board_changes_after_first_arm=False,project_complete=False,
        sampled_setup_wall_seconds=time.monotonic()-START,sampled_setup_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True)
    final_pin = save_new(output/'frozen-children.json',record)
    fresh()
    require(pv.file_digest(output/'frozen-children.json',4*1024**2)[0] == final_pin
        and child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload, 'final freeze or copied controller changed')
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population-version', choices=('legacy-v1','improve-v2',CURRENT40_VERSION,PARENT_CLASS_VERSION,REVIEW60_VERSION,CHOICE60_VERSION), default='legacy-v1')
    for name in ('runtime','sources','qualification','output','enclosure'): parser.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-manifest-sha256','sources-sha256','qualification-sha256','expected-administration-head','enclosure-sha256'):
        parser.add_argument('--'+name,required=True)
    args=vars(parser.parse_args(argv)); args['sources_path']=args.pop('sources')
    try: print(json.dumps(freeze(**args))); return 0
    except (ValueError,OSError,p.Rejected) as exc: print('Comparison freeze refused: '+str(exc),file=sys.stderr); return 2


if __name__=='__main__': raise SystemExit(main())
