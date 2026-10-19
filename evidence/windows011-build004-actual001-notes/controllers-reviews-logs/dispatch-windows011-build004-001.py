"""One exact-source public standard-runner compile-only regression."""
import concurrent.futures,datetime,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];base=root/'.runs/windows011-build004-actual001';assert not base.exists();base.mkdir()
gh='/opt/homebrew/bin/gh';repo='faisalm7/KiCad-Autorouter'
def api(endpoint):return json.loads(subprocess.check_output([gh,'api',endpoint],timeout=20))
statuses=('queued','in_progress','waiting','pending','requested')
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 futures={s:pool.submit(api,'repos/'+repo+'/actions/runs?status='+s+'&per_page=100') for s in statuses}
 active={s:future.result() for s,future in futures.items()}
for s,r in active.items():assert r['total_count']==0 and r['workflow_runs']==[],s
meta=api('repos/'+repo);assert meta['private'] is False and meta['archived'] is False and meta['visibility']=='public'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();assert head=='72db8d41c8d389f8c3b6f80fb22535bd9962c93c'
receipt=json.loads((root/('.runs/checkpoint-'+head[:7]+'.json')).read_text());assert receipt['verified'] and receipt['git_head']==receipt['remote_sha']==head
protocol=root/'scripts/windows_native_slice/persistent_guard_build_protocol004.json';sha=hashlib.sha256(protocol.read_bytes()).hexdigest();assert sha=='1e77ac76423031bfc606a35d02ee69bb84f596679250e85d33c2eb046e4ac3ae'
for name,pin in json.loads(protocol.read_text())['source_files_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==pin
assert hashlib.sha256((root/'.github/workflows/manual-python-controls.yml').read_bytes()).hexdigest()=='d6791b9cfa6d6b373288c9b8c71a6628b852a4034968514b0b1cb8e040c76f7f'
record=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),public=True,archived=False,expected_source_sha=head,expected_protocol_sha256=sha,active_CI_status_queries_empty=True,active_queries=active,standard_runner='windows-2022',contents_permission='read',CI_minutes=3,artifact_uploads=0,cache_uploads=0,installer=False,Native=False,spending=0,billing_primary='https://docs.github.com/en/billing/concepts/product-billing/github-actions',billing_checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='One build-null-only target regression of C4389 fix. Real-policy011 protocol remains closed; no validSID/owner/profile/policy/socket operations.',new_CI_dispatched=False)
(base/'pre-dispatch.json').write_text(json.dumps(record,indent=2)+'\n')
args=[gh,'workflow','run','manual-python-controls.yml','--repo',repo,'--ref','rebuild/local-20261010-015447','-f','probe=windows-guard-build','-f','expected_source_sha='+head,'-f','expected_protocol_sha='+sha]
with (base/'dispatch.stdout.log').open('xb') as out,(base/'dispatch.stderr.log').open('xb') as err:
 result=subprocess.run(args,stdout=out,stderr=err,timeout=30)
assert result.returncode==0,'Uncertain dispatch: preserve directory and inspect remote; never blindly redispatch.'
print((base/'dispatch.stdout.log').read_text())
