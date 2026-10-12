# Mixed PIC worker getter correction

Clear for the next bounded ROOT-only native attempt. The only runtime edit replaces `pad.GetNetClassSlow()` with `pad.GetEffectiveNetClass()`; the exact old worker with that textual substitution equals the corrected worker.

Pinned pcbnew.py declares PAD(BOARD_CONNECTED_ITEM). The inherited `GetEffectiveNetClass(self) -> NETCLASS` is at lines11283–11285. `GetNetClassSlow` at20041–20043 belongs to NETINFO_ITEM, which PAD does not inherit. Pinned board_connected_item.cpp141–155 returns the item's net class when available, then the board Default/fallback class; this is an effective-class observation, not pairwise rule evaluation.

The same 247-fake-PAD regression passes with the new worker and raises AttributeError on the exact failed001 worker. Fake PADs intentionally provide no Slow method. This is a pure API-use regression, not proof of native return behavior.

Actual001 at2ad7831b1c84455930477578f39733e45b820b5f remains failed: one executed native process, exit1, cleanup complete; initialization sidecar records AttributeError. Initialization text DRC, context/DSN export, compilation and Java import were not reached. The log also contains a preceding wxApp assertion; it is retained and not attributed as the terminating cause. Inner cost1.622148291s wall/.990432s CPU; complete outer invocation is bound in audit.json. Every frozen artifact, all15 original files and the copied complete input remain byte-exact; no evidence was overwritten or reclassified.

No driver, budget, scope, rule, geometry, support gate or acceptance predicate is changed. Native/JVM reruns and full suites were not performed by this review. New actual API behavior remains the lead's next qualification.
