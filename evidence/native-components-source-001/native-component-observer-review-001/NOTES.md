# Native component observer: bounded static review

The draft's core partition rule matches the retained primary source: PAD-seeded `GetConnectedItems(pad,0)` obtains same-net clusters; only PAD UUID membership enters normalization. Requiring every member's returned set to equal the seed's set rejects asymmetric/nontransitive observations. Repeated ZONE parent UUIDs never become union keys. This is source review, not demonstrated Native capability.

Two pre-integration items:

1. **Pure normalizer contract gap** — `normalize_draft.py:18` derives eligibility from membership in `('pth','smd')`, but never requires the attribute itself to be a known string. An added `attribute='unknown-pad-kind', net='', netcode=0, eligible=False, excluded_reason='excluded'` row passes the remaining checks. A `npth` row with positive GND/code1, eligibleFalse and an explanation also passes. The worker currently rejects these at lines79/82, so this is not an observed Native-worker acceptance bug. Add explicit known-attribute and NPTH/code0 requirements to the pure boundary. The proposed test patch includes both cases and is expected to expose the current gap; it is unexecuted.
2. **Imported wrapper must be bound in the enclosing Native experiment** — worker lines61–70 hash Python and `_pcbnew.so` and check the extension module's loaded path, but do not bind `pcbnew.__file__` or the Python wrapper bytes. Existing `pipeline.tool_manifest()` does not pin `pcbnew.py` either. Merely invoking that existing helper will not close this declared limitation. The retained research manifest already records the installed wrapper path and SHA256 `cd1c06c4709c653256ebd0c98c66d80cd72033767fac27c34ea01b5ec586116a`. Capture/recheck that wrapper in the enclosing experiment, and verify the loaded wrapper path, before presenting exact pinned API evidence. No wrapper mutation or native probe was performed here.

No further concrete defect was found by this bounded reading of identity/census, output separation, failure publication and retained API semantics. The mandatory caller proof of exact saved-refill semantics, enclosing helper/tool stability and outer process limits still needs implementation/verification. The worker expressly reports it did not validate refill semantics; `diagnostic_completed` must remain diagnostic. Strict SWIG return handling and item constants still require real controls. The existing publisher can emit invalidated/failed output without creating accepted routing; load/preflight exceptions before output creation must remain visible through the caller's process record.

`pure-normalization-controls-draft.patch` adds five pure controls to proposed `tests/test_native_component_normalization.py`: valid same-net separate components with duplicate pad numbers retained by UUID; unknown/duplicate/mixed-net and query-census failures; asymmetric/nontransitive sets; shared ZONE-token rejection; and the two excluded-attribute gap cases. It imports only proposed `experiments.native_components_v1.normalize_draft`. If the lead renames that module on integration, adjust the one import. Nothing is applied or run.

After integration and the normalizer fix, proposed command from the project root with the lead's project interpreter:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_native_component_normalization.py -v
```

No tests, Native/JVM/engine, network, Git, backup or delegation actions ran. Only this assigned excluded review directory was written; no tracked/.runs/.data edits. Reviewed draft hashes are in review.json. Measured interval2026-10-15 10:52:26 UTC to10:55:31 UTC is185s; excludes dispatch-to-first-clock and final review-note writing. Full controller/model/subprocess CPU is unavailable. No speed, Native success, support admission, routing or independence claim is made.
