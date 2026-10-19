# PS5 Linux Porting

Source-first notes, evidence, and small tools for porting the PS5 Linux loader
to additional firmware.

This is a research companion to
[pLinux5-NG](https://github.com/pLabs5/pLinux5-NG),
[ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader), and
[Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn). It is not a
Linux distribution, jailbreak bundle, or ready-to-run payload release.

## Current result

The active case study is a regular PS5 on firmware 11.60.

Linux and physical HDMI output now work through the official-loader/Sonic
architecture on firmware 11.60. Run 15 executed the complete Sonic-equivalent
display path and produced visible output while the same boot reached
authenticated Linux userspace over wired SSH.

Run 16 reused the exact Run 15 loader with an Ubuntu 24.04 image and again
reached authenticated wired userspace with visible physical output. This is a
cross-distribution control on the same console; Run 15 remains the loader
baseline and the Ubuntu initrd is not the exact CachyOS initrd from Run 15.
The Ubuntu USB was a custom build based on `ps5-linux-image` commit `52db0a4`,
not the stock image produced by that upstream revision. See the
[Run 16 Ubuntu USB guide](docs/ubuntu2404-run16-usb.md) for the source revision,
layout, exact boot-file identities, and read-only verification steps.

Run 17 used the same loader and Ubuntu USB and brought up the onboard Wi-Fi.
An out-of-tree NXP IW620 driver built for the exact Run 16 kernel downloaded
the 11.60 firmware, joined a 5 GHz network, and carried an HTTPS download over
Wi-Fi. The published image still blacklists the driver and contains neither
the modules nor the firmware; Run 17 added them to the installed root
filesystem. See the [Wi-Fi guide](docs/ubuntu2404-wifi.md) and the
[Run 17 evidence](evidence/11.60-ubuntu-run-17-wifi.md).

Run 18 booted CachyOS with an opt-in loader build that carries upstream's
13.60 low-memory DMA reservation. Linux saw `[0x01000000, 0x40000000)` as
reserved, reached authenticated wired SSH, and passed a short write and
read-back check on the USB root. Run 18 is counted as the hardware validation
of that build. The build was made because testers reported read/write errors
on the 11.60 port. Those errors have not been reproduced on this console, and
Run 18 does not show that the reservation fixes them. The DMA build is for
testers who want to try it; Run 15 remains the release baseline. The built ELF
is published with the
[`firmware-11.60-dma-e820-run18` loader release](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-run18).
See the [Run 18 evidence](evidence/11.60-cachyos-run-18-dma-e820.md) and the
[tester guide](docs/ubuntu2404-tester-guide.md), which covers this ELF with
the [Ubuntu 24.04 image built by CI](https://github.com/gzimbric/ps5-linux-image/releases/tag/ubuntu2404-1160-build-3).
That pairing has not been booted yet.

The public Ubuntu profile uses `ps5` / `ubuntu` as its initial login. Change
that password immediately after first login, before exposing SSH beyond a
trusted local network.

The loader source for Run 15 is published at
[gzimbric/ps5-linux-loader `firmware-11.60-sonic-display`](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display)
(tested source commit `e0b7a2e`; reproducible release-check commit `69657e6`).
It is source only; build it yourself. See
[upstream references](docs/upstream-references.md#published-1160-loader-source)
for how its commits map to the source hashes recorded in the evidence.

| Boundary | 11.60 result |
|---|---|
| Byepervisor resume strike | Pass, 16 of 16 GameOS VMCBs written and verified |
| Sonic-style resume carrier, HV transition, and Linux transfer | Pass; authenticated Linux userspace in Runs 10, 12, 14, 15, 16, 17, and 18 |
| Linux 7.1.7 and 54,376,639-byte loader input | Pass in Runs 15 and 16; their initrd contents differ as documented |
| Ubuntu 24.04 control image | Pass in Run 16 with the exact Run 15 loader; authenticated SSH and visible desktop |
| Onboard Wi-Fi (IW620) | Pass in Run 17 with separately built modules and the 11.60 firmware; scan, 5 GHz association, and an HTTPS download over Wi-Fi |
| Opt-in DMA E820 loader build | Pass in Run 18 with CachyOS; intended e820 reservation, authenticated SSH, and a 12 GiB USB write and read-back check; display not recorded as observed |
| Run 15 CachyOS physical USB boot partition | Pass; FAT verification succeeded and the active files matched the working boot-media identities |
| Sonic PRE1/PRE2: VBIOS copy, transmitter call, timed wait | Pass as part of Run 12 |
| Visible HDMI | **Pass in Runs 15 and 16**; physical output was directly observed and corroborated by active DRM state |
| Full Sonic preamble with display table disabled | Fail in Run 11; no SSH |
| PRE3 with runtime MP3 buffer clear and `mp3_initialize(0)` | Fail twice in Run 13; no SSH |
| MP3 initialization without the redundant runtime clear | Pass in Run 14; authenticated SSH, white light, no HDMI |
| MP3 commands 21 and 22 | Present in the successful Run 15 containing sequence; individual returns were not instrumented |
| 29-call display-operation table | Present in the successful Run 15 containing sequence; individual target returns were not instrumented |

Run 15 (`PRE=5`, `OP=29`, clear disabled) is the current hardware-verified
baseline. It is pinned to source commit
`815b1fdc5c76088762e42ad0ad80b0099a54e60d` and combines the three fidelity
corrections established from Sonic's artifact: omit the redundant runtime
clear, store the response buffer before the request buffer with Sonic's exact
gap and alignment, and preserve the outer-call/leaf-tail-jump dispatcher.
Run 14 remains the initializer-only control; Run 13 remains a repeatable
non-working clear-enabled artifact.

The earlier page-alias, inert-wake, and carrier stages remain useful historical
evidence: they established the exact S3 boundary and led to the now-working
copy-to-kernel-text carrier. The superseded pLinux-derived wrapper and direct
PID-1 alias transfer remain negative results, not current candidates. See the
[current sanitized run matrix](evidence/11.60-sonic-display-runs.md), the
[Ubuntu control boot](evidence/11.60-ubuntu-run-16.md), the
[Ubuntu USB build and verification guide](docs/ubuntu2404-run16-usb.md), the
[Sonic 13.60 binary reference](docs/sonic-13.60-reference.md) and the
[11.60 reconstruction plan](docs/11.60-reconstruction-plan.md).

See [the full 11.60 status](docs/11.60-status.md) before attempting another
hardware run. Follow-up kernel work and its evidence limits are tracked in the
[11.60 maintenance backlog](docs/maintenance-backlog.md).

## Why this repository exists

A working hypervisor bypass is necessary for high-firmware Linux, but it is
not the whole Linux port. The loader must also:

1. preserve a known-good bypass state across the payload-requested rest and
   operator wake cycle;
2. load and stage the kernel, initrd, boot parameters, and identity map;
3. move every CPU out of the hypervisor through a controlled VM exit;
4. prevent one CPU from reaching the Linux barrier before its peers;
5. switch to the identity page table and a valid per-CPU stack;
6. park secondary CPUs and let one bootstrap CPU enter Linux;
7. provide firmware-appropriate memory, ACPI, IOMMU, VRAM, and command-line
   data.

Most of the repeated 11.60 crashes came from treating one of those boundaries
as if it were only an offset substitution.

## Repository map

| Path | Purpose |
|---|---|
| `docs/` | Architecture, workflow, failure ledger, current status, and upstream pins |
| `evidence/` | Sanitized hardware evidence without raw console data |
| `firmwares/` | Machine-readable firmware status manifests |
| `templates/` | Consistent run reports for console testing |
| `tools/` | Publication checks, manifest validation, link checks, log classification, and the Wi-Fi load scripts |

The exact Arch/CachyOS `mkinitcpio` changes used for Run 15 are in the
[tested Run 15 initramfs recipe](docs/initrd-recipe.md). Run 16 used a separate
Ubuntu `initramfs-tools` build documented in the
[Ubuntu USB guide](docs/ubuntu2404-run16-usb.md).

## Quick checks

```sh
make check
```

To classify a locally captured 11.60 log without publishing it:

```sh
python3 tools/classify_1160_log.py /path/to/capture.log
```

The classifier reports the last known checkpoint and does not modify the log.

To compare a mounted FAT/EFI partition with the successful Ubuntu Run 16 boot
files without modifying it:

```sh
python3 tools/check_ubuntu2404_usb.py /path/to/mounted-efi
```

Ubuntu images built by the `ps5-linux-image` CI workflow have a different
initrd, so this strict comparison fails on them. The
[tester guide](docs/ubuntu2404-tester-guide.md) covers those images.

## Safe testing rule

Change one irreversible boundary at a time. Each diagnostic should either
return and prove restoration or clearly state that it is the final takeover
attempt. A successful return from a diagnostic proves only the path that the
diagnostic actually exercised.

## What is intentionally excluded

This repository does not contain:

- kernel or hypervisor images;
- decrypted firmware or console keys;
- the IW620 Wi-Fi firmware or built driver modules;
- Linux disk images;
- raw console logs, private network addresses, or local paths;
- built ELF or shellcode binaries;
- the experimental 11.60 loader source or a crash-prone build presented as a
  working display release.

Hashes and small factual offsets are included only as provenance or validation
metadata. See [publication policy](docs/publication-policy.md).

## Related work

- [pLinux5-NG](https://github.com/pLabs5/pLinux5-NG)
- [ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader)
- [11.60 loader source fork](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display)
- [ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image)
- [ps5-linux-mwifiex](https://github.com/ps5-linux/ps5-linux-mwifiex)
- [Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn)
- [PS5 Hypervisor Bypass Porting](https://github.com/gzimbric/ps5-hv-bypass-porting)

## License

Original documentation and tools in this repository are available under the
MIT License. Upstream projects and any future derived patches retain their own
licenses. See [LICENSES/README.md](LICENSES/README.md).
