# Actual installed CLI help

The pinned KiCad10.0.0 CLI returned exit0 for `pcb drc --help` inside the existing network-denial sandbox and isolated run configuration. The output confirms the exact parity, refill, severity, track-error, violation-exit and save flags. No board or schematic was supplied; no DRC, netlist, native parity or routing correctness was exercised. Save remains excluded from the prospective parity invocation.
