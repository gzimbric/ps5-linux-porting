# PS5 Pro 11.60 Linux Test 3

Linux Test 3 is the current PS5 Pro test for retail firmware 11.60. Use this
pair together:

- [Pro Linux Test 3 loader release](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-pro-linux-test-3)
- [Ubuntu 24.04/Linux 7.3 Image 3](https://github.com/gzimbric/ps5-linux-image/releases/tag/ubuntu2404-k73-image-3)

The complete preparation and boot steps live in the loader repository's
[PS5 Pro 11.60 tester guide](https://github.com/gzimbric/ps5-linux-loader/blob/main/PS5_PRO_1160_TESTING.md).
Follow that guide exactly. In particular, Image 3 needs this text added to the
single line in `cmdline.txt` before it is used on a Pro:

```text
modprobe.blacklist=ps5_gpufreq,ps5_cpufreq module_blacklist=ps5_gpufreq,ps5_cpufreq usbcore.autosuspend=-1
```

The released Image 3 file has not been rebuilt with that line. The edit is a
required preparation step, not a property of the downloadable image.

## What passed

On one PS5 Pro, the exact Test 3 loader and Ubuntu Image 3 reached the Ubuntu
desktop at 1920x1080 over HDMI from two cold boots. Wired SSH and onboard
Wi-Fi worked. USB input remained available with `usbcore.autosuspend=-1`.

That is the full hardware scope. It is one console and one display, not broad
model or display coverage.

## What is still open

- Bluetooth did not produce a usable controller on the tested Pro.
- Pro CPU/GPU frequency control has not been validated and the regular-console
  frequency modules must remain blacklisted.
- Linux does not expose a GPU temperature reading on the Pro.
- Games and sustained GPU load have not been tested.
- The Linux drive negotiated USB 2 speed in the tested port.
- `ps5-boot-report.service` fails on the released Image 3. The timeout fix and
  a default USB autosuspend workaround are in newer image source, not in this
  release.
- Other displays, longer idle periods, text-console switching and display
  power/input cycling still need coverage.

Use wired input and keep the first tests light. Fully power off between
attempts; do not use Linux sleep or hibernation.

## Do not mix the test paths

Tests 1 and 2 are superseded. The Run 18 and Run 21 loaders and the older
Ubuntu 24.04/Linux 7.1.7 pair are regular-console builds and are not Pro
substitutes.

The older [Ubuntu 24.04 build 3 guide](ubuntu2404-tester-guide.md) remains in
this repository as the hardware-tested regular-console 7.1.7 record. Its
loader, hashes and boot instructions apply only to that legacy pair.
