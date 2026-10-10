#!/usr/bin/env python3
"""Real native counterexamples on the original diagnostic family, never benchmarks."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter import sexpr as sx
from autorouter.pipeline import Job, routes, tree_hash, validate_candidate, save_json, sha, tool_manifest, native_accepted, native_rejection_reasons

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--valid',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args(); valid=Path(args.valid).resolve(); root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=False)
    original=sx.read(valid)
    cases=['positive','disconnected','short','wrong_pad_net','moved_footprint','rotated_footprint','pad_geometry','illegal_via','narrow_track','removed_zone','removed_protected','reduced_clearance','changed_severity','added_rules']
    outcomes=[]
    for name in cases:
        job=Job(root/name,60)
        source=job.out/'source'; candidate_dir=job.out/'candidate'
        shutil.copytree(valid.parent,source);shutil.copytree(valid.parent,candidate_dir)
        candidate=candidate_dir/valid.name
        tree=copy.deepcopy(original); protected=[]
        r=routes(tree); fp=sx.children(tree,'footprint')[0];pad=sx.children(fp,'pad')[0]
        if name=='disconnected': tree.remove(r[0])
        elif name=='short':
            tree.append(['segment',['start','25','10'],['end','25','20'],['width','0.2'],['layer','"F.Cu"'],['net','"SIGNAL_A"']])
        elif name=='wrong_pad_net': sx.one(pad,'net')[1]='"SIGNAL_B"'
        elif name=='moved_footprint': sx.one(fp,'at')[1]='11'
        elif name=='rotated_footprint': sx.one(fp,'at')[:]=['at','10','10','90']
        elif name=='pad_geometry': sx.one(pad,'size')[1]='3'
        elif name=='illegal_via': tree.append(['via',['at','25','10'],['size','0.2'],['drill','0.8'],['layers','"F.Cu"','"B.Cu"'],['net','"SIGNAL_A"']])
        elif name=='narrow_track': sx.one(r[0],'width')[1]='0.01'
        elif name=='removed_zone': tree.remove(sx.children(tree,'zone')[0])
        elif name=='removed_protected': protected=[copy.deepcopy(r[0])];tree.remove(r[0])
        elif name in ('reduced_clearance','changed_severity'):
            project=candidate.with_suffix('.kicad_pro');data=json.loads(project.read_text());settings=data.setdefault('board',{}).setdefault('design_settings',{})
            if name=='reduced_clearance': settings.setdefault('rules',{})['min_clearance']=0
            else: settings.setdefault('rule_severities',{})['clearance']='ignore'
            project.write_text(json.dumps(data))
        elif name=='added_rules': candidate.with_suffix('.kicad_dru').write_text('(version 1)\n(rule "relax" (constraint clearance (min 0mm)))\n')
        sx.write(candidate,tree)
        entry={'case':name,'expected_accepted':name=='positive','candidate_before_sha256':sha(candidate),'source_hashes':tree_hash(source)}
        # Every board is actually read and checked by native KiCad, including invariant failures.
        try: entry['diagnostic_native']=job.drc('diagnostic-drc',candidate)
        except Exception as exc: entry['diagnostic_native_error']=str(exc)
        try:
            digest,native=validate_candidate(job,original,candidate,tree_hash(source),protected)
            entry['candidate_sha256']=digest;entry['native']=native
            entry['accepted']=native_accepted(native)
            entry['native_rejection_reasons']=native_rejection_reasons(native)
        except Exception as exc: entry['accepted']=False;entry['reason']=str(exc)
        raw=job.out/'diagnostic-drc.json'
        entry['native_execution_proven']=raw.is_file() and any(s['name']=='diagnostic-drc' and s['exit_code'] in (0,5) for s in job.steps)
        entry['passed']=entry['accepted']==entry['expected_accepted'] and entry['native_execution_proven']
        entry['steps']=job.steps
        save_json(job.out/'control.json',entry);outcomes.append(entry)
        print(name, 'PASS' if entry['passed'] else 'FAIL',entry.get('reason',entry.get('native',{}).get('blocking')),flush=True)
    summary={'schema':1,'family':'diagnostic-smoke','native_version':'10.0.0','tools':tool_manifest(),'all_passed':all(x['passed'] for x in outcomes),'controls':outcomes}
    save_json(root/'summary.json',summary)
    return 0 if summary['all_passed'] else 1
if __name__=='__main__':sys.exit(main())
