"""Fetch a fixed public source packet into a fresh local demo directory."""
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU_START=cpu()
import argparse,copy,json,re,sys,os,stat
from contextlib import contextmanager
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as shared
from autorouter import floor_route as publication,handoff as h
ROWS=({'bytes': 1066, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/LICENSE', 'git_blob_sha1': '388e1398eb6be796a0ceab266799819af37311b9', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/LICENSE', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': '18f4f144c2d9457195bb6383cdebed6e2e99df4c3d70378363972ddcc992f7a6', 'source_path': 'LICENSE'}, {'bytes': 103334, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/PushButtonLed.kicad_pcb', 'git_blob_sha1': '1548cd51c6ea153763fd3e9741d3c3af8355775a', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/PushButtonLed.kicad_pcb', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': 'a85c5b499b7803d184ec34ef396746afcd16c0557166bd63d7675beb7b61f7a3', 'source_path': 'PushButtonLed.kicad_pcb'}, {'bytes': 16753, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/PushButtonLed.kicad_pro', 'git_blob_sha1': '8acce63ccb417f5f4ac0c1ad832d071a7e5b1e4f', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/PushButtonLed.kicad_pro', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': '186a7d811ca4bf09afa7c286ce0773deb0d8ca4a6404a530658ee664e69d23e0', 'source_path': 'PushButtonLed.kicad_pro'}, {'bytes': 36854, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/PushButtonLed.kicad_sch', 'git_blob_sha1': '44bae1475b69f202d8a4c06f32038faea6382578', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/PushButtonLed.kicad_sch', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': '2fe34f261ee78cf81bc9e7751d9e1b2ca6416944d830d4f5ac50fe40409a0877', 'source_path': 'PushButtonLed.kicad_sch'}, {'bytes': 3064, 'commit': '29c46b7c03d2afd9fe3a58fe2070309b12f94b42', 'destination': 'push-button-led/README.md', 'git_blob_sha1': '4c7fbdc5e95d2449b32e7155e511bfeec6ac98c3', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/gurusaeth12/push-button-led-kicad/29c46b7c03d2afd9fe3a58fe2070309b12f94b42/README.md', 'repository': 'gurusaeth12/push-button-led-kicad', 'rights_basis': 'Root MIT notice by Gurusaeth covers supplied editable hardware/documentation; README has no separate hardware-scope sentence. Retain exact LICENSE/README; embedded stock KiCad content exception only, models unclosed.', 'sha256': 'db7a1e9afa9c288e0e5474637ab3a9d2a2abe07555f6157c06488337cf426de4', 'source_path': 'README.md'})
SECONDS=300
NETWORK_BYTES=161076
OUTPUT_BYTES=2*1024**2
MATERIAL=('scripts/fetch_led_demo.py','experiments/licensed_acquisition_v1/fetch.py','autorouter/floor_route.py','autorouter/handoff.py','autorouter/pipeline.py')
ARC_MATERIAL=('experiments/placement_handoff_native_v1/driver.py','experiments/placement_production_controls_v1/driver.py','autorouter/placement_clearance.py')

ARC_PROFILE={'schema': 1, 'profile_id': 'arcdice', 'project_id': 'arcdice', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'rows': [{'source_path': 'LICENSE', 'bytes': 1067, 'sha256': '13aa5751cc47416650ad3c976d1c001f32ca3b3d49caac777ae66e819a437298', 'git_blob_sha1': '9d4599da9dcec69bb6e4c6cdc867aacbfbd77cdd', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/LICENSE', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/LICENSE', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'README.md', 'bytes': 2930, 'sha256': '876a106e288ec606cf29239d6129d07b79a134005769ba50ef0d450622c1751b', 'git_blob_sha1': '09720df73a14f8f037486dc49d815ade7312083f', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/README.md', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/README.md', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'hardware/ArcDice.kicad_pcb', 'bytes': 488060, 'sha256': '098e90725279e698f61d7f4a5f0281202ba32f655b9c430047c019783a60bf96', 'git_blob_sha1': '4efafcc2ce836ba6414e48197c305ac6fe458aa1', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/hardware/ArcDice.kicad_pcb', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/hardware/ArcDice.kicad_pcb', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'hardware/ArcDice.kicad_pro', 'bytes': 17925, 'sha256': 'be12f193331f3091ef31b9df28dc968119be56269adddcd5b2ed2921523223f6', 'git_blob_sha1': '53d28b286d88e0a1919bee83b70b2afa3f71f7ff', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/hardware/ArcDice.kicad_pro', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/hardware/ArcDice.kicad_pro', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}, {'source_path': 'hardware/ArcDice.kicad_sch', 'bytes': 85359, 'sha256': '388bb0410c3372c2331c84b44ba8a45e10c4b34206a3b28b65cb90057129e4de', 'git_blob_sha1': 'aa3407c4d469eac8323872f13dcec2d980ceb7b3', 'repository': 'VorosEgyes/ArcDice', 'commit': '5908d99db1ef98b5996b380c75e5aee8bb8caaa6', 'mode': '100644', 'destination': 'arcdice/hardware/ArcDice.kicad_sch', 'raw_url': 'https://raw.githubusercontent.com/VorosEgyes/ArcDice/5908d99db1ef98b5996b380c75e5aee8bb8caaa6/hardware/ArcDice.kicad_sch', 'rights_basis': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.'}], 'directories': ['hardware'], 'board_path': 'hardware/ArcDice.kicad_pcb', 'output_prefix': 'arcdice-demo-', 'default_output': '.data/arcdice-demo-001', 'source_subdirectory': 'project', 'receipt_path': 'result.json', 'file_count': 5, 'bytes': 595341, 'max_requests': 5, 'network_byte_cap': 595346, 'max_single_response_bytes': 488061, 'wall_budget_seconds': 300, 'cpu_budget_seconds': 300, 'request_wall_seconds': 30, 'output_byte_cap': 2097152, 'source_entries_cap': 6, 'rights': 'Root MIT notice, Miklos Mod 2024, and exact README retained. README declares MIT but has no separate hardware-scope sentence. Embedded MyFootprints:TP4056-Module origin and optional model rights/closure remain unqualified; no raw board/assets publication or models/libraries/firmware download.', 'native_packet_notice_copies': {'hardware/_licenses/creator/LICENSE': 'LICENSE', 'hardware/_licenses/creator/README.md': 'README.md'}, 'native_packet_files': 7, 'native_packet_bytes': 599338, 'development_exposed': True, 'independent_ancestry_established': False, 'native_validation_performed_by_fetch': False, 'raw_assets_public': False, 'warnings': ['Same already exposed ArcDice source, not an additional independent circuit/family.', 'Fetch performs no native routing, schematic, electrical or physical qualification.', 'Root MIT/README retained; README has no separate hardware-scope sentence.', 'MyFootprints:TP4056-Module origin/local library and eight optional models (two absolute paths) remain unclosed.', 'No scripts/firmware/models/libraries/images/engines downloaded; original Source bytes/hierarchy never normalized.']}

ANALOG_PROFILE={'schema': 1, 'profile_id': 'analog-filter', 'project_id': 'analog-filter', 'repository': 'Myrto-Angeliki/analog-filter', 'commit': '6a34b221758fe32f33eca20d735e88028346753a', 'rows': [{'bytes': 1071, 'commit': '6a34b221758fe32f33eca20d735e88028346753a', 'git_blob_sha1': '178b2e83363bc879439704ba181a3262e4037c24', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Myrto-Angeliki/analog-filter/6a34b221758fe32f33eca20d735e88028346753a/LICENSE', 'repository': 'Myrto-Angeliki/analog-filter', 'rights_basis': 'Pinned root MIT2026 Myrto-Angeliki notice and README preserved; no separately licensed hardware/library entries present in immutable tree. Optional stock KiCad10 models not acquired or qualified.', 'sha256': '63b530c020ac3fb94410ce68da27ae4f1b91408e159f76b799c5d2c2e46186b9', 'source_path': 'LICENSE', 'destination': 'analog-filter/LICENSE'}, {'bytes': 7898, 'commit': '6a34b221758fe32f33eca20d735e88028346753a', 'git_blob_sha1': 'fea2bbb2b7fe9e1cb43e156d225f114eaea7c373', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Myrto-Angeliki/analog-filter/6a34b221758fe32f33eca20d735e88028346753a/README.md', 'repository': 'Myrto-Angeliki/analog-filter', 'rights_basis': 'Pinned root MIT2026 Myrto-Angeliki notice and README preserved; no separately licensed hardware/library entries present in immutable tree. Optional stock KiCad10 models not acquired or qualified.', 'sha256': '093d92eedb9c6d603ec876d9c4998909249e0749f6a44022abb3cff00a435be6', 'source_path': 'README.md', 'destination': 'analog-filter/README.md'}, {'bytes': 85910, 'commit': '6a34b221758fe32f33eca20d735e88028346753a', 'git_blob_sha1': 'a450339e182d855f4a43e2d189dc7d43f5794aee', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Myrto-Angeliki/analog-filter/6a34b221758fe32f33eca20d735e88028346753a/kicad/analog_filter_module.kicad_pcb', 'repository': 'Myrto-Angeliki/analog-filter', 'rights_basis': 'Pinned root MIT2026 Myrto-Angeliki notice and README preserved; no separately licensed hardware/library entries present in immutable tree. Optional stock KiCad10 models not acquired or qualified.', 'sha256': '8867dc5ff9d80ba3789f40832454a6cb6085c4dcb0856e97008bfc43eeb03f34', 'source_path': 'kicad/analog_filter_module.kicad_pcb', 'destination': 'analog-filter/kicad/analog_filter_module.kicad_pcb'}, {'bytes': 17143, 'commit': '6a34b221758fe32f33eca20d735e88028346753a', 'git_blob_sha1': 'd6bdf2231abdd1d3954642df33e9119d393accd9', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Myrto-Angeliki/analog-filter/6a34b221758fe32f33eca20d735e88028346753a/kicad/analog_filter_module.kicad_pro', 'repository': 'Myrto-Angeliki/analog-filter', 'rights_basis': 'Pinned root MIT2026 Myrto-Angeliki notice and README preserved; no separately licensed hardware/library entries present in immutable tree. Optional stock KiCad10 models not acquired or qualified.', 'sha256': '13281fa714b165cec0239ba5891cab8984a0f026fdc067ac8fe209de44cea2dc', 'source_path': 'kicad/analog_filter_module.kicad_pro', 'destination': 'analog-filter/kicad/analog_filter_module.kicad_pro'}, {'bytes': 77314, 'commit': '6a34b221758fe32f33eca20d735e88028346753a', 'git_blob_sha1': 'f1891ad8dd2f993663cac59d4f91c790ae9c4ee1', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Myrto-Angeliki/analog-filter/6a34b221758fe32f33eca20d735e88028346753a/kicad/analog_filter_module.kicad_sch', 'repository': 'Myrto-Angeliki/analog-filter', 'rights_basis': 'Pinned root MIT2026 Myrto-Angeliki notice and README preserved; no separately licensed hardware/library entries present in immutable tree. Optional stock KiCad10 models not acquired or qualified.', 'sha256': '5afb13ba0dae7856b5a79cde0c7251a36a1d111cf9b1e568393c2fb6a1b0252d', 'source_path': 'kicad/analog_filter_module.kicad_sch', 'destination': 'analog-filter/kicad/analog_filter_module.kicad_sch'}], 'directories': ['kicad'], 'bytes': 189336, 'network_byte_cap': 189341, 'output_prefix': 'analog-filter-demo-', 'default_output': '.data/analog-filter-demo-001', 'native_packet_notice_copies': {'kicad/_licenses/creator/LICENSE': 'LICENSE', 'kicad/_licenses/creator/README.md': 'README.md'}, 'native_packet_files': 7, 'native_packet_bytes': 198305, 'warnings': ['Source board is FOUR copper layers; README two-layer sentence disagrees. Preserve actual Source4Cu.', 'Fourteen stock KiCad footprint/model declarations have unclosed optional model assets; no model/library/script download or physical/electrical qualification.', 'Root MIT2026 Myrto-Angeliki and original README retained; no independent pedigree or redistribution claim for unresolved third-party models.']}

CELL_SCAN_PROFILE={'schema': 1, 'profile_id': 'cellscan', 'project_id': 'cellscan', 'repository': 'Studented0/18650-Tester', 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'rows': [{'blob_url': 'https://github.com/Studented0/18650-Tester/blob/628c8a7d80f9de07c24d86102dfca9e353c038ce/LICENSE', 'bytes': 1072, 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'destination': 'cellscan/LICENSE', 'git_blob_sha1': 'af62e679521739bc3d3d425517637122877aa7fb', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Studented0/18650-Tester/628c8a7d80f9de07c24d86102dfca9e353c038ce/LICENSE', 'repository': 'Studented0/18650-Tester', 'sha256': '15833c1331f62081f123fd35c017bb44f6697ba60c706e98116760cb3e35ddf1', 'source_path': 'LICENSE'}, {'blob_url': 'https://github.com/Studented0/18650-Tester/blob/628c8a7d80f9de07c24d86102dfca9e353c038ce/README.md', 'bytes': 4780, 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'destination': 'cellscan/README.md', 'git_blob_sha1': '294b7bbae423225a055852b1199a8ac77c3b6b20', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Studented0/18650-Tester/628c8a7d80f9de07c24d86102dfca9e353c038ce/README.md', 'repository': 'Studented0/18650-Tester', 'source_path': 'README.md'}, {'blob_url': 'https://github.com/Studented0/18650-Tester/blob/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/CellScan_Schematic.kicad_pcb', 'bytes': 982968, 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'destination': 'cellscan/hardware/CellScan_Schematic.kicad_pcb', 'git_blob_sha1': 'db571061c6bc4eab51636c8b1897c20a6b21de37', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Studented0/18650-Tester/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/CellScan_Schematic.kicad_pcb', 'repository': 'Studented0/18650-Tester', 'source_path': 'hardware/CellScan_Schematic.kicad_pcb'}, {'blob_url': 'https://github.com/Studented0/18650-Tester/blob/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/CellScan_Schematic.kicad_pro', 'bytes': 16243, 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'destination': 'cellscan/hardware/CellScan_Schematic.kicad_pro', 'git_blob_sha1': 'e8dee6e6c6468efe9cbfd1b60ed780f6b07cfaa6', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Studented0/18650-Tester/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/CellScan_Schematic.kicad_pro', 'repository': 'Studented0/18650-Tester', 'source_path': 'hardware/CellScan_Schematic.kicad_pro'}, {'blob_url': 'https://github.com/Studented0/18650-Tester/blob/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/CellScan_Schematic.kicad_sch', 'bytes': 290345, 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'destination': 'cellscan/hardware/CellScan_Schematic.kicad_sch', 'git_blob_sha1': '42612c5987c30a6daa7f75b648a78ee0dc36abd0', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Studented0/18650-Tester/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/CellScan_Schematic.kicad_sch', 'repository': 'Studented0/18650-Tester', 'source_path': 'hardware/CellScan_Schematic.kicad_sch'}, {'blob_url': 'https://github.com/Studented0/18650-Tester/blob/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/libraries/ESP32-DevKitC-30PIN.kicad_mod', 'bytes': 3822, 'commit': '628c8a7d80f9de07c24d86102dfca9e353c038ce', 'destination': 'cellscan/hardware/libraries/ESP32-DevKitC-30PIN.kicad_mod', 'git_blob_sha1': '8338c7af4bdc5c7181691f127ed7a6973ec54294', 'mode': '100644', 'raw_url': 'https://raw.githubusercontent.com/Studented0/18650-Tester/628c8a7d80f9de07c24d86102dfca9e353c038ce/hardware/libraries/ESP32-DevKitC-30PIN.kicad_mod', 'repository': 'Studented0/18650-Tester', 'source_path': 'hardware/libraries/ESP32-DevKitC-30PIN.kicad_mod'}], 'directories': ['hardware', 'hardware/libraries'], 'board_path': 'hardware/CellScan_Schematic.kicad_pcb', 'output_prefix': 'cellscan-demo-', 'default_output': '.data/cellscan-demo-001', 'file_count': 6, 'bytes': 1299230, 'max_requests': 6, 'network_byte_cap': 1299236, 'max_single_response_bytes': 982969, 'output_byte_cap': 4194304, 'wall_budget_seconds': 300, 'cpu_budget_seconds': 300, 'request_wall_seconds': 30, 'native_packet_notice_copies': {'hardware/_licenses/creator/LICENSE': 'LICENSE', 'hardware/_licenses/creator/README.md': 'README.md'}, 'native_packet_files': 8, 'native_packet_bytes': 1305082, 'development_exposed': True, 'independent_ancestry_established': False, 'native_validation_performed_by_fetch': False, 'raw_assets_public': False, 'warnings': ['Raw six-file source is not acquired or native-qualified by this registration.', 'Pinned root LICENSE identity and exact README are retained on acquisition; optional assets/custom footprint provenance remain unqualified.', '18650 battery measurement/electrical/physical safety and independent ancestry remain unqualified.', 'Only the six fixed public originals are requested; no models, firmware, scripts, images or additional libraries are downloaded. Original source hierarchy/bytes are never normalized.']}


UV_COMMIT = '63153ac5ca9879299f57e3fb68df606bf78d96f8'
UV_REPOSITORY = 'vodjan/uv-dosimeter'
UV_CACHE_DIRECTORY = '.runs/uv-acquisition-license-readiness-001'
UV_CACHE_RECEIPT_SHA256 = 'bd163cbc6e247cec3e543d488b740b776c833c357ebba7f352755868a79dba58'
UV_CACHE_PROFILE_SHA256 = 'b4ee05ba88e9c13ba6a2236dae79aabd83aba9f20d1c560aa820f2830a93d775'
UV_LICENSE_NAMES = ('LICENSE', 'hardware/LICENSE', 'docs/LICENSE')
UV_RIGHTS = 'Root notice explicitly assigns hardware CERN-OHL-S2.0 and root README CC-BY-SA4.0; hardware/LICENSE fulltext and docs/LICENSE must accompany respective source/notices. Jan Vodstrcil and Ondrej Pokovic credited. Solar math asset exception excluded from packet. Exact original documentation/hardware notices retained; firmware/app GPL and excluded solar-math assets not fetched. Local Waveshare module footprint/symbol origin, BLE/RF/battery/model and medical/functional adequacy remain unqualified.'
UV_PROFILE = dict(schema=1, profile_id='uv-dosimeter', project_id='uv-dosimeter',
    repository=UV_REPOSITORY, commit=UV_COMMIT, rows=[
        dict(source_path=name, bytes=size, git_blob_sha1=blob, mode='100644',
             repository=UV_REPOSITORY, commit=UV_COMMIT, destination='uv-dosimeter/'+name,
             raw_url='https://raw.githubusercontent.com/'+UV_REPOSITORY+'/'+UV_COMMIT+'/'+name,
             blob_url='https://github.com/'+UV_REPOSITORY+'/blob/'+UV_COMMIT+'/'+name,
             rights_basis=UV_RIGHTS, **({'sha256':sha} if sha else {}))
        for name,size,blob,sha in (
            ('LICENSE', 2221, '12afba6178cf123231f502ad182a3e19443fb33a', 'cb3e52ebfb641106bf88be8787cacc1642720020b670ddfaf15c69efcacb9213'),
            ('README.md', 10682, 'ce223c0f9764d192d67571dd103ef1361aabd7a8', None),
            ('docs/LICENSE', 20138, '2d58298e6eda10e7204abb52722efbc840db2390', '28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5'),
            ('hardware/AOL_PD_2.kicad_pcb', 311811, '35e11be906de35eba753608efad1adb1e3fd4d24', None),
            ('hardware/AOL_PD_2.kicad_pro', 16492, '8ef4c9d24b2f74052875dcfa92b4c04e02a73916', None),
            ('hardware/AOL_PD_2.kicad_sch', 115950, '065a1a09db40a486e53d9678f04626f27902d2e5', None),
            ('hardware/LICENSE', 13419, '114486fd9446c39da1b69101597e25e33877fca6', 'd6475a84171f0cf7ff52667dea714df268fc65cea42f0bf328b0b70d4cd0ebab'),
            ('hardware/Moje_wearable.kicad_sym', 6585, '2c8b2e9b891eb8d2eb95c06429764c07078f3848', None),
            ('hardware/Moje_wearable.pretty/Waveshare_ESP32-H2-Zero.kicad_mod', 4470, 'ea73b5458baafaa02b890f4c4a3ba1e529cfc381', None),
            ('hardware/fp-lib-table', 137, 'f299bc6cf0cb69accdfba14ab0bfc3ee6685c39f', None),
            ('hardware/sym-lib-table', 141, '6ab6749d2fa94f9b31602e944d6ba162218da4f9', None),
        )], directories=['docs','hardware','hardware/Moje_wearable.pretty'],
    board_path='hardware/AOL_PD_2.kicad_pcb', output_prefix='uv-dosimeter-demo-',
    default_output='.data/uv-dosimeter-demo-001', file_count=11, bytes=502046,
    max_requests=11, network_byte_cap=502057, max_single_response_bytes=311812,
    output_byte_cap=2*1024**2, wall_budget_seconds=300, cpu_budget_seconds=300,
    request_wall_seconds=30,
    native_packet_notice_copies={'hardware/_licenses/creator/LICENSE':'LICENSE',
        'hardware/_licenses/creator/README.md':'README.md',
        'hardware/_licenses/creator/DOCUMENTATION_LICENSE':'docs/LICENSE'},
    native_packet_files=14, native_packet_bytes=535087, development_exposed=True,
    independent_ancestry_established=False, native_validation_performed_by_fetch=False,
    raw_assets_public=False, warnings=['Original11-file UV source not acquired/native qualified by profile registration.', 'Hardware CERN-OHL-S2 licence retained at hardware/LICENSE; root notice/README+CC-BY-SA4 documentation licence preserved beside native project.', 'Creator CTU-course mirror/author credits and local Waveshare footprint/symbol origins retained; independent ancestry/unresolved assets not proven.', 'Battery/charging/BLE/RF and analog measurement requirements remain unknown; no unrestricted reroute or medical/electrical/physical approval.', 'Only exact11public originals; no firmware/app/math/assets/models/scripts downloaded or executed. Source bytes/names/hierarchy never normalized.'])



NAV_COMMIT = 'b64c0dac2134d69963bf28120305bd79aad3c8ac'
NAV_REPOSITORY = 'sparkfun/SparkFun_Qwiic_Navigation_Switch'
NAV_CACHE_DIRECTORY = '.runs/corpus-next-001/metadata/sparkfun__SparkFun_Qwiic_Navigation_Switch'
NAV_NOTICE_NAMES = ('LICENSE.md', 'README.md')
NAV_CACHE_PINS = {
    '.runs/corpus-next-001/metadata-sha256.json': 'e0ed391a8bfdd7d4bc7ef72202ab8f152961cf86df43cba2ba51a77cc4a5b422',
    NAV_CACHE_DIRECTORY+'/summary.json': '2dfb849f12cd7b39e5624b4b30009f4747488b4bd3c89188000bf974aa3985b8',
    NAV_CACHE_DIRECTORY+'/tree.json': '1cc332989db59aea0e35feb80947807dda49dc61839848af3aa170e48eec116d'}
NAV_RIGHTS = 'Root LICENSE.md explicitly assigns hardware CC-BY-SA4.0, separately software/firmware MIT; retain exact SparkFun attribution and README beside native project. Unacquired models/assets and embedded/external dependencies remain unclosed. No physical, electrical, ancestry or routing-support claim.'
NAV_PROFILE = dict(schema=1, profile_id='navigation-switch', project_id='navigation-switch',
    repository=NAV_REPOSITORY, commit=NAV_COMMIT, rows=[
        dict(source_path=name, bytes=size, git_blob_sha1=blob, mode='100644',
             repository=NAV_REPOSITORY, commit=NAV_COMMIT, destination='navigation-switch/'+name,
             raw_url='https://raw.githubusercontent.com/'+NAV_REPOSITORY+'/'+NAV_COMMIT+'/'+name,
             blob_url='https://github.com/'+NAV_REPOSITORY+'/blob/'+NAV_COMMIT+'/'+name,
             rights_basis=NAV_RIGHTS, **({'sha256':pin} if pin else {}))
        for name,size,blob,pin in (
            ('LICENSE.md', 2883, '37238686da3d06815b45154961d5744d28516153', '60350b68666a0d4903a7197114c723fc6d398d72218b785cc074013e39db374d'),
            ('README.md', 4529, '4aefc290f41ee819f5b20959f47d4a0a1688d6be', '8bb25df4388a5600546fdbf0e9d168b1b7ff2d36309a9c11da368952600bc1d3'),
            ('Hardware/SparkFun_Qwiic_Navigation.kicad_pcb', 676230, 'e042366a1aa0e33acdb3b81111fa5aabd018b175', None),
            ('Hardware/SparkFun_Qwiic_Navigation.kicad_pro', 14759, '7d16ce1658d50c44566614c640eaba90606a262b', None),
            ('Hardware/SparkFun_Qwiic_Navigation.kicad_sch', 271174, '014fc8bd4f03c9b245907a72dbcf478e092a2d37', None),
        )], directories=['Hardware'], board_path='Hardware/SparkFun_Qwiic_Navigation.kicad_pcb',
    output_prefix='navigation-switch-demo-', default_output='.data/navigation-switch-demo-001',
    file_count=5, bytes=969575, max_requests=5, network_byte_cap=969580,
    max_single_response_bytes=676231, output_byte_cap=2*1024**2,
    wall_budget_seconds=300, cpu_budget_seconds=300, request_wall_seconds=30,
    native_packet_notice_copies={'Hardware/_licenses/creator/LICENSE.md':'LICENSE.md',
        'Hardware/_licenses/creator/README.md':'README.md'},
    native_packet_files=7, native_packet_bytes=976987, development_exposed=True,
    independent_ancestry_established=False, native_validation_performed_by_fetch=False,
    raw_assets_public=False, warnings=[
        'Original five-file Navigation source; acquisition alone does not establish native/routing support.',
        'Exact SparkFun CC-BY-SA4 hardware attribution and README retained beside native project.',
        'PCA9554/input-switch/RGB topology and sibling Directional Pad ancestry remain unqualified.',
        'Actual copper layers, rules, pads, external references, jumper protection and physical function remain unknown.',
        'Only five fixed originals and two exact notice copies; no models, firmware, assets or scripts fetched/executed.'])


FLIPPER_COMMIT='50f29ca0f4a3703f07c40d846c40da844663a85c'
FLIPPER_REPOSITORY='sparkfun/SparkFun_Pico_Add_On_Flipper'
FLIPPER_CACHE_DIRECTORY='.runs/corpus-next-001/metadata/sparkfun__SparkFun_Pico_Add_On_Flipper'
FLIPPER_NOTICE_NAMES=('LICENSE.md','README.md')
FLIPPER_CACHE_PINS={
    '.runs/corpus-next-001/metadata-sha256.json':'e0ed391a8bfdd7d4bc7ef72202ab8f152961cf86df43cba2ba51a77cc4a5b422',
    FLIPPER_CACHE_DIRECTORY+'/summary.json':'f660c99b8892f92065e5784e5241e612b2a001cc26519c4c02b61becffceb9c4',
    FLIPPER_CACHE_DIRECTORY+'/tree.json':'a062c58c71ce3751fe2e3ac9f68fff2df7f3d0833b52a72ca5f21dc0e24823a2'}
FLIPPER_RIGHTS='Pinned root LICENSE.md explicitly assigns hardware CC-BY-SA4.0, separate MIT code; retain SparkFun attribution, license link and exact README. Same publisher/templates and different circuit role do not prove independent ancestry. External models/library/embedded assets and electrical/physical adequacy remain unqualified; no scripts/model fetch or source mutation.'
FLIPPER_PROFILE=dict(schema=1,profile_id='pico-flipper',project_id='pico-flipper',repository=FLIPPER_REPOSITORY,commit=FLIPPER_COMMIT,
    rows=[dict(source_path=name,bytes=size,git_blob_sha1=blob,mode='100644',repository=FLIPPER_REPOSITORY,commit=FLIPPER_COMMIT,
        destination='pico-flipper/'+name,raw_url='https://raw.githubusercontent.com/'+FLIPPER_REPOSITORY+'/'+FLIPPER_COMMIT+'/'+name,
        blob_url='https://github.com/'+FLIPPER_REPOSITORY+'/blob/'+FLIPPER_COMMIT+'/'+name,rights_basis=FLIPPER_RIGHTS,**({'sha256':pin} if pin else {}))
        for name,size,blob,pin in (
            ('LICENSE.md',2887,'779c526bbfbeabc5aafe9bf871f22b8189ab91ab','e6560063f9b94f2bc9230cd3079a50a077b4c5e04a1137299850e8aa0e73dc85'),
            ('README.md',4547,'658ffbf5a3dcf41cdab8e586b17f246ef875ad92','12420a29e1d5f713c1ed342f08d6c9c38da80f3cc710d452a4c98a73b812df5d'),
            ('Hardware/SparkFun_Pico_Add_On_Flipper.kicad_pcb',907883,'aac482eb9a0bbeae21331f03637ce61d7b1d4ca1',None),
            ('Hardware/SparkFun_Pico_Add_On_Flipper.kicad_pro',16697,'60cb5524918696bc6ed870f09901d6d1ff4b8cf8',None),
            ('Hardware/SparkFun_Pico_Add_On_Flipper.kicad_sch',179646,'44a502d5741684317eb5bc895a25b106dd023927',None))],
    directories=['Hardware'],board_path='Hardware/SparkFun_Pico_Add_On_Flipper.kicad_pcb',
    output_prefix='pico-flipper-demo-',default_output='.data/pico-flipper-demo-001',file_count=5,bytes=1111660,max_requests=5,
    network_byte_cap=1111665,max_single_response_bytes=907884,output_byte_cap=4*1024**2,
    wall_budget_seconds=300,cpu_budget_seconds=300,request_wall_seconds=30,
    native_packet_notice_copies={'Hardware/_licenses/creator/LICENSE.md':'LICENSE.md','Hardware/_licenses/creator/README.md':'README.md'},
    native_packet_files=7,native_packet_bytes=1119094,development_exposed=True,independent_ancestry_established=False,
    native_validation_performed_by_fetch=False,raw_assets_public=False,warnings=[
        'Five exact originals and seven-file notice packet only; native/routing support remains unqualified.',
        'Passive Pico-header remapping/Qwiic/reset role differs from measured circuits; source history and library/template ancestry remain unproven.',
        'Actual native format/layers/classes/pads/constraints/full schematic and external assets remain unknown.',
        'README stale Eagle repository wording retained; root CC-BY-SA4 hardware notice and separate code MIT retained.',
        'Four MiB output bound explicitly accounts for immutable originals+native packet above two MiB; no original or notice dropped.',
        'No models, scripts, ZIPs, firmware or additional dependencies fetched/executed; no electrical/physical claim.'])

AUDIO_PROFILE = {'schema': 1,
 'profile_id': 'audio-player-my1690x',
 'project_id': 'audio-player-my1690x',
 'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
 'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
 'rows': [{'bytes': 2885,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': 'a66ad56c300f117554b167ce494e39fd2d30c372',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/LICENSE.md',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'sha256': 'cc2731bed1b3d28242eaa4bc9992864b28650bdc69fb4c558ce6e0b7bfc74680',
           'source_path': 'LICENSE.md',
           'destination': 'audio-player-my1690x/LICENSE.md',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/LICENSE.md'},
          {'bytes': 2797,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': '6061de716d286499d8ae9e583cbcd04537be77f8',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/README.md',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'sha256': '8ca8cbb4b5e9f0283f8f257f185b2e7c84bc6b25904fadd52cfce6037c121c21',
           'source_path': 'README.md',
           'destination': 'audio-player-my1690x/README.md',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/README.md'},
          {'bytes': 948809,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': '1d9dc6ce54ebed10841644789984ac7d028ab218',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pcb',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'source_path': 'Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pcb',
           'destination': 'audio-player-my1690x/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pcb',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pcb'},
          {'bytes': 15642,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': '38a1fc1883b51484e720ddbbb7e0937041bfb20f',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pro',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'source_path': 'Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pro',
           'destination': 'audio-player-my1690x/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pro',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pro'},
          {'bytes': 300392,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': '74ae3de26ab37eeffed989bf1c9bc7a815629ee7',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_sch',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'source_path': 'Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_sch',
           'destination': 'audio-player-my1690x/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_sch',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_sch'},
          {'bytes': 2160,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': 'aefa6026ba41f01801b0ab0ec0862fd01445394c',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'source_path': 'Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl',
           'destination': 'audio-player-my1690x/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl'},
          {'bytes': 292,
           'commit': '49d66d63eb43105b7dbe437cc9299c637c69c61d',
           'git_blob_sha1': '8ff294343ad0fc2d90cb9a0ea0097ce2fc69351f',
           'mode': '100644',
           'raw_url': 'https://raw.githubusercontent.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/README.md',
           'repository': 'sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S',
           'rights_basis': 'Original publisher hardware CC-BY-SA4 notice/attribution retained; code MIT is '
                           'separate. Per-asset libraries/models remain unclosed.',
           'sha256': '6add188e18eb48c055d25c6cb3c9e2865bcec753e4da3b3bc97602b7f613f683',
           'source_path': 'Hardware/README.md',
           'destination': 'audio-player-my1690x/Hardware/README.md',
           'blob_url': 'https://github.com/sparkfun/SparkFun_Audio_Player_Breakout_MY1690X-16S/blob/49d66d63eb43105b7dbe437cc9299c637c69c61d/Hardware/README.md'}],
 'directories': ['Hardware'],
 'board_path': 'Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_pcb',
 'output_prefix': 'audio-player-my1690x-demo-',
 'default_output': '.data/audio-player-my1690x-demo-001',
 'file_count': 7,
 'bytes': 1272977,
 'max_requests': 7,
 'network_byte_cap': 1272984,
 'max_single_response_bytes': 948810,
 'output_byte_cap': 3145728,
 'wall_budget_seconds': 300,
 'cpu_budget_seconds': 300,
 'request_wall_seconds': 30,
 'native_packet_notice_copies': {'Hardware/_licenses/creator/LICENSE.md': 'LICENSE.md',
                                 'Hardware/_licenses/creator/README.md': 'README.md'},
 'native_packet_files': 9,
 'native_packet_bytes': 1278659,
 'development_exposed': True,
 'independent_ancestry_established': False,
 'native_validation_performed_by_fetch': False,
 'raw_assets_public': False,
 'warnings': ['Exact seven original Audio files including PRL and stale Hardware README; native/routing '
              'support remains unqualified.',
              'SparkFun root hardware CC-BY-SA4 notice and original README copied beside native source; '
              'software MIT separately stated, no firmware fetched.',
              'Hardware/README.md is the original stale Eagle placeholder; root README/tree identify KiCad. '
              'Discrepancy retained without correction.',
              'MY1690X shield and production panel share the provisional ancestry group; no '
              'independent-family/holdout claim.',
              'Actual layers/rules/pads/protection and USB/SD/audio/power intent remain unseen; no '
              'unrestricted reroute, physical or electrical approval.',
              'Production panel, assembly STEP/models and manufacturing outputs remain explicitly considered '
              'outside fixed core source; any mandatory reference blocks closure. No scripts/models/firmware '
              'acquired or executed.']}
AUDIO_CACHE_DIRECTORY = '.runs/corpus-next-001/metadata/sparkfun__SparkFun_Audio_Player_Breakout_MY1690X-16S'
AUDIO_ROOT_NOTICES = ('LICENSE.md','README.md')
AUDIO_CACHE_PINS = {
    '.runs/corpus-next-001/metadata-sha256.json':'e0ed391a8bfdd7d4bc7ef72202ab8f152961cf86df43cba2ba51a77cc4a5b422',
    AUDIO_CACHE_DIRECTORY+'/summary.json':'7640530c6ec9129031c89f702d3f8ea2178e4485aeb3f0e69a3712c61d939002',
    AUDIO_CACHE_DIRECTORY+'/tree.json':'aa4479f585e50240b96a7d6013f7a8880aaa2943cf28ab07d46bdc50b7f542da'}
AUDIO_METADATA_DIRECTORY = '.runs/next-family-acquisition-readiness-001'
AUDIO_METADATA_PINS = {
    'metadata-receipt.json':'60e531c306d351c64333692e77b3326df0023689acc208db166d82c404cb8d30',
    'metadata-execution.json':'ad8777a3a3700a491fa4339b9804a93e07c82c9b769e659333520ce45eaff3ff',
    'closure.json':'c7041f90420487a60e54d98e4c2142fa873e7610239553814520cfa8adae3342'}

def _cache_bodies(root, cfg, names, directory, witness, caps):
    """Shared bounded immutable notice body capture; no cache search/fallback."""
    from autorouter.placement_clearance import read_bytes
    rows={r['source_path']:r for r in cfg['rows']};files={}
    for name in names:
        row=rows[name];relative=directory+'/'+name
        raw=read_bytes(shared.contained(root,root/shared.safe(relative)),row['bytes'])
        info=shared.payload(row,raw)
        files[name]={'raw':raw,'path':relative,'sha256':info['sha256']}
        witness[relative]=info['sha256'];caps[relative]=row['bytes']
    return files

def _root_notice_cache(root, cfg, directory, proof_pins, names, label):
    """Exact old metadata witness; its unmeasured old timing is never invented."""
    from autorouter.placement_clearance import read_bytes
    witness={};caps={};proofs={}
    for name,pin in proof_pins.items():
        raw=read_bytes(shared.contained(root,root/shared.safe(name)),64*1024)
        if shared.sha(raw)!=pin:raise ValueError(label+' cached metadata pin differs')
        proofs[name]=shared.decode(raw);witness[name]=pin;caps[name]=64*1024
    summary_name=directory+'/summary.json';summary=proofs[summary_name]
    tree_name=directory+'/tree.json';tree=proofs[tree_name]
    manifest=proofs['.runs/corpus-next-001/metadata-sha256.json']
    if (summary.get('repository')!=cfg['repository'] or summary.get('commit')!=cfg['commit']
            or summary.get('source_url')!='https://github.com/'+cfg['repository']+'/tree/'+cfg['commit']
            or summary.get('tree_sha')!=cfg['commit'] or summary.get('metadata_complete') is not True
            or summary.get('board_payloads_downloaded')!=0 or summary.get('status')!='metadata_only_not_acquired'
            or tree.get('sha')!=cfg['commit'] or tree.get('truncated') is not False
            or manifest.get('schema')!=1):raise ValueError(label+' cached metadata scope differs')
    documents=summary.get('metadata_documents',[])
    if len(documents)!=2 or {r.get('path') for r in documents}!=set(names):
        raise ValueError(label+' cached notice population differs')
    files=_cache_bodies(root,cfg,names,directory,witness,caps)
    for row in cfg['rows']:
        entries=[r for r in tree.get('tree',[]) if r.get('path')==row['source_path']]
        if len(entries)!=1 or any(entries[0].get(k)!=v for k,v in
                {'type':'blob','mode':row['mode'],'size':row['bytes'],'sha':row['git_blob_sha1']}.items()):
            raise ValueError(label+' cached tree/file pin differs')
    for name,item in files.items():
        row=next(r for r in cfg['rows'] if r['source_path']==name)
        prior=next(r for r in documents if r['path']==name)
        if any(prior.get(k)!=v for k,v in {'url':row['raw_url'],'bytes':row['bytes'],'sha256':item['sha256']}.items()):
            raise ValueError(label+' cached notice provenance differs')
    for name,pin in witness.items():
        if name!='.runs/corpus-next-001/metadata-sha256.json' and manifest.get('files',{}).get(name[len('.runs/corpus-next-001/'):])!=pin:
            raise ValueError(label+' cached manifest binding differs')
    return {'files':files,'witness':witness,'caps':caps,'label':label+' cached notice',
        'prior_acquisition':{'receipt':summary_name,'sha256':witness[summary_name],
            'proof_kind':'pinned metadata summary/tree/manifest; not a timed HTTP receipt',
            'retained_metadata_bodies':len(files),'retained_metadata_bytes':sum(len(item['raw']) for item in files.values()),
            'new_network_requests':None,'received_bytes':None,'wall_seconds':None,'full_cpu_seconds':None,
            'bootstrap_emission_allowance_seconds':None,'cost_status':'unmeasured prior development metadata; not zero',
            'comparative_accounting_complete':False}}

def navigation_notice_cache(root, cfg):
    if cfg['profile_id']!='navigation-switch':raise ValueError('Navigation notice reuse requires Navigation profile')
    return _root_notice_cache(root,cfg,NAV_CACHE_DIRECTORY,NAV_CACHE_PINS,NAV_NOTICE_NAMES,'Navigation')

def flipper_notice_cache(root,cfg):
    if cfg['profile_id']!='pico-flipper':raise ValueError('Flipper notice reuse requires Flipper profile')
    return _root_notice_cache(root,cfg,FLIPPER_CACHE_DIRECTORY,FLIPPER_CACHE_PINS,FLIPPER_NOTICE_NAMES,'Flipper')

def audio_notice_cache(root, cfg):
    """Reuse two untimed root notices and one separately timed text-body proof."""
    from autorouter.placement_clearance import read_bytes
    if cfg['profile_id']!='audio-player-my1690x':raise ValueError('Audio notice reuse requires Audio profile')
    cache=_root_notice_cache(root,cfg,AUDIO_CACHE_DIRECTORY,AUDIO_CACHE_PINS,AUDIO_ROOT_NOTICES,'Audio')
    proofs={}
    for name,pin in AUDIO_METADATA_PINS.items():
        relative=AUDIO_METADATA_DIRECTORY+'/'+name
        raw=read_bytes(shared.contained(root,root/shared.safe(relative)),64*1024)
        if shared.sha(raw)!=pin:raise ValueError('Audio cached hardware metadata pin differs')
        proofs[name]=shared.decode(raw);cache['witness'][relative]=pin;cache['caps'][relative]=64*1024
    receipt=proofs['metadata-receipt.json'];execution=proofs['metadata-execution.json'];closure=proofs['closure.json']
    if (receipt.get('passed') is not True or receipt.get('failures')!=[] or receipt.get('new_primary_requests')!=3
            or len(receipt.get('requests',[]))!=3 or sum(r.get('received_bytes',0) for r in receipt['requests'])!=28855
            or receipt.get('received_bytes')!=28855 or receipt.get('new_geometry_payloads')!=0
            or receipt.get('new_native_or_engine_jobs')!=0 or closure.get('passed') is not True
            or execution.get('receipt_sha256')!=AUDIO_METADATA_PINS['metadata-receipt.json']
            or closure.get('metadata_receipt_sha256')!=AUDIO_METADATA_PINS['metadata-receipt.json']
            or closure.get('metadata_execution_sha256')!=AUDIO_METADATA_PINS['metadata-execution.json']
            or closure.get('conservative_preparation_bootstrap_emission_allowance_seconds')!=3
            or closure.get('actual_metadata_outer_wall_seconds')!=execution.get('wall_seconds')
            or closure.get('actual_metadata_outer_full_cpu_seconds')!=execution.get('full_cpu_seconds')):
        raise ValueError('Audio cached hardware metadata scope/cost differs')
    process=execution.get('process',{})
    if (process.get('status')!='success' or process.get('exit_code')!=0 or process.get('cleanup_complete') is not True
            or process.get('log_truncated') is not False):
        raise ValueError('Audio cached hardware metadata process incomplete')
    names=('Hardware/README.md',);directory=AUDIO_METADATA_DIRECTORY+'/metadata/'+cfg['repository'].replace('/','__')
    files=_cache_bodies(root,cfg,names,directory,cache['witness'],cache['caps'])
    row=next(r for r in cfg['rows'] if r['source_path']==names[0]);item=files[names[0]]
    matches=[r for r in receipt.get('requests',[]) if r.get('repository')==cfg['repository'] and r.get('source_path')==names[0]]
    expected={'url':row['raw_url'],'final_url':row['raw_url'],'http_status':200,'payload_verified':True,
        'bytes':row['bytes'],'received_bytes':row['bytes'],'sha256':item['sha256'],'response_sha256':item['sha256'],
        'artifact':item['path'][len(AUDIO_METADATA_DIRECTORY+'/'):],'status':'response_received'}
    if len(matches)!=1 or any(matches[0].get(k)!=v for k,v in expected.items()):raise ValueError('Audio cached hardware README provenance differs')
    item['prior_receipt']={'file':AUDIO_METADATA_DIRECTORY+'/metadata-receipt.json','sha256':AUDIO_METADATA_PINS['metadata-receipt.json']}
    cache['files'].update(files)
    cache['prior_acquisition']['additional_metadata_batch']={
        'receipt':AUDIO_METADATA_DIRECTORY+'/metadata-receipt.json','sha256':AUDIO_METADATA_PINS['metadata-receipt.json'],
        'execution':AUDIO_METADATA_DIRECTORY+'/metadata-execution.json','execution_sha256':AUDIO_METADATA_PINS['metadata-execution.json'],
        'retained_file_count':1,'retained_bytes':292,'original_batch_requests':3,'original_batch_bytes':28855,
        'wall_seconds':execution['wall_seconds'],'full_cpu_seconds':execution['full_cpu_seconds'],
        'bootstrap_emission_allowance_seconds':3,'accounting':'Entire three-text batch retained conservatively; prior root metadata timing remains unmeasured, not zero.'}
    return cache


def uv_license_cache(root, cfg):
    """Explicit fixed prior licence evidence only; no cache search or fallback."""
    from autorouter.placement_clearance import read_bytes
    if cfg['profile_id'] != 'uv-dosimeter':raise ValueError('UV licence reuse requires UV profile')
    proof_name=UV_CACHE_DIRECTORY+'/fetch-result.json'
    proof_raw=read_bytes(shared.contained(root,root/shared.safe(proof_name)),64*1024)
    if shared.sha(proof_raw)!=UV_CACHE_RECEIPT_SHA256:raise ValueError('UV cached licence receipt pin differs')
    proof=shared.decode(proof_raw)
    requests=proof.get('requests',[])
    if (proof.get('passed') is not True or proof.get('source_profile_sha256')!=UV_CACHE_PROFILE_SHA256
            or proof.get('new_network_requests')!=3 or proof.get('received_bytes')!=35778
            or len(requests)!=3 or {r.get('source_path') for r in requests}!=set(UV_LICENSE_NAMES)):
        raise ValueError('UV cached licence receipt scope differs')
    rows={r['source_path']:r for r in cfg['rows']}; witness={proof_name:shared.sha(proof_raw)}; caps={proof_name:64*1024}
    files=_cache_bodies(root,cfg,UV_LICENSE_NAMES,UV_CACHE_DIRECTORY+'/licenses',witness,caps)
    for name in UV_LICENSE_NAMES:
        row=rows[name]; prior=next(r for r in requests if r['source_path']==name);info=files[name]
        if (prior.get('url')!=row['raw_url'] or prior.get('final_url')!=row['raw_url']
                or prior.get('http_status')!=200 or prior.get('payload_verified') is not True
                or prior.get('bytes')!=row['bytes'] or prior.get('received_bytes')!=row['bytes']
                or prior.get('git_blob_sha1')!=row['git_blob_sha1']
                or prior.get('sha256')!=info['sha256'] or prior.get('response_sha256')!=info['sha256']):
            raise ValueError('UV cached licence response provenance differs')
    return {'files':files,'witness':witness,'caps':caps,'prior_acquisition':{
        'receipt':proof_name,'sha256':shared.sha(proof_raw),'new_network_requests':3,'received_bytes':35778,
        'wall_seconds':proof['wall_seconds'],'full_cpu_seconds':proof['full_cpu_seconds'],
        'bootstrap_emission_allowance_seconds':proof['bootstrap_emission_allowance_seconds']}}


def check_uv_cache(root, cache):
    if cache is None:return
    from autorouter.placement_clearance import read_bytes
    for name,pin in cache['witness'].items():
        if shared.sha(read_bytes(shared.contained(root,root/shared.safe(name)),cache['caps'][name]))!=pin:
            raise ValueError(cache.get('label','UV cached licence')+' input changed during acquisition')

SUNX_PROFILE = {'schema': 1,
 'profile_id': 'sunx-v21',
 'project_id': 'sunx-v21',
 'repository': 'Open-Air-Foundation/pcb-module-SUNX',
 'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
 'rows': [{'source_path': 'LICENSE',
           'bytes': 20138,
           'git_blob_sha1': '2d58298e6eda10e7204abb52722efbc840db2390',
           'sha256': '28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5',
           'mode': '100644',
           'repository': 'Open-Air-Foundation/pcb-module-SUNX',
           'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
           'destination': 'sunx-v21/LICENSE',
           'raw_url': 'https://raw.githubusercontent.com/Open-Air-Foundation/pcb-module-SUNX/9cee7482c6b3bbd63293f53376335bed6659457f/LICENSE',
           'blob_url': 'https://github.com/Open-Air-Foundation/pcb-module-SUNX/blob/9cee7482c6b3bbd63293f53376335bed6659457f/LICENSE',
           'rights_basis': 'Pinned SUNX v2.1 README explicitly licenses hardware design files CC-BY-SA4; '
                           'exact full LICENSE and AirGradient attribution preserved. WIP '
                           'untested/unreleased branch, no Native/routing/physical/electrical or '
                           'independent-ancestry claim. Mixed KiCad6/9 stock model paths and individual '
                           'library/asset title chains remain unclosed; no models/scripts/firmware acquired. '
                           'Existing PRL is mandatory unchanged original input.'},
          {'source_path': 'README.md',
           'bytes': 2825,
           'git_blob_sha1': '8a3119d0fac301538ec37d9a0520c3bfeed057ec',
           'sha256': '4fc8717b8dc5aaf2992688677378416f2bd5003a8f0d8cc3d5b160e9f575e6b8',
           'mode': '100644',
           'repository': 'Open-Air-Foundation/pcb-module-SUNX',
           'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
           'destination': 'sunx-v21/README.md',
           'raw_url': 'https://raw.githubusercontent.com/Open-Air-Foundation/pcb-module-SUNX/9cee7482c6b3bbd63293f53376335bed6659457f/README.md',
           'blob_url': 'https://github.com/Open-Air-Foundation/pcb-module-SUNX/blob/9cee7482c6b3bbd63293f53376335bed6659457f/README.md',
           'rights_basis': 'Pinned SUNX v2.1 README explicitly licenses hardware design files CC-BY-SA4; '
                           'exact full LICENSE and AirGradient attribution preserved. WIP '
                           'untested/unreleased branch, no Native/routing/physical/electrical or '
                           'independent-ancestry claim. Mixed KiCad6/9 stock model paths and individual '
                           'library/asset title chains remain unclosed; no models/scripts/firmware acquired. '
                           'Existing PRL is mandatory unchanged original input.'},
          {'source_path': 'sunx/sunx.kicad_pcb',
           'bytes': 89260,
           'git_blob_sha1': '87d2f31e79ad9bd81df3538bec13c31aeb55b467',
           'sha256': 'db90383cd5707a208dbeaca1205c34309108da173c319c32968d67b96a617d9f',
           'mode': '100644',
           'repository': 'Open-Air-Foundation/pcb-module-SUNX',
           'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
           'destination': 'sunx-v21/sunx/sunx.kicad_pcb',
           'raw_url': 'https://raw.githubusercontent.com/Open-Air-Foundation/pcb-module-SUNX/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_pcb',
           'blob_url': 'https://github.com/Open-Air-Foundation/pcb-module-SUNX/blob/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_pcb',
           'rights_basis': 'Pinned SUNX v2.1 README explicitly licenses hardware design files CC-BY-SA4; '
                           'exact full LICENSE and AirGradient attribution preserved. WIP '
                           'untested/unreleased branch, no Native/routing/physical/electrical or '
                           'independent-ancestry claim. Mixed KiCad6/9 stock model paths and individual '
                           'library/asset title chains remain unclosed; no models/scripts/firmware acquired. '
                           'Existing PRL is mandatory unchanged original input.'},
          {'source_path': 'sunx/sunx.kicad_prl',
           'bytes': 2418,
           'git_blob_sha1': '20d30c2bbd984629c7df3c7ade4518617ca0101b',
           'sha256': '06b428e24ace7b1ebd945ffed42ab7593611d402902643a66ca172456c34a3f6',
           'mode': '100644',
           'repository': 'Open-Air-Foundation/pcb-module-SUNX',
           'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
           'destination': 'sunx-v21/sunx/sunx.kicad_prl',
           'raw_url': 'https://raw.githubusercontent.com/Open-Air-Foundation/pcb-module-SUNX/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_prl',
           'blob_url': 'https://github.com/Open-Air-Foundation/pcb-module-SUNX/blob/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_prl',
           'rights_basis': 'Pinned SUNX v2.1 README explicitly licenses hardware design files CC-BY-SA4; '
                           'exact full LICENSE and AirGradient attribution preserved. WIP '
                           'untested/unreleased branch, no Native/routing/physical/electrical or '
                           'independent-ancestry claim. Mixed KiCad6/9 stock model paths and individual '
                           'library/asset title chains remain unclosed; no models/scripts/firmware acquired. '
                           'Existing PRL is mandatory unchanged original input.'},
          {'source_path': 'sunx/sunx.kicad_pro',
           'bytes': 14778,
           'git_blob_sha1': '025777fdc3ad644e17e1c978e5af41f83e51eee2',
           'sha256': 'fbaa97c6f1076ceafcae734d8217dfc4cb8e25b71634845bf0aeda885da5b9bb',
           'mode': '100644',
           'repository': 'Open-Air-Foundation/pcb-module-SUNX',
           'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
           'destination': 'sunx-v21/sunx/sunx.kicad_pro',
           'raw_url': 'https://raw.githubusercontent.com/Open-Air-Foundation/pcb-module-SUNX/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_pro',
           'blob_url': 'https://github.com/Open-Air-Foundation/pcb-module-SUNX/blob/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_pro',
           'rights_basis': 'Pinned SUNX v2.1 README explicitly licenses hardware design files CC-BY-SA4; '
                           'exact full LICENSE and AirGradient attribution preserved. WIP '
                           'untested/unreleased branch, no Native/routing/physical/electrical or '
                           'independent-ancestry claim. Mixed KiCad6/9 stock model paths and individual '
                           'library/asset title chains remain unclosed; no models/scripts/firmware acquired. '
                           'Existing PRL is mandatory unchanged original input.'},
          {'source_path': 'sunx/sunx.kicad_sch',
           'bytes': 61245,
           'git_blob_sha1': '8745b998719fe7cc64b17de181956da1bb3460c7',
           'sha256': '095fd2711cbeb1839099c9a10f5e1791c2910c6da463972f910b4996d3fc6a49',
           'mode': '100644',
           'repository': 'Open-Air-Foundation/pcb-module-SUNX',
           'commit': '9cee7482c6b3bbd63293f53376335bed6659457f',
           'destination': 'sunx-v21/sunx/sunx.kicad_sch',
           'raw_url': 'https://raw.githubusercontent.com/Open-Air-Foundation/pcb-module-SUNX/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_sch',
           'blob_url': 'https://github.com/Open-Air-Foundation/pcb-module-SUNX/blob/9cee7482c6b3bbd63293f53376335bed6659457f/sunx/sunx.kicad_sch',
           'rights_basis': 'Pinned SUNX v2.1 README explicitly licenses hardware design files CC-BY-SA4; '
                           'exact full LICENSE and AirGradient attribution preserved. WIP '
                           'untested/unreleased branch, no Native/routing/physical/electrical or '
                           'independent-ancestry claim. Mixed KiCad6/9 stock model paths and individual '
                           'library/asset title chains remain unclosed; no models/scripts/firmware acquired. '
                           'Existing PRL is mandatory unchanged original input.'}],
 'directories': ['sunx'],
 'board_path': 'sunx/sunx.kicad_pcb',
 'output_prefix': 'sunx-v21-demo-',
 'default_output': '.data/sunx-v21-demo-001',
 'file_count': 6,
 'bytes': 190664,
 'max_requests': 6,
 'network_byte_cap': 190670,
 'max_single_response_bytes': 89261,
 'output_byte_cap': 2097152,
 'wall_budget_seconds': 300,
 'cpu_budget_seconds': 300,
 'request_wall_seconds': 30,
 'native_packet_notice_copies': {'sunx/_licenses/creator/LICENSE': 'LICENSE',
                                 'sunx/_licenses/creator/README.md': 'README.md'},
 'native_packet_files': 8,
 'native_packet_bytes': 213627,
 'development_exposed': True,
 'independent_ancestry_established': False,
 'native_validation_performed_by_fetch': False,
 'raw_assets_public': False,
 'warnings': ['Exactly six originals including existing PRL; native notice packet adds two byte-identical '
              'creator notice copies.',
              'KiCad9 SUNX v2.1 branch is explicitly WIP, untested and unreleased; README retains older-main '
              'prose. No routing or fabrication approval.',
              'Root hardware CC-BY-SA4 scope and AirGradient attribution retained; individual '
              'model/library/asset rights and ancestry remain unclosed.',
              'Actual original Native saved refill/fullSCH is not established by metadata or fetch. All '
              'findings and source constraints must remain visible.',
              'Mixed KICAD6/KICAD9 stock model variables remain exact and unresolved; no '
              'models/libraries/assets/scripts/firmware downloaded or executed.',
              'Source6/190664B and native8/213627B are finite inventories, not a production-support or '
              'independent-family count.']}

IR_OBSTACLE_PROFILE = {'schema': 1,
 'profile_id': 'ir-obstacle',
 'project_id': 'ir-obstacle',
 'repository': 'AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB',
 'commit': '6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',
 'rows': [{'source_path': 'LICENSE',
           'bytes': 1077,
           'git_blob_sha1': '9728088fb91be640565f11bd9622373f992b9ee2',
           'sha256': '7a9ff699e91b9acf1cf6747e72f82fab1ec25ead316ece85e14b8043200ebb74',
           'mode': '100644',
           'repository': 'AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB',
           'commit': '6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',
           'destination': 'ir-obstacle/LICENSE',
           'raw_url': 'https://raw.githubusercontent.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/LICENSE',
           'blob_url': 'https://github.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/blob/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/LICENSE',
           'rights_basis': 'Pinned README explicitly applies MIT to repository project files, including '
                           'the listed PCB/PRO/SCH, to the extent the author owns the rights; matching MIT '
                           'copyright2026 Ahmed Osama Metwally and full README retained. '
                           'Design-only/unfabricated; no Native/routing/electrical/physical or '
                           'independent-ancestry claim. Unique embedded LOGO and stock model/library title '
                           'chains remain unclosed; no images/models/libraries/scripts acquired. Prior '
                           'source research197.97749304771423s exceeded180s and remains exposed.'},
          {'source_path': 'README.md',
           'bytes': 3167,
           'git_blob_sha1': '06dc3c56933a13fae59d7d601a3db1e26edff72d',
           'sha256': '1dd84f03c05e371507fda0f5c3be237eea52db5d991858e9c1f75e9327205926',
           'mode': '100644',
           'repository': 'AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB',
           'commit': '6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',
           'destination': 'ir-obstacle/README.md',
           'raw_url': 'https://raw.githubusercontent.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/README.md',
           'blob_url': 'https://github.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/blob/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/README.md',
           'rights_basis': 'Pinned README explicitly applies MIT to repository project files, including '
                           'the listed PCB/PRO/SCH, to the extent the author owns the rights; matching MIT '
                           'copyright2026 Ahmed Osama Metwally and full README retained. '
                           'Design-only/unfabricated; no Native/routing/electrical/physical or '
                           'independent-ancestry claim. Unique embedded LOGO and stock model/library title '
                           'chains remain unclosed; no images/models/libraries/scripts acquired. Prior '
                           'source research197.97749304771423s exceeded180s and remains exposed.'},
          {'source_path': 'KiCad/IR_Sensor.kicad_pcb',
           'bytes': 159647,
           'git_blob_sha1': 'cf3635b8d4a7e79e91626dd6d46a1697065dc54a',
           'sha256': 'f52eca1575d9438b803a672088de98436e9a299b6014a3bbafca963974431774',
           'mode': '100644',
           'repository': 'AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB',
           'commit': '6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',
           'destination': 'ir-obstacle/KiCad/IR_Sensor.kicad_pcb',
           'raw_url': 'https://raw.githubusercontent.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/KiCad/IR_Sensor.kicad_pcb',
           'blob_url': 'https://github.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/blob/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/KiCad/IR_Sensor.kicad_pcb',
           'rights_basis': 'Pinned README explicitly applies MIT to repository project files, including '
                           'the listed PCB/PRO/SCH, to the extent the author owns the rights; matching MIT '
                           'copyright2026 Ahmed Osama Metwally and full README retained. '
                           'Design-only/unfabricated; no Native/routing/electrical/physical or '
                           'independent-ancestry claim. Unique embedded LOGO and stock model/library title '
                           'chains remain unclosed; no images/models/libraries/scripts acquired. Prior '
                           'source research197.97749304771423s exceeded180s and remains exposed.'},
          {'source_path': 'KiCad/IR_Sensor.kicad_pro',
           'bytes': 15157,
           'git_blob_sha1': '0f3d9aed84962363a8848577c76dff4210d01c56',
           'sha256': '0393908f5263db9c95388db7d749115280350ae4b6a7dc44afba203aea3a2f8a',
           'mode': '100644',
           'repository': 'AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB',
           'commit': '6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',
           'destination': 'ir-obstacle/KiCad/IR_Sensor.kicad_pro',
           'raw_url': 'https://raw.githubusercontent.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/KiCad/IR_Sensor.kicad_pro',
           'blob_url': 'https://github.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/blob/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/KiCad/IR_Sensor.kicad_pro',
           'rights_basis': 'Pinned README explicitly applies MIT to repository project files, including '
                           'the listed PCB/PRO/SCH, to the extent the author owns the rights; matching MIT '
                           'copyright2026 Ahmed Osama Metwally and full README retained. '
                           'Design-only/unfabricated; no Native/routing/electrical/physical or '
                           'independent-ancestry claim. Unique embedded LOGO and stock model/library title '
                           'chains remain unclosed; no images/models/libraries/scripts acquired. Prior '
                           'source research197.97749304771423s exceeded180s and remains exposed.'},
          {'source_path': 'KiCad/IR_Sensor.kicad_sch',
           'bytes': 43853,
           'git_blob_sha1': 'd32905d4a5980f35128d2f5fd81c220e552edcce',
           'sha256': 'fb2ead949c4005eda55d7ff8e48ff39293ad096bd9f1ca12a3c623fc62915786',
           'mode': '100644',
           'repository': 'AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB',
           'commit': '6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',
           'destination': 'ir-obstacle/KiCad/IR_Sensor.kicad_sch',
           'raw_url': 'https://raw.githubusercontent.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/KiCad/IR_Sensor.kicad_sch',
           'blob_url': 'https://github.com/AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB/blob/6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899/KiCad/IR_Sensor.kicad_sch',
           'rights_basis': 'Pinned README explicitly applies MIT to repository project files, including '
                           'the listed PCB/PRO/SCH, to the extent the author owns the rights; matching MIT '
                           'copyright2026 Ahmed Osama Metwally and full README retained. '
                           'Design-only/unfabricated; no Native/routing/electrical/physical or '
                           'independent-ancestry claim. Unique embedded LOGO and stock model/library title '
                           'chains remain unclosed; no images/models/libraries/scripts acquired. Prior '
                           'source research197.97749304771423s exceeded180s and remains exposed.'}],
 'directories': ['KiCad'],
 'board_path': 'KiCad/IR_Sensor.kicad_pcb',
 'output_prefix': 'ir-obstacle-demo-',
 'default_output': '.data/ir-obstacle-demo-001',
 'file_count': 5,
 'bytes': 222901,
 'max_requests': 5,
 'network_byte_cap': 222906,
 'max_single_response_bytes': 159648,
 'output_byte_cap': 2097152,
 'wall_budget_seconds': 300,
 'cpu_budget_seconds': 300,
 'request_wall_seconds': 30,
 'native_packet_notice_copies': {'KiCad/_licenses/creator/LICENSE': 'LICENSE',
                                 'KiCad/_licenses/creator/README.md': 'README.md'},
 'native_packet_files': 7,
 'native_packet_bytes': 227145,
 'development_exposed': True,
 'independent_ancestry_established': False,
 'native_validation_performed_by_fetch': False,
 'raw_assets_public': False,
 'warnings': ['Exactly five original creator files: full README/MIT notice and PCB/PRO/flatSCH; source has '
              'no PRL. Native packet adds only two byte-identical notice copies.',
              'README licenses repository project files under the included MIT to the extent of author '
              'rights; embedded artwork/model/library provenance remains unclosed.',
              'Publisher says design-only, unfabricated and untested. Original Native '
              'saved-refill/fullSCH, circuit behavior and physical functionality remain unverified.',
              'One Default class, ordinary pads and rectangle are static observations only. Keep the '
              'original GND zone, clearances, thermal settings, model declarations and all findings '
              'unchanged.',
              'No source models/libraries/images/firmware/upload instructions/scripts acquired or '
              'executed. No routing/production/independent-family claim.',
              'Prior exposed research used21HTTP/1294070B; completed record197.97749304771423s '
              'exceeded180s overall research cap. This failure is retained, not reset by acquisition.']}

def fixed_profile(profile_id='led'):
    if profile_id=='ir-obstacle':return copy.deepcopy(IR_OBSTACLE_PROFILE)
    if profile_id=='sunx-v21':return copy.deepcopy(SUNX_PROFILE)
    if profile_id=='pico-flipper':return copy.deepcopy(FLIPPER_PROFILE)
    if profile_id=='audio-player-my1690x':return copy.deepcopy(AUDIO_PROFILE)
    if profile_id=='navigation-switch':return copy.deepcopy(NAV_PROFILE)
    if profile_id=='uv-dosimeter':return copy.deepcopy(UV_PROFILE)
    if profile_id=='cellscan':return copy.deepcopy(CELL_SCAN_PROFILE)
    if profile_id=='arcdice':return copy.deepcopy(ARC_PROFILE)
    if profile_id=='analog-filter':return copy.deepcopy(ANALOG_PROFILE)
    if profile_id!='led':raise ValueError('unknown fixed public source profile')
    return {'profile_id':'led','rows':copy.deepcopy(ROWS),'directories':[],'bytes':161071,
            'network_byte_cap':NETWORK_BYTES,'output_prefix':'led-demo-','default_output':'.data/led-demo-001',
            'native_packet_notice_copies':{},'native_packet_files':0,'native_packet_bytes':0}

def destination(root,name,*,profile_id='led'):
    root=Path(root).absolute();relative=shared.safe(name);prefix=fixed_profile(profile_id)['output_prefix']
    if len(relative.parts)!=2 or relative.parts[0]!='.data' or not re.fullmatch(re.escape(prefix)+r'[a-z0-9][a-z0-9-]{0,47}',relative.parts[1]):
        raise ValueError('fresh .data/'+prefix+'NAME directory required')
    return shared.contained(root,root/relative)

def verify_project(path,*,profile_id='led',native_packet=False):
    """Read-only fixed original source verifier, independent of research cache."""
    cfg=fixed_profile(profile_id)
    if type(native_packet) is not bool or native_packet and not cfg['native_packet_notice_copies']:raise ValueError('unsupported notice-packet request')
    path=Path(path).absolute();shared.contained(path,path)
    rows=cfg['rows'];count=cfg.get('file_count',5);cap=cfg.get('output_byte_cap',OUTPUT_BYTES)
    if len(rows)!=count or len({r['source_path'] for r in rows})!=count:raise ValueError('fixed source population differs')
    copies=cfg['native_packet_notice_copies'] if native_packet else {};directories=list(cfg['directories'])
    names={r['source_path'] for r in rows}|set(copies)
    if copies:
        directories=sorted(set(directories)|{str(parent) for name in copies for parent in Path(name).parents if str(parent)!='.'})
    before=shared.inventory(path,cap=cap)
    if set(before['files'])!=names or before['directories']!=directories:raise ValueError('exact five original LED project files required' if profile_id=='led' else 'exact fixed original source/notice project required')
    # Derive SHA256 from actual bytes validated against size/Git-blob pins. Some
    # first-acquisition profiles intentionally have no prior SHA256 for a row.
    expected={row['source_path']:shared.payload(row,shared.bounded(path/shared.safe(row['source_path']))) for row in rows}
    for name,origin in copies.items():
        row=next(r for r in rows if r['source_path']==origin)
        copied=shared.payload(row,shared.bounded(path/shared.safe(name)))
        if copied!=expected[origin]:raise ValueError('creator notice copy differs from original bytes')
        expected[name]=copied
    if before['files']!=expected:raise ValueError('fixed source bytes changed during verification')
    shared.inventory(path,before,cap=cap)
    return {'schema':1,'verified':True,'project':str(path),'repository':rows[0]['repository'],
        'source_commit':rows[0]['commit'],'file_count':len(expected),'bytes':sum(x['bytes'] for x in expected.values()),
        'files':expected,'native_accepted':False}

def capture_native_source(profile_id,*,root=ROOT):
    """Read exact originals and notice packet without staging or fallback."""
    cfg=fixed_profile(profile_id)
    if not cfg['native_packet_notice_copies']:raise ValueError('fixed native notice packet required')
    base=shared.contained(Path(root).absolute(),Path(root).absolute()/cfg['default_output'])
    raw=base/'project';native=base/'native-project'
    original=verify_project(raw,profile_id=profile_id)
    packet=verify_project(native,profile_id=profile_id,native_packet=True)
    files={name:shared.bounded(native/shared.safe(name)) for name in packet['files']}
    if (any({'bytes':len(content),'sha256':shared.sha(content)}!=packet['files'][name] for name,content in files.items())
            or verify_project(raw,profile_id=profile_id)!=original
            or verify_project(native,profile_id=profile_id,native_packet=True)!=packet):
        raise ValueError('fixed source changed during read-only capture')
    return native,files

class OwnedFile:
    """Guard delayed exclusive transport creation with an owned parent descriptor."""
    def __init__(self,path,owned,directory_fd):self.path=path;self.owned=owned;self.directory_fd=directory_fd
    @contextmanager
    def open(self,*args,**kwargs):
        if args!=('xb',) or kwargs:raise ValueError('exclusive binary response creation required')
        self.owned();fd=os.open(self.path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0),0o600,dir_fd=self.directory_fd)
        try:
            self.owned();opened=os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):raise ValueError('regular response file required')
            with os.fdopen(fd,'wb',closefd=False) as stream:
                yield stream;stream.flush();self.owned()
            named=os.stat(self.path.name,dir_fd=self.directory_fd,follow_symlinks=False)
            if (named.st_dev,named.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('response file replaced')
        finally:os.close(fd)
    def exists(self):
        self.owned()
        try:os.stat(self.path.name,dir_fd=self.directory_fd,follow_symlinks=False);return True
        except FileNotFoundError:return False

def fetch_demo(name,*,profile_id='led',fetch=False,root=ROOT,transport=shared.fetch_one,started=None,cpu_started=None,reuse_uv_licenses=False,reuse_navigation_notices=False,reuse_audio_notices=False,reuse_flipper_notices=False):
    started=time.monotonic() if started is None else started;cpu_started=cpu() if cpu_started is None else cpu_started
    cfg=fixed_profile(profile_id);root=Path(root).absolute();out=destination(root,name,profile_id=profile_id);rows=cfg['rows'];network_cap=cfg['network_byte_cap'];planned=cfg['bytes'];nested=bool(cfg['native_packet_notice_copies'])
    count=cfg.get('file_count',5);max_requests=cfg.get('max_requests',5);output_cap=cfg.get('output_byte_cap',OUTPUT_BYTES)
    if len(rows)!=count or count!=max_requests:raise ValueError('fixed source/request population differs')
    if type(reuse_uv_licenses) is not bool or reuse_uv_licenses and profile_id!='uv-dosimeter':raise ValueError('explicit UV-only licence reuse flag required')
    if type(reuse_navigation_notices) is not bool or reuse_navigation_notices and profile_id!='navigation-switch':raise ValueError('explicit Navigation-only notice reuse flag required')
    if type(reuse_audio_notices) is not bool or reuse_audio_notices and profile_id!='audio-player-my1690x':raise ValueError('explicit Audio-only notice reuse flag required')
    if type(reuse_flipper_notices) is not bool or reuse_flipper_notices and profile_id!='pico-flipper':raise ValueError('explicit Flipper-only notice reuse flag required')
    direct=profile_id in ('navigation-switch','audio-player-my1690x','pico-flipper');direct_label='Flipper' if profile_id=='pico-flipper' else 'Audio' if profile_id=='audio-player-my1690x' else 'Navigation'
    if direct and (cfg['directories']!=['Hardware'] or any(shared.safe(r['source_path']).parent not in (Path('.'),Path('Hardware')) for r in rows)):
        raise ValueError('fixed '+direct_label+' direct response hierarchy differs')
    if out.exists():raise ValueError('destination already exists; preserve earlier attempts')
    if fetch is not True:
        plan={'schema':1,'action':'plan_only','destination':str(out),'source_commit':rows[0]['commit'],
            'planned_files':count,'planned_bytes':planned,'network_requests':0,'native_accepted':False,
            'planned_network_requests':count-(3 if reuse_uv_licenses else 2 if reuse_navigation_notices else 3 if reuse_audio_notices else 2 if reuse_flipper_notices else 0),'planned_cached_licenses':3 if reuse_uv_licenses else 0,
            'command':'scripts/fetch_led_demo.py --project '+profile_id+' --fetch --output '+name+(' --reuse-uv-licenses' if reuse_uv_licenses else ' --reuse-navigation-notices' if reuse_navigation_notices else ' --reuse-audio-notices' if reuse_audio_notices else ' --reuse-flipper-notices' if reuse_flipper_notices else '')}
        if direct:plan['planned_cached_notices']=2 if reuse_navigation_notices or reuse_flipper_notices else 3 if reuse_audio_notices else 0
        return plan
    cache=uv_license_cache(root,cfg) if reuse_uv_licenses else navigation_notice_cache(root,cfg) if reuse_navigation_notices else audio_notice_cache(root,cfg) if reuse_audio_notices else flipper_notice_cache(root,cfg) if reuse_flipper_notices else None
    extra=ARC_MATERIAL if nested else ()
    def material():return {n:shared.sha(shared.bounded(shared.contained(root,root/n))) for n in (*MATERIAL,*extra)}
    witness=material();owner={};project_owner={};native_owner={};response_owner={};completed={};requests=[];received={};raw_fd=None;hardware_owner={};hardware_fd=None
    def owned():
        h.owned_destination(owner)
        for scope in (project_owner,native_owner,response_owner,hardware_owner):
            if scope.get('created'):h.owned_destination(scope)
        if raw_fd is not None:
            identity=os.fstat(raw_fd);scope=response_owner if nested and not direct else project_owner
            if (identity.st_dev,identity.st_ino)!=scope['directory_identity']:raise ValueError('owned response parent descriptor differs')
        if hardware_fd is not None:
            identity=os.fstat(hardware_fd);named=os.stat('Hardware',dir_fd=raw_fd,follow_symlinks=False)
            if (not stat.S_ISDIR(named.st_mode) or (named.st_dev,named.st_ino)!=hardware_owner['directory_identity']
                    or (identity.st_dev,identity.st_ino)!=hardware_owner['directory_identity']):raise ValueError('owned '+direct_label+' response parent differs')
        return out
    def remaining():
        left=min(SECONDS-(time.monotonic()-started),SECONDS-(cpu()-cpu_started))
        if left<=0:raise TimeoutError('whole LED demo acquisition wall/CPU budget exhausted')
        return left
    shared.contained(root,out.parent);out.parent.mkdir(exist_ok=True);shared.contained(root,out.parent);out.mkdir();h.capture_destination(owner,out);project=out/'project'
    raw_root=out/'responses' if nested and not direct else project;raw_root.mkdir();h.capture_destination(response_owner if nested and not direct else project_owner,raw_root)
    raw_fd=os.open(raw_root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0))
    try:
        owned()
        if direct:
            os.mkdir('Hardware',dir_fd=raw_fd)
            hardware_fd=os.open('Hardware',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0),dir_fd=raw_fd)
            h.capture_destination(hardware_owner,project/'Hardware');owned()
    except BaseException:
        if hardware_fd is not None:os.close(hardware_fd);hardware_fd=None
        os.close(raw_fd);raw_fd=None;raise
    record={'schema':1,'kind':'fixed_public_'+profile_id.replace('-','_')+'_source_acquisition','status':'running','accepted':False,
        'native_accepted':False,'physical_electrical_validation':False,'routing_support':'unqualified',
        'destination':str(out),'project':str(project),'repository':rows[0]['repository'],'source_commit':rows[0]['commit'],
        'source_profile':('fixed '+('six' if count==6 else 'five' if count==5 else str(count))+'-file public '+('ArcDice' if profile_id=='arcdice' else profile_id)+' selection') if nested else 'licensed_acquisition_v7 fixed five-file public LED selection',
        'runtime_sha256':witness,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
        'max_requests':max_requests,'network_byte_cap':network_cap,'output_byte_cap':output_cap,
        'planned_files':count,'planned_bytes':planned,'requests':requests,'files':[],
        'new_network_requests':0,'received_bytes':0,'engine_jobs':0,'native_jobs':0,'models_downloaded':0,
        'independent_ancestry_established':False,'split':'development-exposed',
        'source_files_exact':False,'original_source_constraints_modified':False,
        'warnings':['Small seven-component support/control; no broad routing superiority.',
          'Copy of the same selected LED source, not an additional independent circuit/family.',
          'Original native loading/DRC/complete schematic parity and electrical function are unverified.',
          'Creator makes no fabrication or physical testing claim.',
          'Root MIT/README retained; README gives no separate hardware-license sentence.',
          'Five unique stock-model references remain unclosed; no models/libraries/firmware downloaded.',
          'Original missing_tuning_profile warning and track_on_post_machined_layer error remain unchanged.'],
        'accounting':'Controller clock begins before project imports for CLI. Stored wall/fullCPU sample precedes final publication; final cap covers publication/readback. No speedup or routing-quality claim.'}
    record.update(transfer_count=0,reused_input_files=0,reused_input_bytes=0,cache_inputs_current=True,prior_cache_acquisition=None if cache is None else cache['prior_acquisition'])
    if direct:record['response_layout']='project'
    if nested:record.update(warnings=cfg['warnings'],native_project=str(out/'native-project'),native_packet_prepared=False,native_packet_hashes=None)
    def exact_source():
        if nested:
            if not project_owner.get('created') or not native_owner.get('created'):return False
            verify_project(project,profile_id=profile_id);verified=verify_project(out/'native-project',profile_id=profile_id,native_packet=True)
            if verified['files']!=record['native_packet_hashes']:raise ValueError('native notice packet differs')
            return True
        return len(completed)==count
    def scan():return shared.inventory(owned(),cap=output_cap)
    def stable():
        owned();remaining();check_uv_cache(root,cache)
        if material()!=witness:raise ValueError('acquisition implementation changed during execution')
        actual=scan()['files'];allowed={r['artifact'] for r in requests}|set(completed)|{'result.json','result.json.partial'}
        if nested:
            # Preserve legitimate partial owned copies on failure without claiming completeness.
            allowed|={'project/'+r['source_path'] for r in rows}|{'native-project/'+r['source_path'] for r in rows}|{'native-project/'+n for n in cfg['native_packet_notice_copies']}
        if record['status'] in {'invalidated','failed','cancelled'}:
            allowed|={n for n in actual if re.fullmatch(r'(?:invalidated-result|interrupted-result)-[0-9a-f]{32}\.json',n)}
        if set(actual)-allowed:raise ValueError('unexpected output member')
        for n,info in completed.items():
            if actual.get(n)!=info:raise ValueError('completed source file changed: '+n)
        if record['status']=='acquired_unqualified':
            if not exact_source():raise ValueError('complete source population required')
            verify_project(project,profile_id=profile_id)
        remaining();owned()
    def account():
        cache_current=True
        try:check_uv_cache(root,cache)
        except Exception:cache_current=False  # Metadata only; stable() still rejects.
        owned();actual=scan();record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu()-cpu_started,output_bytes=actual['bytes'],
          new_network_requests=sum(x.get('transport')=='network' for x in requests),
          received_bytes=sum(x.get('received_bytes',0) for x in requests if x.get('transport')=='network'),
          transfer_count=len(requests),reused_input_files=sum(x.get('status')=='verified_cache_copied' for x in requests),
          reused_input_bytes=sum(x.get('cached_bytes',0) for x in requests),cache_inputs_current=cache_current)
        record['source_files_exact']=exact_source() and all(actual['files'].get(n)==info for n,info in completed.items())
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and actual['bytes']<=output_cap and len(requests)<=max_requests and record['received_bytes']<=network_cap
        if not record['within_budget'] or record['status']=='acquired_unqualified' and (not record['source_files_exact'] or not cache_current):record.update(status='failed',accepted=False)
    try:
        stable()
        for index,row in enumerate(rows):
            stable();artifact=('responses/'+str(index+1).zfill(2)+'.payload') if nested and not direct else 'project/'+row['source_path'];req={'index':index,'source_path':row['source_path'],'artifact':artifact,'transport':'verified_cache' if cache is not None and row['source_path'] in cache['files'] else 'network'};requests.append(req)
            response_fd=hardware_fd if direct and shared.safe(row['source_path']).parent==Path('Hardware') else raw_fd
            allowance=network_cap-sum(r.get('received_bytes',0) for r in requests)
            if req['transport']=='verified_cache':
                item=cache['files'][row['source_path']];raw=item['raw']
                with OwnedFile(out/artifact,owned,response_fd).open('xb') as stream:stream.write(raw)
                req.update(status='verified_cache_copied',received_bytes=0,cached_bytes=len(raw),response_sha256=shared.sha(raw),
                    cache_body={'file':item['path'],'sha256':item['sha256']},prior_receipt=item.get('prior_receipt',{'file':cache['prior_acquisition']['receipt'],'sha256':cache['prior_acquisition']['sha256']}))
            else:raw=transport(row,req,OwnedFile(out/artifact,owned,response_fd),allowance,remaining)
            owned();remaining()
            if sum(r.get('received_bytes',0) for r in requests)>network_cap:raise ValueError('network byte cap exceeded')
            info=shared.payload(row,raw)
            if shared.bounded(out/artifact)!=raw or req.get('response_sha256')!=shared.sha(raw):raise ValueError('response artifact/returned payload differ')
            completed[artifact]=info;received[row['source_path']]=raw;record['files'].append({**row,**info});stable()
        if nested:
            from experiments.placement_handoff_native_v1.driver import copy_bytes
            owned()
            if direct:verify_project(project,profile_id=profile_id)
            else:project_owner.update(copy_bytes(received,project,expected_parent_owner=owner))
            owned()
            packet=dict(received)
            for name,origin in cfg['native_packet_notice_copies'].items():packet[name]=received[origin]
            native_owner.update(copy_bytes(packet,out/'native-project',expected_parent_owner=owner));owned()
            for prefix,values in [('project',received),('native-project',packet)]:
                for name,raw in values.items():completed[prefix+'/'+name]={'bytes':len(raw),'sha256':shared.sha(raw)}
            record.update(native_packet_prepared=True,native_packet_hashes=verify_project(out/'native-project',profile_id=profile_id,native_packet=True)['files'])
        if profile_id=='uv-dosimeter':record['warnings'][0]='Exactly eleven original source files acquired; native/routing qualification remains pending.'
        record['status']='acquired_unqualified'
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',first_failure=type(exc).__name__+': '+str(exc))
    finally:
        if hardware_fd is not None:os.close(hardware_fd);hardware_fd=None
        if raw_fd is not None:os.close(raw_fd);raw_fd=None
    publication.publish(out,record,stable,account,remaining,owned=owned)
    try:
        owned();remaining();stable()
        if publication.canonical(publication.read_json(out/'result.json'))!=publication.canonical(record):raise ValueError('final acquisition receipt differs')
        remaining();owned();return record
    except (Exception,KeyboardInterrupt) as exc:
        record.setdefault('first_failure',type(exc).__name__+': '+str(exc));record.update(status='invalidated',accepted=False,source_files_exact=False)
        publication.publish(out,record,stable,account,remaining,owned=owned)
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--project',choices=('led','arcdice','analog-filter','cellscan','uv-dosimeter','navigation-switch','audio-player-my1690x','pico-flipper','sunx-v21','ir-obstacle'),default='led');parser.add_argument('--output');parser.add_argument('--reuse-uv-licenses',action='store_true',help='Explicitly reuse only the three pinned prior UV licence bodies; no fallback');parser.add_argument('--reuse-navigation-notices',action='store_true',help='Explicitly reuse only two pinned prior Navigation notices; old timing unmeasured, no fallback');parser.add_argument('--reuse-audio-notices',action='store_true',help='Explicit fixed Audio root notices and stale Hardware README reuse; no fallback, prior untimed cost retained');parser.add_argument('--reuse-flipper-notices',action='store_true',help='Explicitly reuse two pinned prior Flipper notices; prior metadata cost unmeasured, no fallback');args=parser.parse_args();args.output=args.output or fixed_profile(args.project)['default_output']
    try:
        with shared.cancellation(),shared.alarm(SECONDS):record=fetch_demo(args.output,profile_id=args.project,fetch=args.fetch,started=START,cpu_started=CPU_START,reuse_uv_licenses=args.reuse_uv_licenses,reuse_navigation_notices=args.reuse_navigation_notices,reuse_audio_notices=args.reuse_audio_notices,reuse_flipper_notices=args.reuse_flipper_notices)
    except (Exception,KeyboardInterrupt) as exc:
        print(json.dumps({'status':'failed','reason':type(exc).__name__+': '+str(exc),'accepted':False}));return 2
    print(json.dumps({k:record[k] for k in ('action','status','destination','project','planned_files','planned_bytes','new_network_requests','received_bytes','wall_seconds','total_cpu_seconds','source_files_exact','cache_inputs_current','within_budget') if k in record}));return 0 if record.get('action')=='plan_only' or record.get('status')=='acquired_unqualified' and record.get('within_budget') and record.get('source_files_exact') and record.get('cache_inputs_current') is True else 2
if __name__=='__main__':raise SystemExit(main())
