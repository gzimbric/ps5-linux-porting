# PS5 Linux Porting

This repository records the work needed to boot Linux on newer retail PS5
firmware, with firmware 11.60 as the active case study. It contains research
notes, hardware evidence, tester guides, and validation tools. Linux images,
loader binaries, and release downloads live in the linked source repositories.

This is not a Linux distribution, jailbreak bundle, or ready-to-run payload
release. Everything here is experimental and can crash the console or damage
data on the Linux USB drive.

## Start here

| Goal | Link |
|---|---|
| Test the current CachyOS Image 3 prerelease | [Download Image 3](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-3) and follow the [Image 3 tester guide](docs/cachyos1160-k73-image-3-tester-guide.md) |
| Boot the hardware-tested Ubuntu pair | [Ubuntu 24.04 tester guide](docs/ubuntu2404-tester-guide.md) |
| Test the older public CachyOS prerelease | [Image 2 tester guide](docs/cachyos1160-k73-image-2-tester-guide.md) |
| Read the complete 11.60 result | [Firmware 11.60 status](docs/11.60-status.md) |
| Review the sanitized hardware records | [Evidence index](evidence/README.md) |

## Current 11.60 status

Linux, wired SSH, and physical HDMI output have been observed on one regular
CFI-1115B running firmware 11.60. Run 15 remains the loader and display
baseline. Ubuntu and CachyOS have both booted through the upstream
`ps5-linux-loader` architecture with the Sonic-derived 11.60 display path.

Current gaming work is based on CachyOS and Linux 7.3 with rmux's PS5 patch
set. Keep these artifact boundaries separate:

| Area | Current evidence |
|---|---|
| Loader, HDMI, and SSH | Passed on the tested CFI-1115B. Other models and repeated cold-boot coverage remain open. |
| Ubuntu 24.04 build 3 | The exact CI image and DMA E820 loader pair booted once with visible HDMI, SSH, and the guide's 12 GiB USB check. |
| Local CachyOS Image 3 base | One exact unpublished raw image booted with HDMI and SSH. Its in-image Bluetooth path paired a wireless DualSense and exposed buttons, motion, and touchpad input. |
| Image 3 Wi-Fi follow-up | A stable-MAC NetworkManager configuration resolved the Plasma menu failure on the running system; WPA3, DHCP, and HTTPS passed. This live change was not in the original raw image. |
| Image 3 desktop round trip | Live source changes made Steam's **Switch to Desktop** action and the desktop shortcut back to Gaming Mode pass without compositor overlap. These changes were not in the original raw image. |
| Fan and clock policy | The published Image 3 service sends legacy servo pattern `3` before guarded GPU and CPU scaling. It does not force or measure maximum RPM; on the tested CFI-1115B the exposed target remained 86 °C. The tester guide applies and verifies a 65 °C target after every boot. With that hotfix active, a short bounded CPU load passed. |
| Public Image 3 prerelease | [Published for testing](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-3) from source `16795eb` by successful workflow `39521098451`. Its exact downloadable artifact has now completed one identity-verified cold boot with HDMI, wired SSH, Plasma Wi-Fi, internal-Bluetooth DualSense input, both session directions and a 20-second bounded CPU load. |

The local hardware image and the public CI image have different raw-image
hashes. Their results remain separate. The downloadable prerelease now has its
own exact-image hardware result; the earlier local boot and live follow-ups are
still supporting evidence rather than substitutes for it.

Still pending for Image 3:

- two to four more cold boots and broader console coverage;
- Wi-Fi and DualSense reconnect after a cold boot;
- at least 60 minutes of concurrent Wi-Fi traffic and Bluetooth input;
- a later Steam Offline Mode test after the successful online bootstrap;
- a longer controlled load to assess thermal equilibrium and stability; and
- the performance opt-out, storage integrity, video decode, and longer
  stability checks in the tester guide.

## Downloads and tester guides

### Hardware-tested Ubuntu pair

Run 19 booted this exact pair once on the CFI-1115B:

- [Ubuntu 24.04 build 3 image](https://github.com/gzimbric/ps5-linux-image/releases/tag/ubuntu2404-1160-build-3)
- [Firmware 11.60 DMA E820 loader](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-run18)
- [Ubuntu 24.04 tester guide](docs/ubuntu2404-tester-guide.md)

### Public CachyOS Image 2 prerelease

Image 2 is public for testing, but no identity-verified boot of that exact
image is recorded. Its KDE Wi-Fi join and Steam desktop switch are known open
issues; the guide includes recovery steps.

- [CachyOS Image 2](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-2)
- [Bounded 11.60 loader](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21)
- [Image 2 tester guide](docs/cachyos1160-k73-image-2-tester-guide.md)

### CachyOS Image 3

Image 3 is public as a tester prerelease. CI built and verified the one-file
archive, and that exact artifact has now completed one identity-verified cold
boot on the CFI-1115B. It remains a prerelease while repeated boots, cold
reconnect, coexistence soak, longer thermal/stability testing and the other
acceptance gates remain open. Keep its result separate from the earlier local
boot and live follow-ups.

- [CachyOS Image 3 public prerelease](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-3)
- [Bounded 11.60 loader](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21)
- [Image 3 tester guide and acceptance gates](docs/cachyos1160-k73-image-3-tester-guide.md)
- [Image 3 CI, release and exact-image hardware evidence](evidence/11.60-cachyos-image3-ci.md)
- [Local Image 3 hardware evidence](evidence/11.60-cachyos-image3-local.md)

Image releases are published as one `.img.xz`. The build fails instead of
publishing numbered parts when the compressed image reaches the release size
limit.

## Before testing

- Use only a regular retail PS5 on firmware 11.60. Do not use a PS5 Pro or a
  different firmware.
- Flashing erases the selected USB drive. Confirm the whole device before
  writing an image.
- Use the exact image and loader pair named by its tester guide. Do not mix
  releases, older ELFs, boot files, or third-party root filesystems.
- Start from a full PS5 power-off. After Linux starts, do not use Linux suspend,
  hibernate, or GameOS Rest Mode; shut Linux down fully before another attempt.
- Keep wired Ethernet available as the diagnostic and SSH fallback.
- Gaming Mode to Plasma is not instant. After choosing **Switch to Desktop**,
  wait while Steam and Gamescope exit and Plasma starts. A clean measured pass
  took about 2.4 seconds, while an earlier transition that needed additional
  cleanup took about 27 seconds. Do not click repeatedly or power-cycle just
  because the transition takes several seconds.
- Published Image 3 can show **System policy prevents control of network
  connections** after returning to Plasma. The tester guide includes the
  targeted `steam`/NetworkManager Polkit hotfix; it is not part of the published
  image hash.
- Published Image 3 also leaves `systemd-networkd-wait-online` enabled even
  though NetworkManager owns the network. Its two-minute timeout does not mean
  Wi-Fi or Ethernet failed. The tester guide disables the unused waiter and
  clears its failed state; that cleanup is not part of the published hash.
- A fresh Image 3 build starts in Plasma so networking can be configured. Its
  first Gaming Mode setup needs internet; Offline Mode is a later-use test
  after Steam has saved the required account and game state.
- Published Image 3 needs the tester guide's 65 °C fan-target correction after
  every boot. The documented public range is 40-80 °C, lower values cool more
  aggressively, and Linux exposes no fan RPM or tachometer reading.
- Never copy another image's prebuilt `btusb.ko`. Bluetooth modules must be
  rebuilt for the exact kernel.
- The bounded Wi-Fi loader copies the console's own IW620 firmware to its USB.
  Never redistribute that firmware file.
- Ubuntu starts with `ps5` / `ubuntu`; CachyOS uses `steam` / `steam`. Change
  the password immediately and keep the console on a trusted local network.

## Technical evidence

| Topic | Document |
|---|---|
| Full current result and evidence limits | [Firmware 11.60 status](docs/11.60-status.md) |
| Image 3 public CI artifact | [Image 3 CI, release and exact-image hardware evidence](evidence/11.60-cachyos-image3-ci.md) |
| Image 3 local boot and live follow-ups | [Image 3 local evidence](evidence/11.60-cachyos-image3-local.md) |
| Historical CachyOS Linux 7.3 run | [Run 21 evidence](evidence/11.60-cachyos-k73-run-21.md) |
| Ubuntu CI image hardware boot | [Run 19 evidence](evidence/11.60-ubuntu-ci-run-19.md) |
| Display-port reconstruction history | [Sanitized run matrix](evidence/11.60-sonic-display-runs.md) |
| Remaining work | [Maintenance backlog](docs/maintenance-backlog.md) |
| Source and upstream revision pins | [Upstream references](docs/upstream-references.md) |
| Sonic's 13.60 artifact as a reference | [Sonic 13.60 binary reference](docs/sonic-13.60-reference.md) |

## Why this repository exists

A working hypervisor bypass is only one part of booting Linux. The loader also
has to preserve the bypass across rest and wake, stage the kernel and initrd,
move every CPU out of the hypervisor safely, install the memory map, and bring
up firmware-specific display and devices. Treating the port as a list of
offset substitutions caused many of the earlier failures; this repository
keeps the working path and the evidence for each boundary together.

## Repository map

| Path | Purpose |
|---|---|
| `docs/` | Architecture, workflows, tester guides, current status, and upstream pins |
| `evidence/` | Sanitized hardware evidence without raw console data |
| `firmwares/` | Machine-readable firmware status manifests |
| `templates/` | Consistent hardware-run reports |
| `tools/` | Manifest, privacy, link, log, and media-validation helpers |

The canonical 11.60 loader source is on
[`gzimbric/ps5-linux-loader` `main`](https://github.com/gzimbric/ps5-linux-loader).
The image build source is on
[`gzimbric/ps5-linux-image` `main`](https://github.com/gzimbric/ps5-linux-image).

## Repository checks

Run the manifest, privacy, link, and unit checks with:

```sh
make check
```

To classify a locally captured 11.60 log without modifying it:

```sh
python3 tools/classify_1160_log.py /path/to/capture.log
```

## What is intentionally excluded

This repository does not contain:

- kernel or hypervisor images;
- decrypted firmware, console keys, or the IW620 Wi-Fi firmware;
- Linux disk images or release payloads;
- raw console logs, private network addresses, or local paths;
- built ELF, shellcode, or driver-module binaries; or
- loader and image source already maintained in the linked source repositories.

Hashes and small factual offsets are included only as provenance or validation
metadata. See the [publication policy](docs/publication-policy.md).

## Related work

- [pLinux5-NG](https://github.com/pLabs5/pLinux5-NG)
- [ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader)
- [ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image)
- [ps5-linux-mwifiex](https://github.com/ps5-linux/ps5-linux-mwifiex)
- [rmuxnet/ps5-linux-patches-1](https://github.com/rmuxnet/ps5-linux-patches-1),
  Linux 7.3 PS5 patches and CPU/GPU frequency drivers
- [VivaLaVent/ps5-bazzite-deck v1.0.3](https://github.com/VivaLaVent/ps5-bazzite-deck/releases/tag/v1.0.3),
  the source of the Bluetooth correction rebuilt for Image 3
- [Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn)
- [PS5 Hypervisor Bypass Porting](https://github.com/gzimbric/ps5-hv-bypass-porting)

## License

Original documentation and tools in this repository are available under the
MIT License. Upstream projects and derived patches retain their own licenses.
See [LICENSES/README.md](LICENSES/README.md).
