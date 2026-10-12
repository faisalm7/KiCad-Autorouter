# Installer source-capacity diff review

No scoped blocker found. The proposal raises only the bounded tracked-source inventory from 128 MiB/10,000 files to 192 MiB/12,000 files and records both limits in the receipt. The current stat inventory is 8985 files / 143039891 bytes, so the older128MiB aggregate bound is insufficient. Cumulative streaming read caps, path/symlink checks, the512MiB scratch ceiling,600s whole-job wall cap, network denial and final freshness/publication guards remain unchanged.

The new regression uses six real bytes under a five-byte cap and two files under a one-file cap; it also retains the existing pre-hash bounded-reader sentinel. I reviewed those assertions and the exact AST/function diff; I did not run tests or install anything. ROOT owns focused tests and the later fresh installation. The larger source bound does not promise the independent scratch ceiling will always fit; that remains fail-closed.

Exact source/test hashes, current stat counts and the reviewed patch are retained here. This review changed no tracked or external files.
