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
as a working port while the final takeover is unvalidated.

The upstream control-flow comparison uses these source files directly:

- [`source/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/source/main.c)
  prepares the resume blob, arms the firmware-specific HV path, requests rest,
  and does not launch a second post-wake payload;
- [`shellcode_kernel/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/main.c)
  prepares Linux and invokes the all-core VMMCALL rendezvous in the resume
  context; and
- [`shellcode_kernel/boot_linux.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/boot_linux.c)
  installs the identity map and HV shellcode before staging the Linux inputs.
