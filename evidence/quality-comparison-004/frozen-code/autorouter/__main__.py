"""Offline routing CLI; outputs separate review candidates only."""
import argparse
import json
import platform
import shutil
import subprocess
import sys
from . import config as c
from .pipeline import route, sha, check_result

def doctor():
    checks={}
    for name,path in [('kicad_cli',c.CLI),('kicad_python',c.PYTHON),('java',c.JAVA),('engine',c.JAR)]:
        checks[name]={'path':str(path),'present':path.is_file()}
        if path.is_file(): checks[name]['sha256']=sha(path)
    for name,argv in [('kicad_version',[str(c.CLI),'version']),('pcbnew_version',[str(c.PYTHON),'-c','import pcbnew; print(pcbnew.GetBuildVersion())']),('java_version',[str(c.JAVA),'-version'])]:
        try:
            r=subprocess.run(argv,capture_output=True,text=True,timeout=15)
            checks[name]={'exit':r.returncode,'output':(r.stdout+r.stderr).strip()}
        except Exception as e: checks[name]={'error':str(e)}
    ok=all(checks[k]['present'] for k in ['kicad_cli','kicad_python','java','engine']) and checks.get('kicad_version',{}).get('output')=='10.0.0' and checks.get('pcbnew_version',{}).get('output')=='10.0.0' and checks['engine'].get('sha256')==c.JAR_SHA256 and platform.system()=='Darwin' and shutil.which('sandbox-exec') is not None
    return {'ready':ok,'platform':platform.platform(),'workspace':str(c.ROOT),'checks':checks,'qualified_scope':'experimental CLI; no GUI or comparative improvement claim','setup_network_required':True,'route_network_required':False}

def main():
    p=argparse.ArgumentParser(prog='python -m autorouter')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    review=sub.add_parser('review-copy');review.add_argument('receipt');review.add_argument('--output',required=True)
    improve=sub.add_parser('improve');improve.add_argument('board');improve.add_argument('--output',required=True);improve.add_argument('--seconds',type=float,default=120);improve.add_argument('--proposal-policy',choices=['single','feedback'],default='single')
    verify=sub.add_parser('check-result');verify.add_argument('receipt')
    r=sub.add_parser('route'); r.add_argument('board'); r.add_argument('--output',required=True); r.add_argument('--seconds',type=float,default=120); r.add_argument('--keep-existing',action='store_true');r.add_argument('--adapter',choices=['none','graphics','planes','both'],default='none');r.add_argument('--profile',choices=['standard','tuned','completion-only'],default='standard')
    a=p.parse_args()
    if a.command=='doctor':
        result=doctor();print(json.dumps(result,indent=2));return 0 if result['ready'] else 2
    if a.command=='review-copy':
        from .handoff import review_copy
        try: print(json.dumps(review_copy(a.receipt,a.output),indent=2));return 0
        except Exception as exc: print(json.dumps({'status':'rejected','reason':str(exc)}));return 2
    if a.command=='check-result':
        try: print(json.dumps(check_result(a.receipt),indent=2));return 0
        except Exception as exc: print(json.dumps({'current':False,'reason':str(exc)}));return 2
    try:
        if a.command=='improve':
            from .strategy import prune
            result=prune(a.board,a.output,a.seconds,proposal_policy=a.proposal_policy)
        else: result=route(a.board,a.output,a.seconds,a.keep_existing,a.adapter,a.profile)
    except Exception as exc:
        print(json.dumps({'accepted':False,'error':str(exc)}));return 2
    print(json.dumps({k:v for k,v in result.items() if k in ('status','accepted','reason','candidate','wall_seconds','total_cpu_seconds','metrics')},indent=2))
    return 0 if result['accepted'] else 2
if __name__=='__main__': sys.exit(main())
