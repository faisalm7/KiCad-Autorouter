"""Prospective curator. DO NOT RUN until the lead confirms stable/review-resolved.

Requires an explicit owned freeze JSON with schema=1, source_stable=true,
review_resolved=true, review_sha256, and source_sha256 for exactly SOURCES.
No source bytes are captured merely by authoring this script. It performs no
Native, test, build, GUI, network or Git execution.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, re, sys

SOURCES = {
    'autorouter/default_targets.py', 'autorouter/native.py', 'autorouter/netclass.py',
    'autorouter/netclass_native.py', 'autorouter/pipeline.py', 'autorouter/review_export.py',
    'tests/test_default_target_integration.py', 'tests/test_default_targets.py',
    'tests/test_netclass_native.py',
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze-confirmation', type=Path, required=True)
    args = parser.parse_args()
    global ROOT, notes, refs, files, material, total, p, f, io
    ROOT = Path(__file__).resolve().parents[2]
    notes = Path(__file__).resolve().parent
    output = ROOT / 'evidence/default-targets-implicit-resolution-003.json'
    assert not output.exists()
    assert sorted(q.name for q in notes.iterdir()) == ['curate.py']
    confirmation = args.freeze_confirmation.resolve(strict=True)
    assert confirmation.is_relative_to(ROOT / '.runs') and not args.freeze_confirmation.is_symlink()
    assert confirmation.stat().st_size <= 16384
    freeze = json.loads(confirmation.read_bytes())
    assert set(freeze) == {'schema', 'source_stable', 'review_resolved', 'review_sha256', 'source_sha256'}
    assert type(freeze['schema']) is int and freeze['schema'] == 1
    assert freeze['source_stable'] is True and freeze['review_resolved'] is True
    assert type(freeze['source_sha256']) is dict and set(freeze['source_sha256']) == SOURCES
    assert all(type(x) is str and re.fullmatch('[0-9a-f]{64}', x)
               for x in [freeze['review_sha256'], *freeze['source_sha256'].values()])
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / '.runs/runtime-directory-037/runtime'))
    from autorouter import pipeline, floor_route, placement_clearance
    p, f, io = pipeline, floor_route, placement_clearance
    helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
    assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
    definitions = [n for n in ast.parse(helper.read_bytes()).body if isinstance(n, ast.FunctionDef)
                   and n.name in {'retain', 'tree', 'cost'}]
    assert {n.name for n in definitions} == {'retain', 'tree', 'cost'}
    refs = {}; files = []; material = []; total = 0
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(helper), 'exec'), globals())

    dependencies = []
    for name, expected in [
        ('evidence/default-targets-integration-correction-002.json', '49990479ac677638f5bee214ea22c16350ef5ccf7fe5c05580b4837f6b024c60'),
        ('evidence/default-targets-full181-001.json', '32a00ddcfda35daa3956fb74343c499f291925117605eb83634f092b20cd2bf3'),
        ('evidence/gui-runtime037-077-positive-001.json', 'f5d13e8b9e6946b8e9c4d4404503d2e74a409693dc1374224baff988ea50bfd4'),
    ]:
        q = ROOT / name
        assert p.sha(q) == expected
        j = f.read_json(q); idx = ROOT / j['files_index']['path']
        assert p.sha(idx) == j['files_index']['sha256']
        x = f.read_json(idx)
        for row in x.get('files', []): refs.setdefault(row['sha256'], row['path'])
        for row in x.get('material', []): refs.setdefault(row['sha256'], row['retained'])
        dependencies.append(dict(path=name, sha256=expected, files_index=j['files_index']))

    review = ROOT / '.runs/default-targets-implicit-review-001.json'
    assert review.is_file() and not review.is_symlink()
    assert p.sha(review) == freeze['review_sha256']
    review_record = f.read_json(review)
    for name, digest in freeze['source_sha256'].items():
        assert review_record['source_pins'][name]['sha256'] == digest
        assert review_record['source_pins'][name]['bytes'] == (ROOT / name).stat().st_size
    selected = [(confirmation, Path('proof/freeze-confirmation.json')),
                (review, Path('proof') / review.name)]
    license_sha = '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986'
    license_path = refs[license_sha]
    assert p.sha(ROOT / license_path) == license_sha
    selected.append((ROOT / license_path, Path('rights/LICENSE')))
    for name in sorted(SOURCES):
        q = ROOT / name
        assert p.sha(q) == freeze['source_sha256'][name]
        selected.append((q, Path('source') / name))
    tests = []
    for label, count, wall, cpu in [
        ('implicit-targeted-001', 38, 1.63, 1.35),
        ('native-scalars-001', 10, .08, .05),
        ('netclass-regression-001', 21, 2.53, 2.39),
    ]:
        log = ROOT / '.runs' / ('default-targets-' + label + '.log')
        time_log = ROOT / '.runs' / ('default-targets-' + label + '-time.log')
        text = time_log.read_text()
        match = re.findall(r'^Ran (\d+) tests in ([\d.]+)s$', text, re.M)
        assert len(match) == 1 and int(match[0][0]) == count
        assert re.findall(r'^OK$', text, re.M) == ['OK']
        measured = cost(time_log)
        assert measured == dict(wall_seconds=wall, CPU_seconds=cpu)
        assert log.read_bytes() == b''
        selected += [(log, Path('targeted-tests') / log.name),
                     (time_log, Path('targeted-tests') / time_log.name)]
        tests.append(dict(case=label, tests=count, passed=True,
            unittest_seconds=float(match[0][1]), complete_external_cost=measured,
            stdout_empty=True, unittest_and_time_output='retained -time.log',
            scope='Constructed source controls; not Native qualification.'))

    # Finite, all-or-nothing payload preflight before the first copied byte.
    secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
    new = {}
    for q, name in selected:
        assert q.is_file() and not q.is_symlink()
        raw = io.read_bytes(q, 4 * 1024**2)
        assert b'\0' not in raw and not secret.search(raw)
        raw.decode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        if digest not in refs: new.setdefault(digest, len(raw))
    assert sum(new.values()) + 256 * 1024 < 16 * 1024**2
    for q, name in selected: retain(q, name)
    assert p.sha(review) == freeze['review_sha256']
    for name, digest in freeze['source_sha256'].items(): assert p.sha(ROOT / name) == digest

    scope = '''# Implicit Default resolution003: source/constructed controls only

This additive packet freezes nine source/test files only after explicit lead
confirmation that the source is stable and the independent AI review is resolved.
The raw review and confirmation remain visible. It does not rewrite correction002,
full181, the failed Mixer trial, or immutable runtime037's GUI-positive evidence.
Every one of the nine final source pins matches the independently retained review.
That review identifies an absent-only detached project normalization, same-load
Native floor observations, and v2 original/final/export observation binding. It
does not establish that actual selected7 implicit parent/getter values pass.
Each targeted invocation retains its real empty stdout and combined unittest/time
stderr. Counts are separate invocations, not disjoint test coverage or Native proof.
The raw targeted logs have no independent source-stability manifest; final bytes
are pinned at freeze, and association with these controls is bounded accordingly.

Full181 passed at historical f54 but did not cover the later implicit-Default
compatibility blocker. These v2 source changes/constructed controls alone do not
qualify an installed runtime, actual same-load Native observations, Native scalar
readback, route/export, GUI, Windows, family improvement, or product support.
Old GUI037 positive proof stays bound to immutable c3e7/c1ef and is not promoted
to this changed build. Review is AI review, not human PCB/electrical/physical review.

Only project-owned code/tests and explicit owned test/review metadata are selected;
repository GPL LICENSE is an exact verified dependency payload link. Prior notices
remain through the dependency packets.
No private boards/browser data, downloaded tools, caches, or unrelated archive
payload is read/copied. Raw originals remain unmodified. No Native, tests, builds,
GUI, CI, network or Git execution occurs in this curator. Authoring/curation CPU
is additional unmetered, notzero. This text packet is not a full backup/restoration.
'''
    with (notes / 'SCOPE.md').open('x') as stream: stream.write(scope)
    for q in [Path(__file__), notes / 'SCOPE.md']:
        raw = q.read_bytes()
        files.append(dict(path=str(q.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        total += len(raw)
    for row in material:
        assert p.sha(ROOT / row['original']) == row['sha256'] == p.sha(ROOT / row['retained'])
    p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material,
        preflight=dict(max_file_bytes=4 * 1024**2, packet_ceiling_bytes=16 * 1024**2,
            selected_material_secret_pattern_check=True, UTF8_no_NUL=True,
            selected_material_occurrences=len(selected), new_unique_bytes=sum(new.values()))))
    summary = dict(schema=1, kind='implicit-Default-v2-source-and-constructed-controls',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        accepted=False, routing_accepted=False, production_qualified=False,
        installation_qualified=False, Native_qualified=False, actual_GUI=False,
        project_complete=False, human_review=False, physical_electrical_validation=False,
        source_sha256=freeze['source_sha256'], targeted_invocations=tests,
        independent_AI_review=dict(original=str(review.relative_to(ROOT)), sha256=p.sha(review),
            lead_confirmed_resolved=True, final_nine_source_pins_match=True,
            findings=review_record['findings'], conclusion=review_record['conclusion'],
            human_review=False),
        source_freeze=dict(original=str(confirmation.relative_to(ROOT)), sha256=p.sha(confirmation),
            lead_confirmed_stable=True, source_hashes_checked_before_and_after_copy=True),
        test_binding_limit='Targeted logs preserve actual outcomes/costs but contain no independent source-stability manifest. Final source bytes were captured only at this confirmed freeze.',
        prior_result_scope='Full181 is historical f54 source tests; GUI037 is the immutable c3e7/c1ef one-positive path. Neither qualifies these changed bytes.',
        authored_findings=[
            'The source review reports absent-only Default/rule resolution in a detached project copy, preserving raw source bytes and refusing malformed present fields.',
            'The source review reports same-load five-floor integer observations and unanimous Default/parent scalar checks; actual selected7 getter/parent behavior remains a Native prerequisite.',
            'The source review reports required v2 transport and original/final/fresh-export dimension binding. These are static/constructed-control findings, not demonstrated Native admission.'],
        remaining=['Fresh full suite and isolated install for final bytes',
            'Actual same-load selected7 Native absent-field/scalar observations and ordinary Route/export/invalid controls',
            'Fresh GUI controls for a changed build; independent-family effectiveness and other project release gates'],
        accounting='Each complete external targeted cost is retained separately. Test invocations may overlap; no disjoint-coverage or Native inference. Review/authoring/curation costs additional unmetered, notzero.',
        dependencies=dependencies,
        rights=dict(license='Repository GPL; project-owned source/tests and owned test metadata.',
            retained_LICENSE=license_path, LICENSE_sha256=license_sha,
            private_inputs_or_downloaded_tools_published=False),
        curation_helper=dict(path=str(helper.relative_to(ROOT)), sha256=p.sha(helper)),
        retention=dict(new_payload_files=len(files), new_payload_bytes=total,
            material_occurrences=len(material), source_files=9,
            no_original_edits=True, no_Native_tests_build_GUI_CI_network_Git_execution=True),
        files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
    p.save_json(output, summary)
    physical = [q for q in notes.rglob('*') if q.is_file()] + [output]
    assert sum(q.stat().st_size for q in physical) < 16 * 1024**2
    for row in files: assert p.sha(ROOT / row['path']) == row['sha256']
    print(json.dumps(dict(path=str(output.relative_to(ROOT)), sha256=p.sha(output),
        files_index_sha256=p.sha(notes / 'files.json'), physical_files=len(physical),
        physical_bytes=sum(q.stat().st_size for q in physical), Native_qualified=False), sort_keys=True))

if __name__ == '__main__':
    main()
