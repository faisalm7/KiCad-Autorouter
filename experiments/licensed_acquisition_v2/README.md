# PAW3395 acquisition profile — prospective, not fetched

This directory contains a thin wrapper and fixed data for the existing bounded controller in `experiments/licensed_acquisition_v1/fetch.py`. It introduces no second controller. Its built-in `v2` profile admits only `badjeff/paw3395-pcb` at `b71e346fc04ef18c26e0e8638ce0333395d41a14`: the entire pinned tree's **14 nonexecutable blobs / 2,163,350 bytes**. The six local files and shared v1 controller/test bytes must all match committed HEAD before any request and remain exact through publication. Shared-source checks follow Git subprocesses and final evidence scans. Direct HEAD sampling precedes final material hashing; these are bounded finite samples, not atomic protection against arbitrary concurrent writers.

The original v1 default, protocol and historical acquisition remain unchanged. No arbitrary manifest/profile CLI is added. The source includes native PCB/project/schematic, original PRL, local footprint/table, README/LICENSE, media and fabrication options. Every path, Git blob SHA1, byte size and mode is fixed. Three already read metadata files also have SHA256; the other eleven hashes remain unknown until exact blob-verified acquisition. No downloaded file executes.

The README applies CERN-OHL-P-2.0 and declares two layers / 3.3V. This is sufficient to propose development inspection, not proof of actual source format, authentic external dependency closure, per-asset redistribution rights or circuit independence. The original table points to the included custom footprint; its model and stock-library references remain unseen. Keep the complete tree and all notices. Follow `STATIC_AUDIT.md` after acquisition; never substitute current libraries or infer missing asset rights.

The unchanged capacity limits are 10MiB per project and invocation body, 64MiB all `.data`, 24MiB output, 2,048 data files / 4,096 entries, 300 seconds total /30 seconds per request. Fourteen fixed requests have no retries. The frozen **345 files /37,408,570 bytes** baseline would become **359 /39,571,920 bytes**. The fetcher never deletes or overwrites old inputs. A fresh destination/output is mandatory; failed partials require a separate reviewed continuation rather than automatic resume.

The acquired denominator stays **19** now. A successful full fetch makes20 acquired boards, retaining all19 old boards and failures; it does not add an eligible/complete/independent family or native acceptance. PAW3395/PAW3950 options remain one development lineage until source-history and structural comparison. No reserved holdout is inspected.

Offline preparation:

```sh
python3 -B experiments/licensed_acquisition_v2/fetch.py
python3 -B experiments/licensed_acquisition_v2/test_fetch.py
```

The tests reuse all legacy adversarial controls and add fixed-profile, shared-source, cross-profile and final-publication mutation checks. They use tiny temporary sources and mocked transports, with no network.

Only after ROOT reviews/checkpoints the exact shared and profile files, and the sequential native lane is idle:

```sh
python3 -B experiments/licensed_acquisition_v2/fetch.py --fetch --output .runs/licensed-acquisition-005-run-001
```

This command is not run by source preparation. It requires both `.data/expansion005` and the output to be absent, takes the existing foreground acquisition lock and verifies all source/response/material bytes through the final receipt. SIGINT/SIGTERM, stale input, bad response, altered shared code or publication errors invalidate success. Timer/output limits include final checks; stored timing precedes final publication. No change to `data/sources.json` or the original `data/fetch.py` is necessary for this bounded acquisition.
