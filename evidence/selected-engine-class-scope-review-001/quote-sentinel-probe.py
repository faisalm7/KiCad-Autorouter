"""Read-only actual retained input; pure parser/emitter defect, no native execution."""
from pathlib import Path
from autorouter import routing_scope as rs,adapter as a
raw=Path('.runs/selected-net-native-positive-001/task.dsn').read_bytes()
emitted,binding=rs.partition_dsn(raw,['SIGNAL_A'])
assert a._QUOTE_SENTINEL.encode() in emitted
try:a._parse_dsn(emitted.decode())
except ValueError as exc:assert str(exc)=='DSN contains reserved quote sentinel';print('reproduced normalized parser sentinel emitted into engine DSN')
else:raise AssertionError('before-fix output unexpectedly reparsed')
