# Protected import v2 independent review

No remaining scoped blocker found at pipeline `779705e14db01f4dcd32f09d9b966dbdf203f72b278b49f0a6c395be31a56dbc`, tests `eb9bffa909035ad3daf60cb442f621baf04521f105fb3e8491ae65ffdcc615ed`. Native qualification of the corrected locked case remains pending.

The actual rejected locked run has two exact `(locked yes)` children moved by native serialization, with original UUIDs retained. V2 extracts only a single explicit `(locked yes)` child for signature positioning. It does not normalize its value/form, other field order, coordinates, width, net, layers, unknown fields or route kind. The output replaces a unique matched route with the exact original node, preserving the original lock field placement too. Duplicate normalized matches and UUID collisions still reject.

Twelve small independent saved-file controls pass: the actual locked import remains rejected by default/v1; v2 reconstructs its exact original nodes and binds copied imported/candidate bytes; v1 downgrade, unknown/missing policies, removed/false/duplicate locks, unrelated field reorder and normalized duplicate matches reject; the actual accepted partial002 v1 receipt still passes the full central checker. All source and both original run inventories are unchanged before/after.

The final explicit policy dispatch preserves old v1 signature semantics. Default transplant calls stay v1 and historical receipts without reconciliation keep their original acceptance guard. Only the native production route opts into v2. The source diff is limited to this policy/signature/readback dispatch; final native and exact protected-node guards are unchanged.

This review ran no KiCad, Java, compiler, routing, GUI or network. ROOT owns the fresh locked native run. The prior failed locked run remains rejected and intact.

Reproduce once with fresh review scratch: `python3 -B .runs/review-protected-import-v2-001/audit.py` (the script deliberately refuses an existing copied-files directory).
