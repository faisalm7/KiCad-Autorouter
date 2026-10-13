"""Offline routing CLI; outputs separate review candidates only."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from . import config as c
from .pipeline import route, sha, check_result


def preference_arguments(parser):
    parser.add_argument('--settings',help='Explicit persistent JSON preset; never loaded globally')
    parser.add_argument('--seconds',type=float,default=None)
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument('--keep-existing',action='store_true',default=None,help='Protect every existing route')
    scope.add_argument('--scope',choices=['whole','partial'],default=None)
    parser.add_argument('--adapter',choices=['none','graphics','planes','both'],default=None)
    parser.add_argument('--profile',choices=['standard','tuned','completion-only'],default=None)
    parser.add_argument('--guidance',choices=['native','board-floors-v1','placement-clearance-v1'],default=None)
    parser.add_argument('--scoring-preference',choices=['via_default','via_low','via_high'],default=None)
    parser.add_argument('--layers',nargs='+',choices=['source_all','F.Cu','B.Cu'],default=None,
                        help='Allowed NEW routing copper; explicit lists require native completion-only on qualified two-layer boards')


def explicit_preferences(args):
    result={key:getattr(args,key) for key in ('seconds','adapter','profile','guidance','scoring_preference') if getattr(args,key) is not None}
    if args.keep_existing or args.scope=='partial':result['scope']='partial_completion'
    elif args.scope=='whole':result['scope']='whole_board_unlocked_routing'
    if args.layers is not None:result['layers']='source_all' if args.layers==['source_all'] else args.layers
    return result


def preview(board,settings=None,overrides=None):
    """Read the same static guards as routing; no engine, native validation or writes."""
    from . import preferences as pref, pipeline as p, sexpr as sx, placement_clearance as pc
    from .handoff import real_path
    captured=pref.load(settings) if settings is not None else None
    effective=pref.resolve(captured,overrides)
    source=real_path(board);before=pc.inventory(source.parent)
    original=p.preflight(source)
    if effective['guidance']!='native':
        from . import board_floor as g
        if p.netclass_policy(source) is not None:raise p.Rejected('unsupported: floor policy requires one Default class')
        g.qualify_scope(json.loads(source.with_suffix('.kicad_pro').read_text()),g.task_from_source(original))
        if effective['guidance']=='placement-clearance-v1':pc.narrow_source(original)
    protected=[item for item in p.routes(original) if effective['scope']=='partial_completion' or p.locked(item)]
    copper=[sx.unquote(row[1]) for row in sx.one(original,'layers',[])[1:] if isinstance(row,list) and len(row)>2 and sx.unquote(row[1]).endswith('.Cu')]
    layer_preview=None
    if effective['layers']!='source_all':
        from . import layer_policy as lp
        lp._source_layers(original)
        lp._route_map(original)
        layer_preview={'allowed_new_route_layers':effective['layers'],
            'protected_items_outside_allowed_layers':sum(not set(lp._route_layers(item))<=set(effective['layers']) for item in protected),
            'description':'Exact original protected copper is preserved, including layers outside the requested new-route list. New through vias require both copper layers.'}
    pref.check_fresh(captured)
    if pc.inventory(source.parent)!=before:raise p.Rejected('source changed during preview')
    return {'status':'preview','static_preflight_passed':True,'native_validation_performed':False,
            'source':str(source),'source_sha256':before[source.name],'effective_preferences':effective,
            'copper_layers':copper,'existing_route_items':len(p.routes(original)),
            'protected_route_items':len(protected),'rerouted_route_items':len(p.routes(original))-len(protected),
            'layer_restriction':layer_preview,
            'scope_description':'Complete remaining connections while preserving every existing route' if effective['scope']=='partial_completion' else 'Reroute unlocked copper while preserving locked routes',
            'next_step':'Run route with these settings to create a separate candidate. Acceptance still requires original-design checks and native KiCad refill/DRC.'}

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
    settings=sub.add_parser('settings-init',help='Create an explicit editable JSON preset without overwriting a file')
    settings.add_argument('--output',required=True)
    view=sub.add_parser('preview',help='Preview settings, protected routing and static support without changing the board')
    view.add_argument('board');preference_arguments(view)
    review=sub.add_parser('review-copy');review.add_argument('receipt');review.add_argument('--output',required=True)
    review.add_argument('--render',action='store_true',help='Add native before/after copper plots and a local HTML review')
    choice=sub.add_parser('review-choice',help='Record accept/reject intent for a separate project; no PCB approval or application')
    choice.add_argument('review');choice.add_argument('--choice',required=True,choices=['accept','reject']);choice.add_argument('--output',required=True)
    export_cmd=sub.add_parser('review-export',help='Fresh native validation into a new separate project after accept intent; no live apply')
    export_cmd.add_argument('choice');export_cmd.add_argument('--output',required=True);export_cmd.add_argument('--seconds',type=float,default=120)
    export_check=sub.add_parser('review-export-check',help='Check stored export/source/report consistency; does not run fresh DRC')
    export_check.add_argument('receipt')
    improve=sub.add_parser('improve');improve.add_argument('board');improve.add_argument('--output',required=True);improve.add_argument('--seconds',type=float,default=120);improve.add_argument('--proposal-policy',choices=['single','feedback'],default=None)
    improve.add_argument('--guidance',choices=['native','placement-search-v1'],default='native',help='Explicit experimental planning policy; original rules are still enforced')
    improve.add_argument('--allocation',choices=['standard-85-v1','legacy-tuned'],default=None,help='Placement pruning budget/proposal allocation; defaults to the measured standard85 variant')
    recover=sub.add_parser('recover',help='Experimental whole-board routing with bounded thermal repair');recover.add_argument('board');recover.add_argument('--output',required=True);recover.add_argument('--seconds',type=float,default=120)
    verify=sub.add_parser('check-result');verify.add_argument('receipt')
    r=sub.add_parser('route');r.add_argument('board');r.add_argument('--output',required=True);preference_arguments(r)
    a=p.parse_args()
    if a.command=='doctor':
        result=doctor();print(json.dumps(result,indent=2));return 0 if result['ready'] else 2
    if a.command in {'settings-init','preview'}:
        try:
            if a.command=='preview':result=preview(a.board,a.settings,explicit_preferences(a))
            else:
                from . import preferences as pref
                from .handoff import real_path
                target=real_path(a.output,existing=False)
                with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as stream:
                    json.dump(pref.validate(dict(pref.DEFAULTS)),stream,indent=2);stream.write('\n')
                result={'created':str(target),'usage':'Pass this file explicitly with --settings; command-line options override only their named settings.'}
            print(json.dumps(result,indent=2));return 0
        except Exception as exc:print(json.dumps({'status':'rejected','reason':str(exc)}));return 2
    if a.command=='review-copy':
        from .handoff import review_copy
        try: print(json.dumps(review_copy(a.receipt,a.output,render=a.render),indent=2));return 0
        except Exception as exc: print(json.dumps({'status':'rejected','reason':str(exc)}));return 2
    if a.command=='review-choice':
        from .handoff import review_choice
        try: print(json.dumps(review_choice(a.review,a.output,a.choice),indent=2));return 0
        except Exception as exc: print(json.dumps({'status':'rejected','reason':str(exc)}));return 2
    if a.command=='check-result':
        try: print(json.dumps(check_result(a.receipt),indent=2));return 0
        except Exception as exc: print(json.dumps({'current':False,'reason':str(exc)}));return 2
    if a.command=='review-export':
        from .review_export import export
        try:
            result=export(a.choice,a.output,a.seconds)
            print(json.dumps({key:result.get(key) for key in ('status','export_accepted','project_file','candidate_sha256','native_report_sha256','wall_seconds','total_cpu_seconds')},indent=2))
            return 0 if result['export_accepted'] else 2
        except Exception as exc:print(json.dumps({'status':'rejected','reason':str(exc)}));return 2
    if a.command=='review-export-check':
        from .review_export import check_export
        try:print(json.dumps(check_export(a.receipt),indent=2));return 0
        except Exception as exc:print(json.dumps({'current':False,'reason':str(exc)}));return 2
    try:
        if a.command=='improve':
            if a.guidance=='placement-search-v1':
                if a.proposal_policy not in (None,'feedback'):raise ValueError('placement pruning requires its declared feedback proposal policy')
                from .placement_strategy import prune,STANDARD_ALLOCATION
                result=prune(a.board,a.output,a.seconds,allocation=a.allocation or STANDARD_ALLOCATION)
            else:
                if a.allocation is not None:raise ValueError('--allocation requires placement-search-v1 guidance')
                from .strategy import prune
                result=prune(a.board,a.output,a.seconds,proposal_policy=a.proposal_policy or 'single')
        elif a.command=='recover':
            from .recovery import recover
            result=recover(a.board,a.output,a.seconds)
        else: result=route(a.board,a.output,settings_path=a.settings,preference_overrides=explicit_preferences(a))
    except Exception as exc:
        print(json.dumps({'accepted':False,'error':str(exc)}));return 2
    print(json.dumps({k:v for k,v in result.items() if k in ('status','accepted','reason','candidate','wall_seconds','total_cpu_seconds','metrics')},indent=2))
    return 0 if result['accepted'] else 2
if __name__=='__main__': sys.exit(main())
