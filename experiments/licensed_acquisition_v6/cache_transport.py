"""Fixed existing clock responses only; no network and no source writes."""
import copy
from pathlib import Path
from experiments.licensed_acquisition_v1 import fetch as shared

class Cache:
    def __init__(self,root,plan,rows):
        self.root=Path(root);self.reuse=copy.deepcopy(plan['cache_reuse']);self.rows=copy.deepcopy(rows)
        if self.reuse['transport']!='fixed-clock-verified-cached-response-v1' or self.reuse['new_network_requests']!=0:raise ValueError('fixed offline cache contract required')
        if set(self.reuse['files'])!={r['destination'] for r in rows}:raise ValueError('complete cache population required')
        self.verify()
    def path(self,name):return shared.contained(self.root,self.root/shared.safe(name))
    def verify(self):
        metadata={}
        for name,info in self.reuse['metadata'].items():
            raw=shared.bounded(self.path(name))
            if (len(raw),shared.sha(raw))!=(info['bytes'],info['sha256']):raise ValueError('frozen cache lineage metadata changed')
            metadata[Path(name).name]=shared.decode(raw)
        receipt=metadata['fetch-receipt.json'];profile=metadata['acquisition-profile-facts.json']
        clocks=[p for p in profile['profiles'] if p['repository']=='ugolnikovE/als311-clock' and p['commit']=='494ab6baf40746d313fe11379425900ebe97c319']
        if len(clocks)!=1 or len(clocks[0]['files'])!=10:raise ValueError('exact original clock profile required')
        sources={r['path']:r for r in clocks[0]['files']}
        for row in self.rows:
            info=self.reuse['files'][row['destination']];raw=shared.bounded(self.path(info['raw_path']));shared.payload(row,raw)
            if (len(raw),shared.sha(raw))!=(info['bytes'],info['sha256']):raise ValueError('cached response changed')
            hits=[r for r in receipt['requests'] if r.get('label')==info['label'] and r.get('url')==row['raw_url']]
            if len(hits)!=1 or hits[0].get('final_url')!=row['raw_url'] or hits[0].get('sha256')!=row['sha256'] or hits[0].get('bytes')!=row['bytes'] or hits[0].get('file')!=Path(info['raw_path']).name:raise ValueError('cached source request binding differs')
            source=sources.get(row['source_path'])
            if source is None or (source['bytes'],source['sha256'],source['git_blob_sha'],source['primary_url'])!=(row['bytes'],row['sha256'],row['git_blob_sha1'],row['raw_url']):raise ValueError('cached source profile differs')
    def transport(self,row,record,path,allowance,remaining):
        remaining();self.verify()
        if row not in self.rows:raise ValueError('unknown row outside fixed clock cache')
        raw=shared.bounded(self.path(self.reuse['files'][row['destination']]['raw_path']))
        if len(raw)>allowance:raise ValueError('cached payload allowance')
        shared.payload(row,raw)
        with path.open('xb') as stream:stream.write(raw)
        record.update(transport=self.reuse['transport'],network_requests=0,network_bytes=0,
            url=row['raw_url'],cached_raw_path=self.reuse['files'][row['destination']]['raw_path'],
            lineage_sha256={k:v['sha256'] for k,v in self.reuse['metadata'].items()},
            received_bytes=len(raw),response_sha256=shared.sha(raw),status='cached_payload_reused')
        self.verify();remaining();return raw
