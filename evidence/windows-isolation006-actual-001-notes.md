# Windows006 isolation-only observation

[Actual record](windows-isolation006-actual-001.json), [public run](https://github.com/faisalm7/KiCad-Autorouter/actions/runs/39090040127). Source: `946d53d3c9f567b69a1a7b938c45aaf88b395038`.

The `windows-isolation` job completed its finite diagnostic on the standard `windows-2022` runner. The existing mocked PowerShell structure/refusal harness actually ran and exited zero. The unchanged live firewall gate exited **1** at its first inbound rule; the overall diagnostic job succeeded because it retained that refusal and the requested snapshot, then completed cleanup. Admission and Windows product support remained false. No KiCad/JRE/JAR acquisition, Native/JVM work or execution of the selected `cmd.exe` occurred in this mode.

The snapshot contains both exact owned inbound/outbound rules, all six filter groups, enabled Domain/Private/Public profiles and one Public interface. `EnforcementStatus` has outer type `System.Object[]`; both items have type `System.String` and text `ProfileInactive`, `Enforced`. No numeric enforcement enum value was observed. Both application filters expose `Package=null` with empty items; this is not recorded as `Any`. Other address/port/service/interface applicability values are retained exactly in the JSON. This fills the earlier evidence gap without proving transport denial or active/future-profile equivalence.

| Measured scope | Actual observation |
| --- | --- |
| Workflow | 33 seconds; provider `run_duration_ms=33000` |
| `windows-isolation` job | 29 seconds |
| Script | 6.8063175 seconds |
| Gate child | 3.6916075 seconds; exit 1 |
| Mocked harness child | 0.8701791 seconds; exit 0 |
| Provider timing | All reported billable buckets are zero milliseconds |
| Whole CPU | Unknown; billable milliseconds are not CPU time |
| Artifacts | API `total_count=0`; mode requested no artifact/cache upload |

Exactly two newly owned restrictive rules were removed. The record reports each exact name absent from both ActiveStore and PersistentStore, no cleanup query errors, and scratch removal. It hashes an existing valid Microsoft-signed `C:\Windows\System32\cmd.exe` and never executes that file.

Curation checked the single packet at raw `job.log` line 243 against `record.json`, strict base64 decoding plus length/SHA256 for all four embedded streams, the diagnostic packet against `firewall-diagnostic.json`, and source pins against local bytes with the recorded Windows CRLF conversion. All matched. Raw inputs under `.runs/windows-isolation006-actual-001/` were preserved unmodified. The public JSON excludes full API actor/committer/contact objects and the checkout transcript. Reviewed checkout credential values were masked; no unmasked credential pattern was found. Raw files remain on this Mac and in the provider log subject to its retention; this is not an independent raw-evidence backup claim.

No new runtime, CI, test, installer, download or network work was performed for this curation. Keep Native/JVM admission deferred. Windows routing, cancellation, original-rule validation, review/export and product integration remain unqualified; the original scalar guard and all failures remain retained.
