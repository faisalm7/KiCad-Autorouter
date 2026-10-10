#!/usr/bin/env python3
"""Actual native class controls on a previously accepted interf_u project.

Execution is explicit, sequential, offline
at native-worker level, and limited to complete disposable project copies.
No solver is launched. Unit-test or mocked counts cannot qualify these controls.
"""
import argparse
import copy
from decimal import Decimal
import json
from pathlib import Path
import resource
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autorouter import config as c, pipeline as p, sexpr as sx


def cpu_total():
    own=resource.getrusage(resource.RUSAGE_SELF)
    child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime


class OfflineJob(p.Job):
    def step(self,name,argv,allowed=(0,)):
        return super().step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],allowed)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',required=True,help='Accepted interf_u result.json retained under .runs')
    parser.add_argument('--output',required=True,help='New direct child of this checkout .runs')
    parser.add_argument('--seconds',type=float,default=180)
    args=parser.parse_args()
    if not 30<=args.seconds<=180: raise p.Rejected('Control budget must be 30–180 seconds')
    runs=ROOT/'.runs'
    receipt=Path(args.receipt).absolute()
    output=Path(args.output).absolute()
    if runs.is_symlink() or output.is_symlink() or output.parent!=runs or output.exists():
        raise p.Rejected('Output must be a new direct child of real project .runs')
    if receipt.name!='result.json' or not receipt.is_relative_to(runs) or receipt.resolve()!=receipt:
        raise p.Rejected('Expected canonical local .runs result.json')
    started,cpu_started=time.monotonic(),cpu_total()
    verified=p.check_result(receipt)
    prior=json.loads(receipt.read_text())
    valid=Path(verified['candidate'])
    source=Path(prior['source'])
    if source.name!='interf_u.kicad_pcb' or p.netclass_policy(source) is None:
        raise p.Rejected('This control protocol requires qualified interf_u')
    original=sx.read(source)
    protected=[route for route in p.routes(original) if prior['scope']=='partial_completion' or p.locked(route)]
    source_before=p.tree_hash(source.parent)
    accepted_before=p.tree_hash(valid.parent)
    receipt_before=p.sha(receipt)
    map_path=receipt.parent/'final-netclasses.json'
    native_map=json.loads(map_path.read_text())
    project=json.loads(source.with_suffix('.kicad_pro').read_text())
    tools=p.tool_manifest()
    p.check_storage()
    output.mkdir()
    shutil.copy2(__file__,output/'native_class_controls.py')
    shutil.copy2(receipt,output/'accepted-receipt.json')
    shutil.copy2(map_path,output/'accepted-native-map.json')
    shutil.copytree(source.parent,output/'original-snapshot')
    shutil.copytree(valid.parent,output/'accepted-snapshot')
    code=output/'code';code.mkdir()
    for relative,digest in tools['implementation_sha256'].items():
        shutil.copy2(ROOT/relative,code/Path(relative).name)
        if p.sha(code/Path(relative).name)!=digest: raise p.Rejected('Implementation changed during freeze')
    deadline=started+args.seconds
    summary={'schema':1,'experiment':'native effective-netclass dimension controls','mocked_native_execution':False,
             'human_review':False,'physical_electrical_validation':False,'solver_executed':False,
             'source':str(source),'source_hashes':source_before,'accepted_receipt':str(receipt),
             'accepted_receipt_sha256':receipt_before,'accepted_candidate_sha256':verified['candidate_sha256'],
             'tools':tools,'budget_seconds':args.seconds,'cpu_budget_seconds':args.seconds,
             'cpu_enforcement':'post-completion accounting cap, not hard CPU preemption',
             'script_sha256':p.sha(Path(__file__)),
             'control_setup_timing':'includes source validation and initial artifact copies',
             'controls':[],'all_passed':False}

    def assert_immutable_inputs():
        if (p.tree_hash(source.parent)!=source_before or p.tree_hash(valid.parent)!=accepted_before
                or p.sha(receipt)!=receipt_before or p.tree_hash(output/'original-snapshot')!=source_before
                or p.tree_hash(output/'accepted-snapshot')!=accepted_before):
            raise p.Rejected('Original, accepted evidence, or immutable snapshot changed')
        for relative,digest in tools['implementation_sha256'].items():
            if p.sha(ROOT/relative)!=digest: raise p.Rejected('Active implementation changed')

    def select_route(tree,kind):
        native={row['name']:row for row in native_map['nets']}
        names={node[1]:sx.unquote(node[2]) for node in sx.children(tree,'net')}
        choices=[]
        for route in p.routes(tree):
            if route[0]!=kind or route in protected: continue
            atom=sx.one(route,'net')[1]
            row=native.get(names.get(atom,sx.unquote(atom)))
            if row: choices.append((route,row))
        if not choices: raise p.Rejected('No unprotected '+kind+' available for this control')
        choices.sort(key=lambda item:(item[1]['class']=='Default',sx.dump(item[0])))
        return choices[0]

    positive_native=None
    try:
        for case in ('positive','below_target_track','wrong_via_diameter','wrong_via_drill'):
            assert_immutable_inputs()
            remaining=min(deadline-time.monotonic(),args.seconds-(cpu_total()-cpu_started))
            if remaining<5: raise p.Rejected('Whole control budget exhausted')
            job=OfflineJob(output/case,min(40,remaining))
            candidate=job.out/'candidate'/source.name
            shutil.copytree(valid.parent,candidate.parent)
            tree=sx.read(candidate)
            entry={'case':case,'expected_accepted':case=='positive','accepted':False,'passed':False}
            if case!='positive':
                route,row=select_route(tree,'segment' if case=='below_target_track' else 'via')
                key,target_key,floor_key=(('width','width_nm','min_track_width') if case=='below_target_track' else
                    ('size','via_diameter_nm','min_via_diameter') if case=='wrong_via_diameter' else
                    ('drill','via_drill_nm','min_through_hole_diameter'))
                target=row[target_key]
                floor=int(Decimal(str(project['board']['design_settings']['rules'][floor_key]))*1000000)
                changed=(target+floor)//2
                if not floor<changed<target: raise p.Rejected('No above-floor below-target dimension available')
                before=copy.deepcopy(route)
                sx.one(route,key)[1]=format(Decimal(changed)/1000000,'f')
                sx.write(candidate,tree)
                entry['mutation']={'native_net':row['name'],'class':row['class'],'dimension':key,
                                   'native_target_nm':target,'original_floor_nm':floor,'changed_nm':changed,
                                   'original_route':before,'changed_route':copy.deepcopy(route)}
            entry['candidate_before_sha256']=p.sha(candidate)
            try:
                entry['diagnostic_native']=job.drc('diagnostic-drc',candidate)
                entry['diagnostic_native_report_sha256']=p.sha(job.out/'diagnostic-drc.json')
                entry['diagnostic_native_clean_routing']=not any(entry['diagnostic_native'][key] for key in ('opens','blocking','exclusions'))
            except Exception as exc:
                entry['diagnostic_error']=type(exc).__name__+': '+str(exc)
            if any(step.get('status')=='cancelled' for step in job.steps): raise KeyboardInterrupt
            entry['native_execution_proven']=(job.out/'diagnostic-drc.json').is_file() and any(
                step['name']=='diagnostic-drc' and step['exit_code'] in (0,5) and step['cleanup_complete'] for step in job.steps)
            try:
                digest,native=p.validate_candidate(job,original,candidate,source_before,protected)
                entry.update(candidate_sha256=digest,native=native,native_report_sha256=p.sha(job.out/'final-drc.json'))
                entry['accepted']=not any(native[key] for key in ('opens','blocking','exclusions'))
                if case=='positive' and entry['accepted']:
                    positive_native=json.loads((job.out/'final-netclasses.json').read_text())
            except Exception as exc:
                entry['rejection']=type(exc).__name__+': '+str(exc)
            if any(step.get('status')=='cancelled' for step in job.steps): raise KeyboardInterrupt
            expected_rejection=('generated track differs from native netclass target' if case=='below_target_track' else
                                'generated via differs from native netclass target')
            target_rejected=expected_rejection in entry.get('rejection','')
            entry['passed']=entry['native_execution_proven'] and (entry['accepted'] if case=='positive' else target_rejected)
            entry['steps']=job.steps
            entry['candidate_after_sha256']=p.sha(candidate)
            assert_immutable_inputs()
            p.save_json(job.out/'control.json',entry)
            summary['controls'].append(entry)
            print(case, 'PASS' if entry['passed'] else 'FAIL',flush=True)

        if positive_native is None: raise p.Rejected('Positive native validation did not pass; forged-map controls cannot qualify')
        positive_candidate=output/'positive/candidate'/source.name
        for case in ('tampered_native_width','native_Default_fallback'):
            altered=copy.deepcopy(positive_native)
            row=next((row for row in altered['nets'] if row['class']!='Default'),None)
            if row is None: raise p.Rejected('No native nondefault row available')
            if case=='tampered_native_width': row['width_nm']-=1000
            else:
                default=next(cls for cls in project['net_settings']['classes'] if cls['name']=='Default')
                row['class']='Default'
                for native_key,key in (('width_nm','track_width'),('clearance_nm','clearance'),('via_diameter_nm','via_diameter'),('via_drill_nm','via_drill')):
                    row[native_key]=int(Decimal(str(default[key]))*1000000)
            folder=output/case;folder.mkdir()
            p.save_json(folder/'forged-native-map.json',altered)
            entry={'case':case,'expected_accepted':False,'native_execution_proven':True,
                   'native_evidence':str(output/'positive/final-netclasses.json'),
                   'native_evidence_sha256':p.sha(output/'positive/final-netclasses.json'),
                   'forged_map_sha256':p.sha(folder/'forged-native-map.json'),'accepted':False,'passed':False,
                   'qualification':'Actual positive native map then local JSON tamper; no fabricated native execution'}
            try:
                p.audit_candidate_netclasses(positive_candidate,protected,altered)
                entry['accepted']=True
            except Exception as exc:
                entry['rejection']=type(exc).__name__+': '+str(exc)
                expected='differs from original project value' if case=='tampered_native_width' else 'differs from admitted literal assignment'
                entry['passed']=expected in str(exc)
            p.save_json(folder/'control.json',entry)
            summary['controls'].append(entry)
            print(case, 'PASS' if entry['passed'] else 'FAIL',flush=True)
        assert_immutable_inputs()
        summary['all_passed']=len(summary['controls'])==6 and all(item['passed'] for item in summary['controls'])
    except KeyboardInterrupt:
        summary['all_passed']=False
        summary['error']='Control batch cancelled'
    except Exception as exc:
        summary['error']=type(exc).__name__+': '+str(exc)
    finally:
        summary['wall_seconds']=time.monotonic()-started
        summary['invocation_cpu_seconds']=cpu_total()-cpu_started
        summary['source_unchanged']=p.tree_hash(source.parent)==source_before
        summary['accepted_candidate_unchanged']=p.tree_hash(valid.parent)==accepted_before
        summary['within_budgets']=summary['wall_seconds']<=args.seconds and summary['invocation_cpu_seconds']<=args.seconds
        summary['all_passed']=summary['all_passed'] and summary['within_budgets'] and summary['source_unchanged'] and summary['accepted_candidate_unchanged']
        summary['limitations']='Class-target controls are additional routing eligibility checks. Raw DRC cleanliness is recorded, not assumed. No electrical, physical, broad netclass, or solver superiority claim.'
        p.save_json(output/'summary.json',summary)
    return 0 if summary['all_passed'] else 1


if __name__=='__main__':
    sys.exit(main())
