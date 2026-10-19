"""One bounded read-only full006→current receipt/capacity forecast, not a backup.

No Git, subprocess, archive, restore or Native call is permitted in this child.
Production backup limits are changed only in this process and restored afterward.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from contextlib import ExitStack
from unittest.mock import patch
import argparse, hashlib, json, os, re, resource, shutil, signal, stat, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from scripts import backup as b
BASE=ROOT/'.local-backups/checkpoint-20261015T181606Z-b9d396079eb4422f9ba8aee6b1a85b28/receipt.json'
BASE_SHA='82dff0759a5a9ec89b23ee34f3f5330bd847a6f3fd65aeca5b3079db7c1787b3'
BASE_BYTES=77959854
BACKUP_SHA='a74350a473b2788f85ac6681dba74760681817a3ae122327c16d3e9932472477'
TEMPLATE=ROOT/'.runs/integration-backup-capacity-001/forecast.py'
TEMPLATE_SHA='201c6acd31ab171346ab93ac36aa8cd1a0aba33d20915d1d2de4396d51913861'
GiB=1024**3
MAX_INPUT=64*1024**2


def cpu():
    return sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))


def forbidden(*args,**kwargs):
    raise RuntimeError('Forecast prohibits subprocess/Git/archive/backup/restore execution')


def serialize_measure(value, *, canonical=False):
    options=dict(sort_keys=True,separators=(',',':')) if canonical else dict(sort_keys=True,indent=2)
    size=0;hashed=hashlib.sha256()
    for text in json.JSONEncoder(allow_nan=False,**options).iterencode(value):
        raw=text.encode();size+=len(raw);hashed.update(raw)
    if not canonical:size+=1;hashed.update(b'\n')
    return size,hashed.hexdigest()


def allocation(rows):
    return sum(((row['size']+4095)//4096)*4096 for row in rows)


def tracked_forecast(path, expected_sha, head):
    if path is None:
        assert expected_sha is None
        return None,None
    path=Path(path)
    assert path.is_absolute() and ROOT in path.parents and not path.is_symlink()
    assert path.stat().st_size<=MAX_INPUT
    index,pin,size=b.read_json(path)
    assert pin==expected_sha and type(index) is dict
    assert set(index) in ({'schema','source_head','files'},{'schema','source_head','files','git_refs'})
    assert type(index['schema']) is int and index['schema']==1 and index['source_head']==head
    assert type(index['files']) is list and len(index['files'])<=500000
    seen=set();directories=set();logical=allocated=rounded=0
    for row in index['files']:
        assert type(row) is dict and set(row)=={'path','size'}
        name=row['path'];assert type(name) is str
        rel=PurePosixPath(name)
        assert name and not rel.is_absolute() and str(rel)==name and '..' not in rel.parts and '\\' not in name and '.git' not in rel.parts
        assert name not in seen and type(row['size']) is int and row['size']>=0
        seen.add(name);target=ROOT/name
        for parent in (target,*target.parents):
            if parent==ROOT:break
            assert not parent.is_symlink()
        info=target.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size==row['size']
        logical+=info.st_size;allocated+=getattr(info,'st_blocks',0)*512
        rounded+=((info.st_size+4095)//4096)*4096
        directories.update(str(parent) for parent in rel.parents if str(parent)!='.')
    refs=index.get('git_refs')
    if refs is not None:
        assert type(refs) is list and len(refs)<=4096 and len(set(refs))==len(refs)
        assert all(type(line) is str and re.fullmatch(r'[0-9a-f]{40,64} refs/[^\x00-\x20]+',line) for line in refs)
    return dict(path=str(path),sha256=pin,bytes=size,source_head=head,files=len(seen),directories=len(directories),
        logical_bytes=logical,observed_current_allocated_bytes=allocated,working_tree_4KiB_forecast_bytes=rounded+4096*len(directories),
        rough_working_tree_allowance_bytes=2*(rounded+4096*len(directories)),
        limitation='Supplied frozen tracked paths were statted, not queried from Git. Two times 4KiB working-tree allocation is a rough planning allowance, not an upper bound on Git object database/history, new bundle or physical storage.'),refs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--source-head',required=True)
    parser.add_argument('--writers-idle',action='store_true')
    parser.add_argument('--tracked-stat-index')
    parser.add_argument('--tracked-stat-sha256')
    args=parser.parse_args()
    assert args.writers_idle and re.fullmatch(r'[0-9a-f]{40}',args.source_head)
    assert (args.tracked_stat_index is None)==(args.tracked_stat_sha256 is None)
    assert args.tracked_stat_sha256 is None or re.fullmatch(r'[0-9a-f]{64}',args.tracked_stat_sha256)
    output=Path(args.output)
    assert output.is_absolute() and ROOT/'.runs' in output.parents and output.parent.is_dir()
    assert not os.path.lexists(output) and not output.parent.is_symlink()
    start=time.monotonic();cpu0=cpu();free0=shutil.disk_usage(ROOT).free
    production={key:getattr(b,key) for key in ('LIMIT','MAX_FILES','MAX_RECEIPT_BYTES','MAX_CHAIN_RECEIPT_BYTES','MAX_CHAIN')}
    result=dict(schema=1,status='forecast_failed',backup_created=False,archive_created=False,restoration_performed=False,
        native_executed=False,Git_executed=False,subprocess_executed_by_child=False,scopes=list(b.SCOPES),exclusions_added=False,
        production_caps=production,forecast_only_caps=dict(files=500000,directories=500000,logical_bytes=20*GiB),
        source_head=args.source_head,source_head_authority='Caller-supplied frozen metadata; child never queries or certifies Git state.',
        writers_idle_asserted=True,authoritative_backup_or_release_qualification=False)
    prior_signal=signal.getsignal(signal.SIGALRM)
    def alarm(*unused):raise TimeoutError('Forecast590-second child deadline')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(590)
    try:
        assert b.digest(ROOT/'scripts/backup.py')==BACKUP_SHA and b.digest(TEMPLATE)==TEMPLATE_SHA
        with ExitStack() as stack:
            for name in ('run','Popen'):stack.enter_context(patch.object(subprocess,name,forbidden))
            for name in ('git','create','verify','checkpoint','load_chain','make_archive','restore_archive','audit_archive','check_artifacts'):
                stack.enter_context(patch.object(b,name,forbidden))
            stack.enter_context(patch.object(b,'MAX_FILES',500000))
            stack.enter_context(patch.object(b,'LIMIT',20*GiB))
            prior,prior_sha,prior_bytes=b.read_json(BASE)
            assert prior_sha==BASE_SHA and prior_bytes==BASE_BYTES and prior['schema']==1 and prior['source_root']==str(ROOT)
            b.check_manifest(prior['inventory'])
            verification_path=BASE.parent/'verification-b59c37b1560943369ceb8e9eba1e23ca.json'
            verification,verification_sha,verification_bytes=b.read_json(verification_path)
            assert (verification['verified'] is True and verification['receipt_sha256']==BASE_SHA
                and verification['restored_git_head']==prior['git_head'] and verification['all_refs_restored'] is True
                and verification['git_bundle_verified_in_empty_repository'] is True
                and verification['non_git_files_verified']==len(prior['inventory']['files']) and verification['cli_smoke']['exit']==0)
            current=b.inventory(ROOT)  # Complete, unchanged shared credential/path/hash guards.
            b.check_manifest(current)
            inventory_bytes,inventory_sha=serialize_measure(current,canonical=True)
            delta=b.delta_inventory(prior['inventory'],current,directory_policy=b.DELTA_DIRECTORIES_COMPACT)
            tracked,refs=tracked_forecast(args.tracked_stat_index,args.tracked_stat_sha256,args.source_head)
            forecast={key:prior[key] for key in ('source_root','git_refs','limitation','excluded','bundle','archive')}
            forecast.update(schema=2,kind='incremental',created_utc=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
                git_head=args.source_head,inventory=current,delta=delta,
                parent=dict(name=str(BASE.relative_to(ROOT/'.local-backups')),sha256=BASE_SHA),
                base_verification=dict(name=str(verification_path.relative_to(ROOT/'.local-backups')),sha256=verification_sha))
            if refs is not None:forecast['git_refs']=refs
            receipt_bytes,receipt_sha=serialize_measure(forecast)
            metadata_allowance=64*1024
            chain_bytes=prior_bytes+receipt_bytes
            bundle=BASE.parent/'repository.bundle';info=bundle.lstat();bundle_entry=prior['bundle']
            assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size==bundle_entry['size']
            bundle_hash=None
            if info.st_size<=64*1024**2:
                bundle_hash=b.digest(bundle);after=bundle.lstat()
                assert (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                assert bundle_hash==bundle_entry['sha256']
            counts={scope:dict(files=0,directories=0,logical_bytes=0) for scope in b.SCOPES}
            for row in current['files']:
                count=counts[row['path'].split('/',1)[0]];count['files']+=1;count['logical_bytes']+=row['size']
            for name in current['directories']:counts[name.split('/',1)[0]]['directories']+=1
            target_payload=allocation(current['files']);target_dirs=4096*len(current['directories'])
            base_restore=allocation(prior['inventory']['files'])+4096*len(prior['inventory']['directories'])
            delta_payload=allocation(delta['inventory']['files']);delta_dirs=4096*len(delta['inventory']['directories'])
            max_copy=max((((row['size']+4095)//4096)*4096 for row in delta['inventory']['files']),default=0)
            conservative_peak=max(base_restore+delta_payload+delta_dirs,target_payload+target_dirs)+max_copy
            # backup.checkpoint retains its separately extracted delta-check
            # tree. It still occupies disk during a subsequent full verify.
            integrity_payload=delta_payload+delta_dirs
            integrity_root=4096
            end_to_end_peak=conservative_peak+integrity_payload+integrity_root
            reserve=3*GiB;receipt_alloc=((receipt_bytes+4095)//4096)*4096
            tracked_allowance=None if tracked is None else tracked['rough_working_tree_allowance_bytes']
            result.update(status='read_only_forecast_completed_not_backup',inventory=dict(files=len(current['files']),directories=len(current['directories']),logical_bytes=current['total_file_bytes'],canonical_sha256=inventory_sha,canonical_serialized_bytes=inventory_bytes,absent_scopes=current['absent_scopes'],per_scope=counts),
                full006=dict(path=str(BASE),sha256=prior_sha,receipt_bytes=prior_bytes,files=len(prior['inventory']['files']),directories=len(prior['inventory']['directories']),logical_bytes=prior['inventory']['total_file_bytes'],verification_sha256=verification_sha,verification_bytes=verification_bytes),
                compact_delta=dict(files=len(delta['inventory']['files']),directories=len(delta['inventory']['directories']),logical_bytes=delta['inventory']['total_file_bytes'],deleted_files=len(delta['deleted_files']),deleted_directories=len(delta['deleted_directories']),directory_policy=b.DELTA_DIRECTORIES_COMPACT),
                receipt_forecast=dict(serialized_incremental_bytes=receipt_bytes,serialized_sha256=receipt_sha,two_node_chain_receipt_bytes=chain_bytes,unmeasured_metadata_allowance_bytes=metadata_allowance,incremental_fits_current_receipt_cap_with_allowance=receipt_bytes+metadata_allowance<=production['MAX_RECEIPT_BYTES'],two_node_fits_current_chain_cap_with_allowance=chain_bytes+metadata_allowance<=production['MAX_CHAIN_RECEIPT_BYTES'],metadata_scope='Exact current inventory/delta and shared receipt JSON formatting. New archive/bundle metadata stands in with fixed historical full006 fields; refs are caller-frozen if provided, otherwise historical only. SHA is of this forecast shape, not a real backup receipt.'),
                population_fits_current_capture_caps=len(current['files'])<=production['MAX_FILES'] and len(current['directories'])<=production['MAX_FILES'] and current['total_file_bytes']<=production['LIMIT'],
                tracked_checkout=tracked,existing_full006_bundle=dict(path=str(bundle),bytes=info.st_size,sha256=bundle_hash,hash_checked=bundle_hash is not None,scope='Existing prior bundle only; not a current Git bundle or current history/checkout proof.'),
                restore_capacity=dict(target_payload_4KiB_bytes=target_payload,target_directories_4KiB_bytes=target_dirs,reserve_bytes=reserve,base_restore_4KiB_bytes=base_restore,delta_staging_payload_4KiB_bytes=delta_payload,delta_staging_directories_4KiB_bytes=delta_dirs,largest_transient_copy_4KiB_bytes=max_copy,conservative_restore_plus_stage_peak_4KiB_bytes=conservative_peak,new_receipt_4KiB_bytes=receipt_alloc,headroom_after_target_dirs_reserve_bytes=free0-target_payload-target_dirs-reserve,headroom_after_conservative_peak_receipt_reserve_bytes=free0-conservative_peak-receipt_alloc-reserve,rough_tracked_checkout_allowance_bytes=tracked_allowance,headroom_after_tracked_allowance_bytes=None if tracked_allowance is None else free0-conservative_peak-receipt_alloc-reserve-tracked_allowance,unknown_additional_bytes=['Actual new compressed delta archive','Actual new repository bundle and restored Git object database/history','Filesystem metadata/allocation differences beyond4KiB arithmetic','Subsequent evidence/authoring growth']),
                end_to_end_capacity=dict(scope='Capture integrity checkpoint followed by full restoration, retaining both scratch trees. Restore-only arithmetic above excludes this additional retained delta-check tree.',capture_integrity_retained_payload_4KiB_bytes=delta_payload,capture_integrity_retained_directories_4KiB_bytes=delta_dirs,capture_integrity_retained_tree_4KiB_bytes=integrity_payload,capture_integrity_root_directory_4KiB_bytes=integrity_root,restore_only_peak_4KiB_bytes=conservative_peak,combined_integrity_and_restore_peak_4KiB_bytes=end_to_end_peak,new_receipt_4KiB_bytes=receipt_alloc,reserve_bytes=reserve,headroom_after_integrity_restore_receipt_reserve_bytes=free0-end_to_end_peak-receipt_alloc-reserve,rough_tracked_checkout_allowance_bytes=tracked_allowance,headroom_after_tracked_allowance_bytes=None if tracked_allowance is None else free0-end_to_end_peak-receipt_alloc-reserve-tracked_allowance,still_unknown=['Actual new compressed archive','Actual new Git bundle and restored object database/history','Other filesystem metadata and later growth']),
                disk=dict(free_before_bytes=free0,free_after_bytes=shutil.disk_usage(ROOT).free),
                limitations=['One shared inventory cutoff with per-file stability only; no second complete inventory equality or Git-state certification.','Other writers must be idle; result/log are subsequent small additions not in the measured cutoff.','No500k manifest, source paths or private source contents are published; only aggregate measurements and canonical hashes.','Production capture/receipt/chain limits remain unchanged. Forecast-only elevated bounds cannot authorize capture.','Compression and actual Git restoration are unmeasured; a positive arithmetic headroom is not a demonstrated feasible backup/restore.'])
        assert all(getattr(b,k)==v for k,v in production.items())
        assert b.digest(ROOT/'scripts/backup.py')==BACKUP_SHA and b.digest(TEMPLATE)==TEMPLATE_SHA
    except BaseException as exc:
        result.update(status='forecast_failed',error=type(exc).__name__+': '+str(exc),production_caps_restored=all(getattr(b,k)==v for k,v in production.items()))
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,prior_signal)
    result.update(forecast_completed=result['status']=='read_only_forecast_completed_not_backup',wall_seconds=time.monotonic()-start,full_CPU_seconds=cpu()-cpu0,production_caps_restored=all(getattr(b,k)==v for k,v in production.items()))
    encoded=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    assert len(encoded)<=64*1024
    with output.open('xb') as stream:stream.write(encoded)
    print(encoded.decode(),end='')
    return 0 if result['status']=='read_only_forecast_completed_not_backup' else 2


if __name__=='__main__':raise SystemExit(main())
