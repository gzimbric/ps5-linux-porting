# Evidence

This directory contains compact, sanitized summaries. Raw console captures
remain private because they can contain network addresses, local filesystem
paths, and unrelated system output.

Each summary distinguishes direct observations from conclusions. A missing
post-crash marker is reported as an unknown boundary, not proof that the next
instruction executed.

- `11.60-summary.txt` is the compact machine-readable snapshot.
- `11.60-sonic-display-runs.md` records the Run 10 through Run 15
  display bring-up matrix, source and artifact identities, physical USB
  verification scope, and observation limits.
- `11.60-ubuntu-run-16.md` records the same-loader Ubuntu 24.04 control boot,
  visible display and authenticated userspace result, input identities, and
  the console's non-MT7921 wireless hardware.
