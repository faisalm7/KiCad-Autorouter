from pathlib import Path
import ast
root=Path(__file__).parent/'.runs'
for name in ('run-universal-shift-interface-native-paired300-002.py','read-universal-shift-interface-native-paired300-002.py'):
 p=root/name;s=p.read_text().replace("native['source_before']","native['source_hashes']").replace("gate['source_before']","gate['source_hashes']")
 s=s.replace('delivered_wall_full_cpu_budget_per_arm_seconds=240','delivered_wall_full_cpu_budget_per_arm_seconds=300').replace("'prerequisite240 reserve or complete cost differs'","'historical prerequisite cost or300 planning reserve differs'")
 needle="if review['passed'] is not True or review['source_current'] is not True:raise p.Rejected('new controls independent readback not qualified')"
 indent='        ' if name.startswith('read-') else '    '
 extra="""
INDENTrequired={gate['result']:gate['result_sha256'],gate['execution']:gate['execution_sha256'],gate['readback_execution']:gate['readback_execution_sha256']}
INDENTif any(gate['pins'].get(path)!=pin for path,pin in required.items()):raise p.Rejected('control receipt proof pin missing')
INDENTif (control['actor_result_sha256']!=gate['result_sha256'] or review['actor_result_sha256']!=gate['result_sha256'] or review['actor_execution_sha256']!=gate['execution_sha256'] or review['actor_sha256']!=native['actor_sha256']):raise p.Rejected('control independent proof chain differs')
INDENTif (native['shared_checks']!=gate['shared_checks'] or native['positive_native']!=gate['positive_native'] or native['negative_saved_native']!=gate['negative_saved_native'] or native['negative_expected_rejection']!='generated track differs from native netclass target' or any(native['positive_native'][k] or native['negative_saved_native'][k] for k in ('opens','blocking','warnings','exclusions'))):raise p.Rejected('actual positive/invalid composite Native outcomes differ')
INDENTif f.canonical(pc.inventory((ROOT/gate['result']).parent,max_bytes=64*1024**2,max_files=3000,max_entries=6000,with_directories=True))!=f.canonical(gate['material']):raise p.Rejected('qualified control material population changed')
""".replace('INDENT',indent)
 assert needle in s;s=s.replace(needle,needle+extra,1);ast.parse(s);p.write_text(s)
p=root/'run-universal-shift-interface-native-paired300-readback-001.py';s=p.read_text();needle=" for name,pin in {**spec['prior_matrix']['pins'],**spec['netclass_delta']['control']['pins']}.items():require(p.sha(ROOT/name)==pin)"
new="""
 gate=spec['netclass_delta']['control']
 required={gate['result']:gate['result_sha256'],gate['execution']:gate['execution_sha256'],gate['readback_execution']:gate['readback_execution_sha256']}
 for path,pin in required.items():require(gate['pins'].get(path)==pin and p.sha(ROOT/path)==pin)
 require(f.canonical(pc.inventory((ROOT/gate['result']).parent,max_bytes=64*1024**2,max_files=3000,max_entries=6000,with_directories=True))==f.canonical(gate['material']))
"""
assert needle in s;s=s.replace(needle,needle+new,1);ast.parse(s);p.write_text(s)
print('Source-hash field,300 receipt labels, complete control proof chain/pins/material fixed; syntax parsed.')
