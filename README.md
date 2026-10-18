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

The loader source for Run 15 is published at
[gzimbric/ps5-linux-loader `firmware-11.60-sonic-display`](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display)
(tested source commit `e0b7a2e`; reproducible release-check commit `69657e6`).
It is source only; build it yourself. See
[upstream references](docs/upstream-references.md#published-11.60-loader-source)
for how its commits map to the source hashes recorded in the evidence.

| Boundary | 11.60 result |
|---|---|
| Byepervisor resume strike | Pass, 16 of 16 GameOS VMCBs written and verified |
| Sonic-style resume carrier, HV transition, and Linux transfer | Pass; authenticated Linux userspace in Runs 10, 12, 14, and 15 |
| Current kernel and 54,376,639-byte initrd | Pass; authenticated wired networking and SSH |
| Attached physical USB boot partition | Pass; FAT verification succeeded and active files hash-match the successful run inputs |
| Sonic PRE1/PRE2: VBIOS copy, transmitter call, timed wait | Pass as part of Run 12 |
| Visible HDMI | **Pass in Run 15**; physical output was directly observed and corroborated by active DRM state |
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
| `tools/` | Publication checks, manifest validation, link checks, and log classification |

The exact GPU-firmware and module-option changes used to rebuild the working
7.1.7 initramfs are in the [tested 11.60 initramfs recipe](docs/initrd-recipe.md).

## Quick checks

```sh
make check
```

To classify a locally captured 11.60 log without publishing it:

```sh
python3 tools/classify_1160_log.py /path/to/capture.log
```

The classifier reports the last known checkpoint and does not modify the log.

## Safe testing rule

Change one irreversible boundary at a time. Each diagnostic should either
return and prove restoration or clearly state that it is the final takeover
attempt. A successful return from a diagnostic proves only the path that the
diagnostic actually exercised.

## What is intentionally excluded

This repository does not contain:

- kernel or hypervisor images;
- decrypted firmware or console keys;
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
- [Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn)
- [PS5 Hypervisor Bypass Porting](https://github.com/gzimbric/ps5-hv-bypass-porting)

## License

Original documentation and tools in this repository are available under the
MIT License. Upstream projects and any future derived patches retain their own
licenses. See [LICENSES/README.md](LICENSES/README.md).
