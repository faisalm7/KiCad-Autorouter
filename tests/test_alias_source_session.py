"""Exact retained-source transport; exporter rounding stays a visible defect."""
import json,unittest
from decimal import Decimal
from autorouter import sexpr as sx,adapter
from experiments.roller_export_alias_v1 import padless_alias as a
from tests.test_alias_protected_order import m
from tests.test_padless_alias_scope import source
from tests.test_alias_design_path import dsn
from experiments.pic_mixed_transport_probe_v1 import ses_checks as sc

def fixture():
 tree=sx.parse(source().decode());tree.append(['net','1','"GND"'])
 for i in range(11):tree.append(['segment',['start','10.0005',str(i)],['end','11.0005',str(i)],['width','0.254'],['layer','"F.Cu"'],['net','1'],['uuid',json.dumps(f'owned-track-{i}')]])
 raw=(sx.dump(tree)+'\n').encode();binding=a.plan(raw);dt=adapter._parse_dsn(dsn(binding,'/owned/A/native.dsn').decode());sx.one(dt,'network').append(['net','"GND"',['pins']])
 wiring=['wiring']
 for i in range(11):wiring.append(['wire',['path','"F.Cu"','254','10000',str(-i*1000),'11000',str(-i*1000)],['net','"GND"'],['type','route']])
 dt.append(wiring);return raw,binding,adapter._dump_dsn(dt).encode()

class ExactSourceSession(unittest.TestCase):
 def test_raw_export_rounding_rejects_without_tolerance(self):
  raw,binding,native=fixture()
  with self.assertRaisesRegex(ValueError,'exact original'):m.build(native,raw,binding)
 def test_declared_original_source_preserves_half_um_exactly(self):
  raw,binding,native=fixture();before=(bytes(raw),bytes(native));ses,filtered,record=m.build(native,raw,binding,geometry_source='original_protected_source')
  self.assertEqual((raw,native),before);self.assertFalse(record['raw_native_dsn_route_diff']['equal']);self.assertFalse(record['raw_dsn_geometry_repaired'])
  self.assertFalse(record['solver_execution']);self.assertEqual(record['exact_original_segments'],11)
  parsed=sx.parse(filtered.decode());self.assertEqual(sx.one(parsed,'base_design'),['base_design','"/owned/A/native.dsn"'])
  network=sx.one(sx.one(parsed,'routes'),'network_out');actual=sc.Counter()
  for net in sx.children(network,'net'):
   for wire in sx.children(net,'wire'):
    path=sx.one(wire,'path');actual.update(sc.segments(sx.unquote(net[1]),'top_layer',sc.number(path[2])/10,sc.pairs(path[3:],10)))
  self.assertEqual(actual,sc.source_routes(sx.parse(raw.decode()))[0])
 def test_unknown_geometry_source_or_subgrid_refused(self):
  raw,binding,native=fixture()
  with self.assertRaises(ValueError):m.build(native,raw,binding,geometry_source='relaxed')
  tree=sx.parse(raw.decode());sx.one(sx.children(tree,'segment')[0],'start')[1]='10.00005';bad=(sx.dump(tree)+'\n').encode();binding=a.plan(bad)
  with self.assertRaisesRegex(ValueError,'exact SES grid'):m.build(native,bad,binding,geometry_source='original_protected_source')

if __name__=='__main__':unittest.main()
