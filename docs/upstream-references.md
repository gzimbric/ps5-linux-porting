# Upstream references

The following revisions were checked through 2026-10-18.

| Project | Branch | Commit | Role |
|---|---|---|---|
| [pLabs5/pLinux5-NG](https://github.com/pLabs5/pLinux5-NG) | `master` | `3a7ea6f6c874773641b21d20f95f5df6f648ac40` | High-firmware Linux integration |
| [ps5-linux/ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader) | `main` | `64637c177eaed277fb6ccce394cbb29dd047b893` | Established Linux boot path |
| [ps5-linux/ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) | `main` | `52db0a42302e4a6b5420a11fa00a84841ea5db56` | Upstream base for the custom Run 16 Ubuntu image |
| [PS5Dev/Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn) | `main` | `ea04f7132b837087f552c57261cb800481a3a910` | Upstream high-firmware bypass |
| [gzimbric/Byepervisor-Reborn](https://github.com/gzimbric/Byepervisor-Reborn) | `firmware-11.60-pr` | `a1536c4e8c88536e7d7b676270603326efba098e` | Hardware-validated 11.60 bypass fork |
| [gzimbric/ps5-hv-bypass-porting](https://github.com/gzimbric/ps5-hv-bypass-porting) | `main` | `0a7f263d5cc4bb91984d0b00d68daaa0561a4542` | Bypass porting methods and evidence rules |
| [gzimbric/ps5-linux-loader](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display) | `firmware-11.60-sonic-display` | `69657e6127db2ff9cc9ac2ad5e5aaebaa8019daf` | Hardware-verified 11.60 loader source with a hash-pinned Run 15 release check |

The local Linux research branch started from pLinux5-NG commit
`d5bd6b9f45c465e466e1e97083c9f162b94aad2c`. It is intentionally not published
as a working port and is now a superseded historical branch.

The active bounded diagnostics start from official loader commit
`64637c177eaed277fb6ccce394cbb29dd047b893`. The Stage 0 and Stage 1 hardware
passes were built from diagnostic source commit
`779af2f58aec61351278dd36cae9306e087ee873`. Their tested ELF hashes are
recorded in [the firmware status](11.60-status.md); the binaries and raw logs are
not redistributed here.

The later Sonic-style 11.60 source port remains based on that same official
loader lineage. Runs 11 through 13 were built from local commit
`5f922ead8859e2229d92e3d074e24fddf3f7932e`. Run 12 (`PRE=2`, `OP=0`)
reached authenticated Linux; the exact Run 13 (`PRE=3`, `OP=0`) ELF failed
twice. Run 14 was built from local commit
`87718a6565703079b96aa0b23a4996ec83308a4c` and passed authenticated Linux
with PRE3's runtime clear disabled while retaining `mp3_initialize(0)`. Run 15
was built from local commit `815b1fdc5c76088762e42ad0ad80b0099a54e60d` and
produced physical display output plus authenticated Linux with the full
Sonic-equivalent sequence. This repository records the commits and artifact
hashes as provenance but does not vendor the loader source or binaries.

## Published 11.60 loader source

The loader source is published, without binaries, on the
[`firmware-11.60-sonic-display`](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display)
branch of the `gzimbric/ps5-linux-loader` fork, on top of official commit
`64637c177eaed277fb6ccce394cbb29dd047b893`.

Before publication, the local commits were rewritten only to replace a
machine-local author address with a GitHub no-reply address. Commit messages,
dates, and file trees are unchanged, so each published commit has the same
tree hash as the local commit recorded in the evidence. The run-relevant
mappings are:

| Use | Local evidence commit | Published commit | Tree |
|---|---|---|---|
| Stage 2A | `a3c1d304daf0e297511846cc9aaab3ced8397954` | `656a9a9776277cddb88ae2a21cf1d99ad2884341` | identical |
| Run 10 | `c0233e2eeac10ac32982d2a20107b37c9cbda159` | `a776ba852a90df1d060c547d0b21a2737c333108` | identical |
| Runs 11-13 | `5f922ead8859e2229d92e3d074e24fddf3f7932e` | `b8e8243b2384ea42e06bffb142bb3c00f8c2b0c5` | identical |
| Run 14 | `87718a6565703079b96aa0b23a4996ec83308a4c` | `2c108c09a349ab95c015df93d268c1de04c826e6` | identical |
| Run 15 and release | `815b1fdc5c76088762e42ad0ad80b0099a54e60d` | `e0b7a2e9ac1fe6ec8de8f1883ba9470ad7ee690d` | `97e96d7d6fbec038812e0a1f9919b1d7c91a9410` |

To confirm the Run 15 source identity, check that
`git rev-parse e0b7a2e^{tree}` prints `97e96d7d6fbec038812e0a1f9919b1d7c91a9410`.
Commit `69657e6127db2ff9cc9ac2ad5e5aaebaa8019daf` adds the Run 15 diagnostic
gates as build defaults, invalidates stale objects when those gates change,
and makes `linux-1160-check` require the authenticated dumps and all three Run
15 artifact hashes. A clean build at that commit reproduced the tested outer
ELF, wake blob, and wake ELF byte for byte. Building requires the PS5 payload
SDK and authenticated 11.60 kernel-text and hypervisor dumps, which are not
distributed. See `PORTING_1160.md` on that branch for build details.

## Published Run 16 image source

Run 16 did not use the stock Ubuntu image from the upstream image builder. Its
custom Ubuntu 24.04 source is published on the
[`ubuntu2404-1160-tested`](https://github.com/gzimbric/ps5-linux-image/tree/ubuntu2404-1160-tested)
branch of the `gzimbric/ps5-linux-image` fork, based on upstream commit
`52db0a42302e4a6b5420a11fa00a84841ea5db56`.

The verified immutable source pin is:

```text
commit: 376d8da75e40930f5f687857172eedc60b3da9ba
tree:   47268dfca7b903d2fd6c4ee89cae8db67d0f24c0
```

The source branch contains no disk image or boot binaries. See the
[Run 16 Ubuntu USB guide](ubuntu2404-run16-usb.md) for the exact media
identities and the distinction between byte identity and loader compatibility.
The exact Run 16 bzImage came from a separate deterministic Run 15 kernel build
with fixed KBUILD user and host plus controlled date behavior. The image branch
now integrates that recipe. The Ubuntu USB guide records the separate kernel
and image-assembly validation results; it does not claim a one-command build
from empty caches.

The upstream control-flow comparison uses these source files directly:

- [`source/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/source/main.c)
  prepares the resume blob, arms the firmware-specific HV path, requests rest,
  and does not launch a second post-wake payload;
- [`shellcode_kernel/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/main.c)
  prepares Linux and invokes the all-core VMMCALL rendezvous in the resume
  context; and
- [`shellcode_kernel/boot_linux.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/boot_linux.c)
  installs the identity map and HV shellcode before staging the Linux inputs.
