# Installation040 shared bounded-read draft

Prepared only in this ignored directory. Production, installed040, all executed packets, and raw results remain untouched. No project/draft imports, tests, Native, JAR, full reader, network, Git command, or subprocess profile was run by this reviewer. Python standard-library file generation and AST parsing only.

## Exact change

`autorouter/placement_clearance.py:35`: replace `handle.read(limit+1)` with `handle.read(before.st_size+1)`. The existing descriptor size check still refuses a file larger than the caller's ceiling before reading. Descriptor regular-file, no-follow/nonblocking open, symlink ancestry refusal, byte length, device/inode/size/mtime comparisons and all rejection messages remain unchanged. The one additional byte detects growth beyond the observed size; growth within the caller ceiling remains rejected rather than silently accepted.

A 3-byte source file currently receives a 384MiB+1 request when it is the first file in a source inventory. New code requests 4 bytes. The helper still buffers each actual file; this is neither a streaming hash, a new cache, a larger cap, nor a changed evidence acceptance rule. It preserves the existing descriptor-race model; it does not add proof against an adversary restoring file bytes/metadata between observations.

The old real-file growth control in `tests/test_placement_observer.py` checks request 7 for an observed 5-byte file at limit6. Its expectation becomes6. No other body or fixture is changed.

## Prospective controls (unexecuted)

`tests/test_bounded_file_read.py` contains six real-file methods using the existing fdopen-wrapper style:

- Request exactly observed size+1 for empty/tiny files under384MiB and for exact/zero caller boundaries. The assertion executes before delegating to the real buffered read, so before-fix failure cannot itself request384MiB.
- Shared inventory requests4/6 for 3/5-byte files even with384MiB remaining allowance; checks exact SHA map.
- Actual append during read, still below the caller ceiling, rejects.
- Actual truncation during read rejects.
- Same-size write after read with explicitly changed mtime rejects.
- A descriptor already over the caller bound rejects before any read request.

Expected before/after behavior is a prediction, not a result: first two new methods should fail on the frozen old helper; all six should pass after integration. Growth/truncation/metadata/oversize negatives should continue rejecting under both versions. Lead can run new controls alone against the old helper first, then apply the shared helper and existing expected-size update. Do not load a hidden patched helper into the installation040 qualifier.

Prospective focused integration command, not executed:

```sh
.venv/bin/python -B -m unittest tests.test_bounded_file_read tests.test_placement_observer tests.test_placement_policy tests.test_placement_clearance tests.test_install_smoke -v
```

`changes.patch` is a standard unified patch for one production line, one existing test expectation, and the new test file. Exact current base file hashes and diagnostic receipt hashes are in `base-pins.json`; full proposed files are alongside it.

## What the retained measurements establish

The004 statement trace reaches `companion.read_transport(ntplan)` at ~255.9MB prior peak; it is not killed during the initial full source inventory. The005 finer trace completes installed companion context, its698-file inventory, and toolchain constructor at295,731,200B prior peak, then enters `p.check_result` at companion line75. It is killed before returning. No statement inside that shared checker was isolated; the oversized request is a source-level resource defect, and its contribution to this actual peak is still uncertain.

Retained process receipts (kernel direct-child peak RSS, sampled group RSS is a separate estimate):

| retained run | process status | child wall s | child CPU s | direct-child peak RSS B |
| --- | --- | ---: | ---: | ---: |
| native-schematic-transport-readback-execution-001 | success | 7.319065999996383 | 6.872207 | 2204581888 |
| installation040-native-001 | success | 31.93542554200394 | 22.756306000000002 | 2209333248 |
| current-installation040-review-002 | memory_limit | 6.536101167002926 | 4.4494430000000005 | 1330266112 |
| current-installation040-review-003 | memory_limit | 6.479388042003848 | 4.51316 | 1335820288 |
| current-installation040-review-004 | memory_limit | 6.76539891702123 | 4.435886 | 1321058304 |
| current-installation040-review-005 | memory_limit | 8.370136375015136 | 6.105713 | 1105772544 |

The earlier successful pure transport readback already used~2.2GB without any Native/JVM replay. This predates the seven-group040 audit. The040 Native process success above is a child process fact: its original outer remains invalidated for the root-vs-installed command-prefix guard. None of002–005 is a passed reader or a free retry. Keep all failed receipts and costs. No RSS cap change is proposed.

The actual supplied source+installed040 identity remains frozen6bd0d57b. A real shared-helper change needs fresh integration/installed context/protocol (future041), with the old040 artifact honestly partial. It cannot qualify current040 by monkeypatching or relabeling its source. Later bounded measurement is needed before claiming lower memory use, a usable1GiB reader, or causal attribution to this correction.

## Review cost

Elapsed wall through note preparation: 534.843 seconds for this memory-review task, including source inspection and waiting for lead-owned002–005 profiles; 148.668 seconds since the explicit patch request. Full reviewer CPU and model/server work are unmeasured. The measured child costs in the table belong to lead-owned retained executions and are not reviewer costs. External spend by this reviewer: $0.
