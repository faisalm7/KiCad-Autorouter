# Mixed PIC worker NetInfo correction

Cleared for the next bounded original-source observation. Actual002 remains failed and does not qualify PAD.GetEffectiveNetClass return conversion: the declared wrapper returned SwigPyObject without GetName. No cast, repr, integer coercion or guessed default is introduced.

The corrected worker uses BOARD.GetNetsByName → NETINFO_ITEM.GetNetClassSlow → GetName/GetClearance, the same unchanged floor_context path that actually returned111 Default/POWER net rows in PIC custom observation002 at129dde0. Its context/hash/process/code bindings are verified in input-audit.json. This establishes the existing net-info lookup path, not pad-local or pairwise clearance behavior.

Net class and class clearance fields are explicitly tagged as net metadata. Assigned pad name/code must match the bounded unique map. Netless rows retain None/None and unavailable_netless; all247 rows still query own/local values. The driver cross-checks both pre- and post-initialization metadata against the same-loaded-board context, including exact assigned types/classes/clearances, netless absence and UUID population. Original rules, geometry, initialization and export sequence, budgets, publication lifecycle and routing-support flags are unchanged.

Three existing focused pure methods pass, covering opaque PAD avoidance, six invalid assigned-metadata cases and seven same-context row mutations. The same fake PADs reproduce the original SwigPyObject.GetName error with exact failed002 code and succeed with the correction:247 own-clearance queries,236 assigned rows and11 explicit netless rows; PAD.GetEffectiveNetClass is never invoked. These controls establish Python logic only. No native/JVM work or full suite was run here.

All frozen failed002 artifacts and all15 original/copied source files remain byte-exact. Its single native process exited1 with cleanup complete, before initialization text report, context/DSN export, compilation or Java import. Inner cost1.261237625s wall/.971917s CPU; complete outer costs are retained in input-audit.json. The preceding wxApp assertion is preserved separately from the terminating AttributeError. Prior001,002 failures and previous source-only review stay unchanged.

No remaining source blocker was found within this narrow correction. Fresh native execution remains required before calling the new observation successful; mixed-clearance equivalence, routing and production custom-pad support remain unqualified.
