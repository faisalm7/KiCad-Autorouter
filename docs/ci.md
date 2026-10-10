# CI preparation

`.github/workflows/manual-python-controls.yml` is manual-dispatch only, with read-only repository permission, a five-minute limit, no secrets, no dependency installation and no dataset/engine downloads. Official `actions/checkout` v7.0.1 was resolved through GitHub's release/ref APIs to commit `3d3c42e5aac5ba805825da76410c181273ba90b1` on2026-10-10; credentials are not persisted. The selected pure Python controls ran locally as part of the full suite. Remote Linux execution remains untested.

No remote workflow was dispatched or billed. This file does not qualify KiCad, routing, macOS, native DRC, GUI integration or a clean installation. Those require the pinned local Mac evidence. Running CI is a separate owner-approved action under the zero-new-spending rule; do not add push/pull-request triggers or paid runners silently.
