"""Prospective native negative control; never edits its accepted source.

Run only after the lead releases native execution. No solver runs. This tests
the raw excluded flag and parser rejection count, not routing quality.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import shutil
import resource
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, config as c

class OfflineJob(p.Job):
    def step(self,name,argv,allowed=(0,)):
        return super().step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],allowed)

def total_cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime

def nm(value):
    d=Decimal(str(value))*1000000
    if not d.is_finite() or d!=d.to_integral_value():
        raise ValueError('non-integral native report position')
    return str(int(d))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--result',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--run-native',action='store_true',help='explicit lead execution gate')
    args=ap.parse_args()
    if not args.run_native:
        ap.error('native execution is disabled without --run-native')
    started,cpu_started=time.monotonic(),total_cpu()
    receipt=args.result.resolve(strict=True)
    output=args.output.resolve()
    if not output.is_relative_to(ROOT/'.runs') or output.exists():
        raise ValueError('new project-local .runs output required')
    data=json.loads(receipt.read_text())
    p.check_result(receipt)  # read-only evidence verification before any native work
    candidate=Path(data['candidate']).resolve(strict=True)
    if candidate.name!='sonde xilinx.kicad_pcb':
        raise ValueError('this narrow negative control requires the accepted sonde project')
    original_before=p.tree_hash(candidate.parent)
    upstream=Path(data['source']).parent
    upstream_before=p.tree_hash(upstream)
    output.mkdir(parents=True,exist_ok=False)
    summary={'schema':1,'kind':'native excluded-warning negative control',
             'status':'started','accepted_source_receipt':str(receipt),
             'accepted_source_receipt_sha256':p.sha(receipt),'source_before':original_before,
             'upstream_source_before':upstream_before,'solver_jobs':0,'steps':[],
             'tools':p.tool_manifest(),'script_sha256':p.sha(Path(__file__)),
             'wall_budget_seconds':60,'cpu_budget_seconds':60,
             'scope':'one fresh native positive plus deliberate excluded-warning negative; original severities unchanged'}
    try:
        positive=output/'positive-project'
        negative=output/'negative-project'
        shutil.copytree(candidate.parent,positive)
        shutil.copytree(candidate.parent,negative)
        board=positive/candidate.name
        positive_job=OfflineJob(output/'positive-native',20)
        positive_summary=positive_job.drc('drc',board)
        summary['steps']+=positive_job.steps
        positive_report=positive_job.out/'drc.json'
        raw=json.loads(positive_report.read_text())
        proposal=p.parse_report
        positive_checked=proposal(positive_report,board.name)
        if any(positive_checked[k] for k in ('opens','blocking','exclusions')):
            raise ValueError('fresh positive native report is not routing-scope accepted')
        matches=[v for v in raw['violations'] if v.get('type')=='lib_footprint_mismatch'
                 and v.get('severity')=='warning' and v.get('excluded') is not True
                 and len(v.get('items',[]))==1]
        if len(matches)!=1 or raw.get('coordinate_units')!='mm':
            raise ValueError('expected one unexcluded footprint-library mismatch in mm')
        finding=matches[0]
        item=finding['items'][0]
        # Native library-parity markers use FOOTPRINT.GetCenter(), while JSON
        # affected-item positions use GetPosition(). They need not coincide.
        center_script=output/'native_marker_center.py'
        center_script.write_text("import json,sys,pcbnew\nboard=pcbnew.LoadBoard(sys.argv[1])\nitems=[f for f in board.GetFootprints() if f.m_Uuid.AsString()==sys.argv[2]]\nassert len(items)==1\np=items[0].GetCenter()\nwith open(sys.argv[3],'x') as out:json.dump({'x_nm':int(p.x),'y_nm':int(p.y),'uuid':sys.argv[2],'version':pcbnew.GetBuildVersion()},out)\n")
        center_output=output/'native-marker-center.json'
        center_job=OfflineJob(output/'marker-center-native',10)
        center_job.step('marker-center',[c.PYTHON,center_script,board,item['uuid'],center_output])
        summary['steps']+=center_job.steps
        center=json.loads(center_output.read_text())
        if center.get('version')!='10.0.0' or center.get('uuid')!=item['uuid'] or any(type(center.get(k)) is not int for k in ('x_nm','y_nm')):
            raise ValueError('invalid native marker center')
        summary['marker_center']={'value':center,'script_sha256':p.sha(center_script),'report_sha256':p.sha(center_output),'input_sha256':p.sha(board)}
        marker='|'.join([finding['type'],str(center['x_nm']),str(center['y_nm']),
                         item['uuid'],'00000000-0000-0000-0000-000000000000'])
        settings_file=(negative/candidate.name).with_suffix('.kicad_pro')
        settings=json.loads(settings_file.read_text())
        design=settings['board']['design_settings']
        if design.get('drc_exclusions'):
            raise ValueError('negative fixture must start with no exclusions')
        original_severities=dict(design['rule_severities'])
        design['drc_exclusions']=[[marker,'Deliberately invalid acceptance control; disposable copy only']]
        settings_file.write_text(json.dumps(settings,indent=2)+'\n')
        if design['rule_severities']!=original_severities:
            raise ValueError('control changed original severity settings')
        if p.sha(negative/candidate.name)!=p.sha(candidate):
            raise ValueError('control altered source board bytes')
        negative_job=OfflineJob(output/'negative-native',20)
        negative_job.drc('drc',negative/candidate.name)
        summary['steps']+=negative_job.steps
        negative_report=negative_job.out/'drc.json'
        badraw=json.loads(negative_report.read_text())
        actual=[v for v in badraw['violations'] if v.get('type')==finding['type']
                and v.get('severity')=='warning' and v.get('excluded') is True
                and any(x.get('uuid')==item['uuid'] for x in v.get('items',[]))]
        if len(actual)!=1:
            raise ValueError('native did not emit the expected excluded warning; serialization remains unqualified')
        checked=proposal(negative_report,candidate.name)
        current=p.parse_report(negative_report,candidate.name)
        if checked['exclusions']<1:
            raise ValueError('production parser lost actual native excluded flag')
        summary.update(status='passed',native_positive_report_sha256=p.sha(positive_report),
                       native_negative_report_sha256=p.sha(negative_report),
                       positive=positive_checked,negative=checked,current_production_parser=current,
                       actual_native_excluded_warning=actual[0],
                       candidate_rejected_by_production_acceptance=any(checked[k] for k in ('opens','blocking','exclusions')),
                       exclusion_marker=marker,
                       limitation='Parser rejection count tested; no candidate promotion, new routing run or complete check_result receipt fabricated.')
    except Exception as exc:
        summary.update(status='failed',error=type(exc).__name__+': '+str(exc))
    finally:
        summary['source_after']=p.tree_hash(candidate.parent)
        summary['upstream_source_after']=p.tree_hash(upstream)
        summary['original_sources_unchanged']=(summary['source_after']==original_before and summary['upstream_source_after']==upstream_before)
        summary['wall_seconds']=time.monotonic()-started
        summary['cpu_seconds']=total_cpu()-cpu_started
        summary['within_budgets']=summary['wall_seconds']<=60 and summary['cpu_seconds']<=60
        summary['implementation_unchanged']=summary['tools']==p.tool_manifest()
        if not summary['within_budgets'] or not summary['implementation_unchanged']:summary['status']='failed_budget_or_code_change'
        if not summary['original_sources_unchanged']:
            summary['status']='failed_source_changed'
        p.save_json(output/'summary.json',summary)
    print(json.dumps({k:summary[k] for k in ('status','original_sources_unchanged','wall_seconds')},indent=2))
    return 0 if summary['status']=='passed' else 1

if __name__=='__main__':
    raise SystemExit(main())
