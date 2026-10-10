# Failed fresh-checkout test retained

At frozen e1e585f, a clean independent local clone and Python venv were created. Cached official engine setup and pinned-tool doctor passed under per-process network denial. The suite ran 105 tests and failed 19 process-runner controls. The exact logs and failure receipt are retained here; installation did not pass and the native smoke route was not reached.

The follow-up diagnosis found that the old monitor launched the setuid `/bin/ps`, which the sandbox refused with EPERM. The existing Python environment itself was functional. A scoped fix is under development; network denial remains required. A new run identifier must record any retest. This subset omits the disposable clone and copied binary dependencies, whose tracked contents are recoverable from the frozen Git commit.
