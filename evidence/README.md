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
  the console's non-MT7921 wireless hardware. Reproduction and comparison
  instructions are kept separately in the
  [Run 16 Ubuntu USB guide](../docs/ubuntu2404-run16-usb.md).
- `11.60-ubuntu-run-17-wifi.md` records the onboard IW620 Wi-Fi bring-up on
  the same loader and USB: driver and firmware identities, the load and
  association result, the stalled first wake attempt, and evidence limits.
  Build and setup steps are in the [Wi-Fi guide](../docs/ubuntu2404-wifi.md).
- `11.60-cachyos-run-18-dma-e820.md` records the CachyOS boot with the opt-in
  DMA E820 loader build: the build's map change, input identities, the e820
  lines Linux received, the USB write and read-back check, and evidence
  limits. Steps for testing that build with the CI-built Ubuntu image are in
  the [tester guide](../docs/ubuntu2404-tester-guide.md).
- `11.60-ubuntu-ci-run-19.md` records Run 19, which booted the image and ELF
  from the tester guide (CI Ubuntu build 3 and the DMA E820 ELF): input
  identities, the directly observed picture, the e820 lines, the guide's checks
  including the I/O check, warnings, two image defects, and evidence limits.
- `11.60-cachyos-k73-run-21.md` records Run 21, the first boot of CachyOS on
  Linux 7.3.0 (rmux's 7.3 port of the PS5 patches) with the bounded Wi-Fi
  loader build: input identities for the loader and the image, the loader
  lines, the e820 lines and KASLR placement, onboard Wi-Fi with the firmware
  the loader copied, VCN, the Bluetooth failure, the DualSense over USB, the
  desktop switch issue, idle temperatures with rmux's frequency drivers, the
  later install watcher and game-load telemetry, the image 2 source follow-up
  and evidence limits. The image 2 notes do not turn its later, verified CI
  artifacts or still-unbooted hardware state into Run 21 results.
