"""One-shot lead-only full snapshot+restore via existing scripts/backup.py with finite305k filecapacity and10GiB bytecapacity.

Preparation only until the lead releases all scope writers and supplies the
verified clean checkpoint. No timer, retry, background loop or evidence deletion.
"""
from pathlib import Path
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU0=cpu()
import argparse,fcntl,hashlib,json,os,re,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'scripts/backup.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import backup
from autorouter import pipeline as p
from autorouter.runner import run
CAP=1800.;PUBLICATION=2.
OUT=ROOT/'.local-backups/current-full-restoration-execution-006'
HELPER=ROOT/'scripts/backup.py'


def require(value,reason):
    if not value:raise RuntimeError(reason)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--expected-helper-sha256',required=True)
    parser.add_argument('--writers-idle',action='store_true',required=True,
        help='Lead confirms all .runs/.data/.local-reference/source writers are stopped for this one snapshot/restore.')
    args=parser.parse_args()
    require(re.fullmatch('[0-9a-f]{40}',args.expected_head) and re.fullmatch('[0-9a-f]{64}',args.expected_helper_sha256),'exact verified checkpoint/helper pins required')
    backup.backups_directory(ROOT)
    OUT.mkdir(mode=0o700,exist_ok=False)
    record=dict(schema=1,kind='one-shot-current-full-snapshot-and-restoration',verified=False,full_restoration_tested=False,
        expected_git_head=args.expected_head,helper_sha256=args.expected_helper_sha256,controller_sha256=backup.digest(Path(__file__)),
        process=None,writer_idle_declaration=args.writers_idle,shared_experiment_lock_held=False,
        whole_wall_full_cpu_acceptance_cap_seconds=CAP,publication_allowance_seconds=PUBLICATION,
        limitation=backup.LIMITATION,
        scope='Default existing backup CLI creates a new FULL Git/nonGit snapshot then restores and verifies it once. Every earlier backup/evidence/partial remains. No Native/routing/GUI/publication claim.')
    lock_path=ROOT/'.runs/quality-experiment.lock'
    lock=None
    def stable():
        require(backup.digest(HELPER)==args.expected_helper_sha256,'backup helper changed')
        require(backup.git(ROOT,'rev-parse','HEAD')==args.expected_head,'source checkpoint changed')
        require(not backup.git(ROOT,'status','--porcelain=v1','--untracked-files=normal'),'source not clean')
        require(backup.digest(Path(__file__))==record['controller_sha256'],'launcher changed')
    try:
        require(sys.platform=='darwin' and ROOT.resolve()==ROOT,'selected local Mac checkout required')
        require((backup.LIMIT,backup.MAX_FILES,backup.MAX_RECEIPT_BYTES,backup.MAX_CHAIN_RECEIPT_BYTES)==
            (10*1024**3,305000,80*1024**2,192*1024**2),'existing finite backup capacities changed')
        require(not any(x.is_symlink() for x in (lock_path,*lock_path.parents)),'shared lock alias')
        fd=os.open(lock_path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);lock=os.fdopen(fd,'r+')
        info=os.fstat(lock.fileno());require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'ordinary exclusive lock required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);record['shared_experiment_lock_held']=True
        stable()
        # No --incremental/--verify: existing default performs full create+verify.
        record['process']=run([str(ROOT/'.venv/bin/python'),'-B',str(HELPER)],cwd=OUT,log=OUT/'command.log',
            timeout=max(.001,CAP-PUBLICATION-(time.monotonic()-START)),max_log_bytes=128*1024,
            max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3)
        process=record['process']
        require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
            and process['log_truncated'] is False,'full snapshot/restoration command failed; raw output retained')
        payload=json.loads((OUT/'command.log').read_text())
        receipt=Path(payload['receipt']);proof_path=Path(payload['verification'])
        require(receipt.is_absolute() and receipt.resolve(strict=True)==receipt and receipt.parent.parent==ROOT/'.local-backups'
            and receipt.name=='receipt.json' and proof_path.parent==receipt.parent
            and proof_path.name.startswith('verification-') and proof_path.suffix=='.json','backup output paths differ')
        proof,pin,_=backup.read_json(proof_path)
        require(payload['full_restoration_tested'] is True and proof['verified'] is True and proof['full_restoration_tested'] is True
            and proof['all_refs_restored'] is True and proof['git_bundle_verified_in_empty_repository'] is True
            and proof['receipt']==str(receipt) and proof['receipt_sha256']==backup.digest(receipt)
            and proof['restored_git_head']==args.expected_head and proof['cli_smoke']['exit']==0
            and proof['chain_length']==1,'new full restoration proof failed')
        stable()
        require(max(time.monotonic()-START,cpu()-CPU0)+PUBLICATION<=CAP,'whole snapshot/restoration delivery exceeds bounded cap')
        record.update(verified=True,full_restoration_tested=True,receipt=str(receipt),receipt_sha256=backup.digest(receipt),
            verification=str(proof_path),verification_sha256=pin,restore_directory=proof['restore_directory'],
            non_git_files_verified=proof['non_git_files_verified'],all_refs_restored=True,source_clean_after=True)
    except BaseException as exc:
        record.update(verified=False,full_restoration_tested=False,error=type(exc).__name__+': '+str(exc))
    finally:
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
        if (OUT/'command.log').is_file():record['log_sha256']=backup.digest(OUT/'command.log')
        if max(record['wall_seconds'],record['full_cpu_seconds'])+PUBLICATION>CAP:
            record.update(verified=False,full_restoration_tested=False,error='whole snapshot/restoration publication cap exceeded')
        p.save_json(OUT/'execution.json',record)
        if lock is not None:lock.close()
    print(json.dumps({key:record.get(key) for key in ('verified','full_restoration_tested','receipt','verification','wall_seconds','full_cpu_seconds','error')}))
    return 0 if record['verified'] else 2


if __name__=='__main__':raise SystemExit(main())
