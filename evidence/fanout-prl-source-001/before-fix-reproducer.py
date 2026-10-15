#!/usr/bin/env python3
"""Prospective pre-fix free-angle/None metadata reproducer; no Native tools.

Run only through the lead's bounded120s/1GiB runner. The synthetic fixture's
accepted receipt is the defect under observation, NEVER routing acceptance.
Existing test helpers require an owned ROOT/.cache/result-tests directory;
raw bytes are copied to OUT unchanged before that temporary directory closes.
Copied absolute journal paths are diagnostic history, not rebased/replayable
Native evidence. Tool discovery and accounting are explicit seams; root's
outer runner measures complete real wall/CPU and enforces process resources.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.runs/fanout-prl-prefix-reproducer-001'
PINS={
    'autorouter/pipeline.py':'9eb4c169061d3a6f184bf4cab7cc9878280b9de9dec18e49fba117f2e16dec64',
    'autorouter/floor_route.py':'eaec4f7046c7e1284bb74f709a9c82b50ceb0cbd0a11c1bdf4ae4804914e5ecc',
    'autorouter/local_settings.py':'a2ab6296b637ace500f1cdbdd62de0cd9c1803cfc17e38906ced497c1aef21c8',
    'autorouter/engine_angle.py':'900f5f7e34e25a03220664951df4e978327a02628ae0203008093e34b78b8bb0',
    'autorouter/placement_clearance.py':'8fa82414fa40f80d90ed4a42f53fa2e679a52d74cfb4cfa9038239f1217aaff6',
    'tests/test_result.py':'5bd6f37c64aed0756b7b77b5cbd01e2674f695f34d71fb7cd55f7b8287cbb3df',
    'tests/test_normal_local_settings_policy.py':'1132273f80f51753b722f75b7d6ced001cc33742d9fc3e867542073cadaea892',
    'tests/normal_prl_fixture.py':'752f4800dc021d72e0703ab77e1bef65365bfcf12fbe21f11b09f6b08e07bd73',
}
STABLE_AST='ce1fd89d97eb5d44b089e259533858772b05ad4360f5190033f0d21ee97aad57'


def require(value,message):
    if not value:raise AssertionError(message)


def pins_current():
    actual={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in PINS}
    require(actual==PINS,'current source/test helper pins differ from frozen pre-fix producer')
    return actual


def run():
    started=time.monotonic();cpu_started=time.process_time();case=None;target=None;old_flags=None;cancelled=None
    require(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac flags required; no emulated flag outcome')
    require(ROOT==ROOT.resolve() and not any(p.is_symlink() for p in (OUT,*OUT.parents)),'canonical exclusive output required')
    require(not OUT.exists(),'fresh output required')
    before=pins_current();OUT.mkdir()
    sys.path.insert(0,str(ROOT))
    from autorouter import pipeline as p,floor_route as f,local_settings as ls,engine_angle as angle,placement_clearance as pc
    from tests import test_result as receipt_fixture,test_normal_local_settings_policy as prl_fixture
    require(p.c.ROOT==ROOT,'imports escaped selected checkout')
    record=dict(schema=1,status='failed',passed=False,observed_defect=False,routing_native_evidence=False,
                purpose='observe pre-fix accepted synthetic receipt despite late immutable PRL flags',
                source_sha256=before,stable_ast_sha256=STABLE_AST,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                limits=dict(worker_wall_seconds=120,worker_rss_bytes=1024**3,fixture_bytes=32*1024**2,fixture_files=2000),
                scope='software metadata consistency only; authored Native/process reports never executed',
                seams=['frozen synthetic tool manifest','no-op summary account and100-second availability','actual hash followed by flag fault','resultchecker replays profile+PRL only'],
                resource_scope='parent whole runner authoritative; these samples exclude final serialization/tail',
                output=str(OUT),temporary_fixture=None)
    try:
        # Existing owned support setup, not unittest discovery or tool execution.
        case=receipt_fixture.ResultFreshnessTests('runTest');case.setUp()
        prl_fixture.NormalPolicyReceiptControls._put_prl_in_fixture(case)
        record['temporary_fixture']=str(case.root)
        rows=[s for s in case.data['steps'] if s.get('name')=='engine' and s.get('cwd')==str(case.run)]
        require(len(rows)==1 and f.read_json(case.run/'engine-process.json')==rows[0],'expected one existing authored engine')
        require([rows[0][k] for k in ('wall_seconds','cpu_seconds','monitor_cpu_seconds')]==[0,0,0],'only zero-cost authored setup may be replaced')
        # Deliberately use ONLY APIs available in the actual pre-fix source.
        budget=p.engine_profile_settings(angle.PROFILE,119,scoring_variant='via_default',experimental_free_angle=True)
        budget.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
        worker=copy.deepcopy(rows[0]);worker['argv']=p.engine_argv(case.run,budget['argv'],profile=angle.PROFILE)
        case.data['steps']=[worker if row is rows[0] else row for row in case.data['steps']]
        p.save_json(case.run/'engine-process.json',worker)
        case.data.update(engine_profile=angle.PROFILE,baseline=p.engine_baseline(angle.PROFILE,'both'),adapter='both',
                         scoring_variant='via_default',engine_budget=budget,engine_angle_binding=angle.prepare(case.run))
        case.save_receipt()
        source=ROOT/'autorouter/pipeline.py';raw=source.read_bytes()
        require((case.run/'code/pipeline.py').read_bytes()==raw and case.data['tools']['implementation_sha256']['autorouter/pipeline.py']==PINS['autorouter/pipeline.py'],'captured pipeline context differs')
        producer=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='route')
        closures=[n for n in ast.walk(producer) if isinstance(n,ast.FunctionDef) and n.name=='stable']
        require(len(closures)==1,'exact one actual route.stable required')
        require(hashlib.sha256(ast.dump(closures[0],include_attributes=False).encode()).hexdigest()==STABLE_AST,'stable AST differs')
        pc.inventory(case.root,max_bytes=32*1024**2,max_files=2000,max_entries=4000)
        target=case.run/'final-drc-input'/case.source.with_suffix('.kicad_prl').name
        old_flags=target.stat().st_flags;prl_raw=target.read_bytes();require(old_flags==0,'owned PRL must start without flags')
        inventory=f.evidence_inventory(case.run);state={'readbacks':0,'triggered':False};hash_tree=p.tree_hash
        def current_hash(path):
            value=hash_tree(path)
            if state['readbacks'] and Path(path)==case.run/'snapshot' and not state['triggered']:
                os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False)
                state['triggered']=True
                require(target.stat().st_flags & stat.UF_IMMUTABLE,'real flag mutation absent')
                require(target.read_bytes()==prl_raw and f.evidence_inventory(case.run)==inventory,'flag-only mutation changed bytes')
            return value
        def readback(path):
            require(Path(path)==case.receipt,'unexpected synthetic receipt path')
            data=f.read_json(path)
            p.check_engine_profile_record(data,case.run)
            ls.check_normal_policy(case.run,data)
            state['readbacks']+=1
        env=dict(p.__dict__)
        env.update(report=case.data,output=case.run,source=case.source,before=hash_tree(case.source_dir),
                   completed=inventory,native_toolchain=None,_preferences=None,engine_profile=angle.PROFILE,
                   tool_manifest=lambda **kw:case.data['tools'],evidence_inventory=f.evidence_inventory,tree_hash=current_hash)
        # No modified AST node or copied substitute callback body.
        exec(compile(ast.fix_missing_locations(ast.Module(body=closures,type_ignores=[])),str(source),'exec'),env)
        result=f.publish(case.run,case.data,env['stable'],lambda:None,lambda:100,result_checker=readback)
        if result.get('status')=='cancelled':raise KeyboardInterrupt('shared publisher cancelled')
        stored=case.receipt.read_bytes();stored_data=json.loads(stored)
        flag_at_return=target.stat().st_flags
        record.update(state=state,prl_sha256=hashlib.sha256(prl_raw).hexdigest(),flags_at_return=flag_at_return,
                      returned_accepted=result.get('accepted'),stored_accepted=stored_data.get('accepted'),
                      retained_bytes_unchanged=f.evidence_inventory(case.run)==inventory,
                      synthetic_receipt_sha256=hashlib.sha256(stored).hexdigest(),source_current=pins_current())
        # Preserve the exact falsely accepted synthetic receipt, not a repaired one.
        (OUT/'accepted-synthetic-receipt.json').write_bytes(stored)
        (OUT/'owned-prl-bytes.kicad_prl').write_bytes(prl_raw)
        p.save_json(OUT/'retained-before-byte-inventory.json',inventory)
        require(state=={'readbacks':1,'triggered':True},'required late-read sequence not reached')
        require(result.get('accepted') is True and stored_data.get('accepted') is True,'old pre-fix stale acceptance not observed')
        require(flag_at_return & stat.UF_IMMUTABLE and record['retained_bytes_unchanged'],'expected final immutable flag with identical bytes absent')
        record.update(status='observed_defect',passed=True,observed_defect=True)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',passed=False,error=type(exc).__name__+': '+str(exc))
        if isinstance(exc,KeyboardInterrupt):cancelled=exc
    finally:
        try:
            if target is not None and old_flags is not None:
                os.chflags(target,old_flags,follow_symlinks=False)
                require(target.stat().st_flags==old_flags,'owned PRL flags did not restore')
                record['flags_restored']=True
            if case is not None:
                # Diagnostic raw copy only: retain original paths verbatim.
                material=pc.inventory(case.root,max_bytes=32*1024**2,max_files=2000,max_entries=4000)
                shutil.copytree(case.root,OUT/'fixture-bytes',copy_function=shutil.copyfile)
                require(pc.inventory(OUT/'fixture-bytes',max_bytes=32*1024**2,max_files=2000,max_entries=4000)==material,'retained diagnostic byte copy differs')
                record['fixture_byte_inventory']=material
                record['fixture_copy_scope']='exact raw bytes; flags restored; absolute paths unchanged; not independently replayable Native evidence'
            record['source_current']=pins_current()
        except (Exception,KeyboardInterrupt) as exc:
            record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',passed=False,error=type(exc).__name__+': '+str(exc))
            if isinstance(exc,KeyboardInterrupt):cancelled=exc
        finally:
            if case is not None:case.doCleanups()
        record.update(sampled_wall_seconds=time.monotonic()-started,sampled_parent_cpu_seconds=time.process_time()-cpu_started)
        p.save_json(OUT/'result.json',record)
    if cancelled is not None:raise cancelled
    return 0 if record['passed'] else 1


def main():
    # Scoped only to this diagnostic: cancellation must reach owned PRL cleanup.
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def cancel(signum,frame):raise KeyboardInterrupt('received signal '+str(signum))
    try:
        for sig in previous:signal.signal(sig,cancel)
        return run()
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)


if __name__=='__main__':raise SystemExit(main())
