"""Fresh read-only binding gate for the exact production thermal-pair candidate."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
PAIR=ROOT/'.runs/thermal-paired-001';POSITIVE=PAIR/'C_thermal';BASE=POSITIVE/'incumbent'
BASE_HASH='f3469b34e2d7724d65ade7b1a5b3353c75b67c54f525f54b88c3626cd8531b0a'
GOOD_HASH='be7694040a84aaac331981cd121ac66774284df30923550c5054691fe302dabb'
REPORT_HASH='9c686fa4880f270280f11ba049ddb9a7e23a4e576e1023374b95c8673321a45b'
UID='026a2d2d-ef36-597d-a14d-3e1c751c2de8'
PAD='387e8928-4a73-4b3a-ae74-249440996e94';ZONE='00000000-0000-0000-0000-00004cdec22b'
AUDIT_SHA='c6a64ccbd118fe4b15bfd6fdbfb4ad7e1168da9d5da1a5dfb7db389e20c95076'
def read(path):return json.loads(Path(path).read_text())
def verify_positive():
    checks=[]
    def need(ok,message):
        checks.append(message)
        if not ok:raise p.Rejected(message)
    protocol=read(PAIR/'protocol.json');summary=read(PAIR/'paired-summary.json');freeze=protocol['freeze']
    report=read(POSITIVE/'result.json');inc=read(BASE/'result.json')
    need(p.sha(Path(__file__).parent.parent/'audit.json')==AUDIT_SHA,'independent completed paired audit unchanged')
    need(freeze['tools']['git_head']=='cbae1254f00d3470d98ba18d24a09e99874f0cc2' and p.sha(PAIR/'protocol.json')==summary['protocol_sha256'],'historical paired freeze exact')
    need(summary['status']=='completed' and len(summary['results'])==2,'completed pair structure')
    row=summary['results'][1]
    need(row['id']=='C_thermal' and row['accepted'] and row['result_sha256']==p.sha(POSITIVE/'result.json') and row['charged_wall_seconds']<=120 and row['charged_cpu_seconds']<=120,'accepted independently charged C outcome')
    source=Path(report['source']);candidate=Path(report['candidate']);hashes=report['source_hashes']
    need(candidate==POSITIVE/'candidate'/source.name and report['candidate_sha256']==GOOD_HASH and report['native_report_sha256']==REPORT_HASH,'exact production selected candidate/report')
    need(report['tools']==freeze['tools'] and report['source_hashes']==freeze['source_hashes']==inc['source_hashes'],'root/incumbent frozen tools/source')
    for relative,digest in freeze['tools']['implementation_sha256'].items():
        need(p.sha(ROOT/relative)==digest and p.sha(PAIR/'frozen-code'/relative)==digest and p.sha(POSITIVE/'code'/Path(relative).name)==digest,'reviewed current/frozen validation code '+relative)
    for path,digest in freeze['tools']['files'].items():need(p.sha(path)==digest,'native tool pin '+Path(path).name)
    need(p.tree_hash(source.parent)==hashes==p.tree_hash(POSITIVE/'snapshot')==p.tree_hash(BASE/'snapshot'),'all immutable original source copies')
    # Production strict reader checks final native/process/map/metrics/code/input bindings.
    p.check_result(POSITIVE/'result.json')
    original=p.preflight(source);base=sx.read(inc['candidate']);good=sx.read(candidate)
    need(p.sha(inc['candidate'])==inc['candidate_sha256']==BASE_HASH and inc['status']=='drc_rejected' and not inc['accepted'],'exact fresh failed incumbent')
    need(report['incumbent']['receipt']==str(BASE/'result.json') and report['incumbent']['receipt_sha256']==p.sha(BASE/'result.json'),'parent incumbent bound')
    native=p.parse_report(BASE/'final-drc.json',source.name)
    need(native==inc['native'] and p.sha(BASE/'final-drc.json')==inc['native_report_sha256'],'original failed native report bound')
    expected=dict(hashes);expected[source.name]=BASE_HASH;p.verify_candidate_files(Path(inc['candidate']),hashes,BASE_HASH)
    binding=read(BASE/'final-drc-binding.json')
    need(binding['before']==expected and binding['source']==inc['candidate'] and binding['input']==str(BASE/'final-drc-input'/source.name) and binding['saved'] is False,'failed native exact input paths/hash')
    need(p.tree_hash(BASE/'final-drc-input')==binding['after'] and all(binding['after'].get(k)==v for k,v in expected.items()),'failed native actual retained input/rules')
    need(native['opens']==native['warnings']==native['exclusions']==0 and native['blocking']==1 and len(native['findings'])==1 and native['findings'][0]['type']=='starved_thermal' and {i['uuid'] for i in native['findings'][0]['items']}=={PAD,ZONE},'sole exact thermal counterfactual expectation')
    added=[r for r in p.routes(good) if sx.one(r,'uuid')==['uuid','"'+UID+'"']]
    need(len(added)==1 and added[0][0]=='segment' and p.routes(good)==p.routes(base)+added,'exact one generated bridge')
    removed=copy.deepcopy(good);removed.remove(added[0])
    need(removed==base and hashlib.sha256((sx.dump(removed)+'\n').encode()).hexdigest()==BASE_HASH,'bridge removal recreates failed bytes/fill')
    need(p.immutable(base)==p.immutable(good)==p.immutable(original),'original geometry preserved')
    return {'passed':True,'check_count':len(checks),'source':str(source),'source_hashes':hashes,'candidate':str(candidate),'candidate_sha256':GOOD_HASH,'baseline_native':native,'tools':freeze['tools'],'postrun_code_changes':{},'checks':checks}

if __name__=='__main__':print(json.dumps(verify_positive(),indent=2))
