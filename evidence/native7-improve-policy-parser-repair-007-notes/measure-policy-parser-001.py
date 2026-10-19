"""Finite pure-parser cost measurement; no route/readback acceptance claim."""
import time,resource,sys,json,ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import local_settings as local,pipeline as p
raw=(R/'autorouter/pipeline.py').read_bytes();policies={'NORMAL_DRC_LOCAL_SETTINGS_POLICY':local.JOB_POLICY};pairs=tuple(sorted(policies.items()));count=40
start=time.monotonic();cpu0=time.process_time()
for _ in range(count):expected=dict(local._derive_policy_declarations(raw,pairs,ast.parse,ast.walk))
uncached=dict(wall_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-cpu0)
local._cached_policy_declarations.cache_clear();start=time.monotonic();cpu0=time.process_time()
for _ in range(count):assert local.policy_declarations(raw,policies)==expected
cached=dict(wall_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-cpu0)
record=dict(schema=1,kind='pure-policy-parser-microbenchmark-v1',accepted=False,Native=False,actual_GUI=False,calls_per_arm=count,source_sha256=p.sha(R/'autorouter/pipeline.py'),local_settings_sha256=p.sha(R/'autorouter/local_settings.py'),uncached=uncached,bounded_reuse=cached,memo=dict(local._cached_policy_declarations.cache_info()._asdict()),scope='One current captured pipeline literal declaration repeated40times, including first parse. Artificial pure-parser comparison only; full runtime/readback/GUI speed or routing quality not established. Preserve complete external cost separately.')
p.save_json(R/'.runs/policy-parser-microbenchmark-001.json',record);print(json.dumps(record))
