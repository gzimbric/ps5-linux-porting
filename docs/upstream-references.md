# Upstream references

The following revisions were checked on 2026-10-15.

| Project | Branch | Commit | Role |
|---|---|---|---|
| [pLabs5/pLinux5-NG](https://github.com/pLabs5/pLinux5-NG) | `master` | `3a7ea6f6c874773641b21d20f95f5df6f648ac40` | High-firmware Linux integration |
| [ps5-linux/ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader) | `main` | `64637c177eaed277fb6ccce394cbb29dd047b893` | Established Linux boot path |
| [ps5-linux/ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) | `main` | `52db0a42302e4a6b5420a11fa00a84841ea5db56` | Image builder and boot files |
| [PS5Dev/Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn) | `main` | `ea04f7132b837087f552c57261cb800481a3a910` | Upstream high-firmware bypass |
| [gzimbric/Byepervisor-Reborn](https://github.com/gzimbric/Byepervisor-Reborn) | `firmware-11.60-pr` | `a1536c4e8c88536e7d7b676270603326efba098e` | Hardware-validated 11.60 bypass fork |
| [gzimbric/ps5-hv-bypass-porting](https://github.com/gzimbric/ps5-hv-bypass-porting) | `main` | `0a7f263d5cc4bb91984d0b00d68daaa0561a4542` | Bypass porting methods and evidence rules |

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
loader lineage. The latest hardware-tested display-isolation source identity is
local commit `5f922ead8859e2229d92e3d074e24fddf3f7932e`. Runs 11 through 13 were
built from that commit. Run 12 (`PRE=2`, `OP=0`) reached authenticated Linux;
the exact Run 13 (`PRE=3`, `OP=0`) ELF failed twice. This repository records
the commit and artifact hashes as provenance but does not vendor the
experimental loader source or describe it as a working display release.

The upstream control-flow comparison uses these source files directly:

- [`source/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/source/main.c)
  prepares the resume blob, arms the firmware-specific HV path, requests rest,
  and does not launch a second post-wake payload;
- [`shellcode_kernel/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/main.c)
  prepares Linux and invokes the all-core VMMCALL rendezvous in the resume
  context; and
- [`shellcode_kernel/boot_linux.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/boot_linux.c)
  installs the identity map and HV shellcode before staging the Linux inputs.
