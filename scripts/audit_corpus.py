#!/usr/bin/env python3
"""Hash-verify the full acquired population and report static eligibility only."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,help='New JSON file under .runs')
    args=parser.parse_args()
    output=Path(args.output).resolve()
    if ROOT/'.runs' not in output.parents or output.exists():
        parser.error('use a new output file under .runs')
    spec=importlib.util.spec_from_file_location('project_fetch',ROOT/'data/fetch.py')
    fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)
    manifest=fetch.load_manifest()
    report={'schema':1,'kind':'complete acquired population static audit','split':'development-exposed',
            'source_manifest_sha256':p.sha(ROOT/'data/sources.json'),
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'implementation_sha256':{str(f.relative_to(ROOT)):p.sha(f) for f in [Path(__file__),ROOT/'data/fetch.py',*sorted((ROOT/'autorouter').glob('*.py'))]},
            'native_processes_executed':0,'independent_families_established':None,'holdout':False,
            'boards':[],'claims_limit':'Eligibility is a static gate only. It is not native acceptance, family independence or comparative routing evidence.'}
    for project in manifest['projects']:
        directory=ROOT/'.data'/project['destination']
        files=[row for row in manifest['files'] if row['project_id']==project['project_id']]
        expected={str(Path(row['destination']).relative_to(project['destination'])):row['sha256'] for row in files}
        if p.tree_hash(directory)!=expected: raise ValueError('complete project hash/file set differs: '+project['project_id'])
        for entry in project['boards']:
            board=ROOT/'.data'/entry['board']
            row={'project_id':project['project_id'],'family':project['family'],'family_status':project.get('family_independence'),
                 'board':str(board.relative_to(ROOT)),'sha256':p.sha(board),'license':project['license'],
                 'rules_binding':entry['rules_binding'],'static_eligible':False,'native_acceptance':None}
            try:
                p.preflight(board)
                row.update(static_eligible=True,unsupported_reason=None)
            except p.Rejected as exc:
                row['unsupported_reason']=str(exc)
            except Exception as exc:
                row['audit_error']=type(exc).__name__+': '+str(exc)
            report['boards'].append(row)
    report['totals']={'projects':len(manifest['projects']),'boards':len(report['boards']),
                      'files':len(manifest['files']),'bytes':sum(row['bytes'] for row in manifest['files']),
                      'static_eligible':sum(row['static_eligible'] for row in report['boards']),
                      'unsupported':sum('unsupported_reason' in row and row['unsupported_reason'] is not None for row in report['boards']),
                      'audit_errors':sum('audit_error' in row for row in report['boards'])}
    output.parent.mkdir(parents=True,exist_ok=True)
    p.save_json(output,report)
    print(json.dumps({'report':str(output),'totals':report['totals']}))
    return 0 if report['totals']['audit_errors']==0 else 2


if __name__=='__main__':
    raise SystemExit(main())
