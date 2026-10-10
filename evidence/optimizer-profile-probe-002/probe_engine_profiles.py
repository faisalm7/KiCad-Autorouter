#!/usr/bin/env python3
"""Verify routing-profile settings against the actual pinned local JAR.

Runs a settings/parser reflection probe only: no board is loaded, no routing job
is constructed, and no solver is launched. Run outside measured benchmarks.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autorouter import config as c, pipeline as p
from autorouter.runner import run


def expected_setting(key,raw):
    if key.endswith(('job_timeout','.timeout')): return raw
    if key.endswith('improvement_threshold'): return float(raw)*100
    if raw in ('true','false'): return raw=='true'
    return int(raw) if raw.isdigit() else raw


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,help='New direct child of project .runs')
    args=parser.parse_args()
    output=Path(args.output).absolute()
    if output.parent!=ROOT/'.runs' or output.exists() or output.is_symlink() or (ROOT/'.runs').is_symlink():
        raise p.Rejected('New project-local output required')
    if p.sha(c.JAR)!=c.JAR_SHA256:raise p.Rejected('Pinned JAR mismatch')
    profiles=[]
    assigned={}
    for remaining in (120,105,45,900):
        for profile in ('standard','tuned','completion-only'):
            settings=p.engine_profile_settings(profile,remaining)
            name=f'{profile}_remaining_{remaining}'
            assigned[name]=settings
            profiles.append({'name':name,'argv':['-de','probe.dsn','-do','probe.ses',*settings['argv']]})
    request={'timespans':['60s','30s','100s','90s','60','30','100','90','00:01:00','00:00:30','00:01:40','00:01:30'],
             'profiles':profiles}
    p.check_storage()
    output.mkdir();(output/'tmp').mkdir();(output/'java-home').mkdir()
    shutil.copy2(Path(__file__).with_name('EngineProfileProbe.java'),output/'EngineProfileProbe.java')
    shutil.copy2(__file__,output/'probe_engine_profiles.py')
    p.save_json(output/'request.json',request)
    p.save_json(output/'assigned-settings.json',assigned)
    before={str(path):p.sha(path) for path in (c.JAR,c.JAVA,ROOT/'autorouter/pipeline.py',Path(__file__),Path(__file__).with_name('EngineProfileProbe.java'))}
    argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),'-Xms32m','-Xmx256m',
          '-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-Duser.home='+str(output/'java-home'),
          '-Djava.io.tmpdir='+str(output/'tmp'),'--class-path',str(c.JAR),str(output/'EngineProfileProbe.java'),
          str(output/'request.json'),str(output/'actual-settings.json')]
    process=run(argv,cwd=output,log=output/'probe.log',timeout=20)
    p.save_json(output/'process.json',process)
    report={'schema':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'input_hashes':before,'router_executed':False,'board_loaded':False,'passed':False,'process':process}
    checks=[]
    if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']:
        actual=json.loads((output/'actual-settings.json').read_text())
        for text,seconds in actual['timespans_to_seconds'].items():
            if text.endswith('s'):checks.append(seconds is None)
            elif ':' in text:checks.append(seconds==sum(int(part)*scale for part,scale in zip(text.split(':'),(3600,60,1))))
            else:checks.append(seconds==int(text))
        for row in actual['profiles']:
            expected=assigned[row['name']]
            checks.extend([row['effective_job_timeout_seconds']==expected['assigned_job_timeout_seconds'],
                           row['effective_optimizer_timeout_seconds']==expected['assigned_optimizer_timeout_seconds'],
                           row['autorouter_enabled'] is True,
                           row['optimizer_enabled']==(expected['profile']!='completion-only')])
            for flag in expected['argv']:
                key,raw=flag[2:].split('=',1)
                value=row['effective_requested_settings'][key]
                wanted=expected_setting(key,raw)
                checks.append(abs(value-wanted)<1e-6 if isinstance(wanted,float) else value==wanted)
                checks.append(key in row['parsed_cli_arguments'])
        checks.extend(p.sha(path)==digest for path,digest in before.items())
        report.update(passed=all(checks),checks=len(checks),checks_passed=sum(checks),profiles=len(actual['profiles']),
                      actual_settings_sha256=p.sha(output/'actual-settings.json'))
    p.save_json(output/'result.json',report)
    print(json.dumps({'passed':report['passed'],'receipt':str(output/'result.json')}))
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
