# Independent rejected multichannel audit

The audit passed; routing remains rejected. The final native report contains **160 opens, one starved thermal, 94 warnings and zero exclusions**. The thermal is C2 pad1 (UUID6676eb38-09f3-4b48-8024-482389e3ee8d) connected to an isolated island of the F.Cu vbias zone (UUID2ac68700-4aa9-4420-a0e1-76004e618e09). All 17 original project files, original rules and six zone definitions are unchanged; actual saved refill and final DRC were retained and checked.

The raw native DSN→derived guidance→combined geometry adapter chain, SES routes, imported copper and final saved candidate matched. Every generated segment is 0.3 mm; there are zero vias. Earlier track-width(75), clearance(13), annulus(3), and via-diameter(3) errors are absent in this run. This is a diagnostic observation across different exposed runs, not a fresh matched causal comparison or a completed board. Zero-via output does not newly qualify via transport; the separate owned fixture does.

Final candidate SHA256: b5da43c9fc38cc1d5e006f144cc8747528313137cb114e37c27d86a5bf3938a3. Invalid-candidate length is 186.998179 mm. Stored prepublication totals are 57.378238 s wall and 64.509057 s total CPU within 120-second caps. No separate full invocation timer was retained for this CLI run. Engine completion state means the engine stopped, not that native connectivity passed.

The normal `check_result` correctly rejects this receipt. Calling `check_floor_result` directly verifies its retained input/transformation/transport/final-context contract even though the candidate is rejected; that helper does not substitute for native acceptance. The audit separately bound the final native process, input tree and raw rejected report.

`audit.py` is reproducible read-only inspection, reusing the independently reviewed SES parser from the fixture audit by recorded SHA. It writes only its own audit receipt and refuses collisions. The full original run and source hashes were checked unchanged before and after inspection. This is AI consistency review, not fresh native execution, authentication, human PCB review or electrical/physical validation.
