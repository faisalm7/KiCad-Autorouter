Local KiCad Autorouter launcher

Double-click Launch Autorouter.command. This starts the existing KiCad manager
with configuration, documents/plugins and cache in this folder, not globally.
Open a saved project, open PCB Editor and click the green Autorouter toolbar
icon. In the separate router window choose the exact saved PCB/output paths.
Save and CLOSE source PCB/schematic editors and acknowledge before routing.
Candidates/review/export stay separate; no automatic live-board edits.

This is a bootstrap for this exact existing checkout, virtual environment and
pinned tools, not a standalone application, package or dependency installer.
Keep this checkout and tools in place. A changed checkout/tool refuses launch;
prepare a NEW launcher folder after an intentional update. Nothing downloads.

Only this isolated config enables KiCad's local IPC API. Telemetry, KiCad and
package update checks are disabled in the new config. This is not an OS network
sandbox or protection against hostile same-user writers. Standard symbol,
footprint or 3D library warnings may appear if libraries are not installed;
no libraries are fetched and no source project is repaired automatically.
Live config/documents/cache remain mutable, but linked/special files or folders
refuse launch. Each home is bounded to 512 MiB, 10,000 files/20,000 entries.
Keep old launcher folders; prepare a fresh one if these limits are exceeded.

The launcher refuses when it observes another KiCad manager/editor for this
user. Close those applications first; it never kills them. This sampled check
cannot prevent simultaneous startup or detect deliberately renamed processes.
Closing Terminal can terminate the manager; cancel active routing in the router
window and wait for its existing cleanup before closing applications.
