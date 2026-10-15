# Sonic 13.60 binary reference

Date: 2026-10-15

This document records static observations from an independently supplied
`1360linux.elf`. The private binary is not redistributed.

| Property | Value |
|---|---|
| Size | 237,448 bytes |
| SHA-256 | `e51a0298cb2c97b71be0ddad9f070b574c110c899d9fe513562355272fc81226` |
| Format | x86-64 PIE ELF, not stripped |

The ELF is the primary architectural reference for the high-firmware Linux
handoff. Public repositories establish source lineage, but do not replace
behavior observed in the shipped artifact.

## Observed top-level sequence

```text
setup_env
  -> fetch_linux
  -> prepare_resume
  -> hv_defeat_13xx
  -> sleep(5)
  -> enter_rest_mode
  -> sleep forever if the outer payload resumes
```

This is one coupled payload. There is no second userland Linux-launch phase.

## Image staging before suspend

`fetch_linux` maps bzImage and initrd with shared anonymous mappings, reads the
files, builds `linux_info`, and installs a stable kernel alias for every 16 KiB
image page. `prepare_resume` similarly installs every page of the embedded
kernel wake shellcode, fills its argument block, removes execute-only text
protection, and invalidates the kernel pmap.

These mappings are aliases of the populated user pages. They are not a second
full image copy.

## 13.xx HV defeat

The outer payload combines the public Byepervisor-Reborn resume hook with the
original loader's S3 wake chain:

- a retained executable AP payload is placed at physical `0x3ffff000`;
- the `HV_MP_STARTUP_CALL` window launches it under NPT root 0;
- the AP payload dynamically finds and validates all 16 GameOS VMCBs;
- it clears nested paging and the VMCB clean field for all 16; and
- the original S3 wake chain enters the separately installed kernel wake
  shellcode.

The AP payload and the kernel wake shellcode have different jobs. The AP
payload changes the VMCBs. It does not stage or start Linux.

## Kernel wake shellcode

The embedded 26,896-byte wake shellcode accepts the 13.xx family, initializes
its copied arguments, disables the kernel CFI check, and executes this sequence:

1. Patch the live HV VM-exit path.
2. Build a low identity-map page table at physical `0x100000000`.
3. Install the HV/Linux transition code at physical `0x100003000`.
4. Copy VBIOS data and perform the 13.xx display operations.
5. Copy `linux_info` to physical `0x100005000`.
6. Set the final bzImage destination to physical `0x100009000` and the initrd
   destination to the next 16 KiB-aligned address.
7. Copy bzImage and initrd from the kernel aliases installed before suspend.
8. Rendezvous every CPU on a callback whose body is `vmmcall(1)`.

The installed HV transition disables the remaining SVM state, builds Linux
boot parameters and the e820 map, copies the protected-mode kernel, and enters
Linux. No part of this successful path returns to resumed GameOS userland.

## Implication for the 11.60 port

The current pLinux5-NG-derived 11.60 path is not a direct port of this design.
It skips image-page installation and `prepare_resume`, redirects the MP-startup
hook into a new wake wrapper, constructs retained copy lists and a cloned PML4,
stages Linux from that hook context, and retains a userland post-resume path.

Those changes may pursue the same final objective, but their execution context,
memory contract, and ordering differ from the known-working reference. The
11.60 reconstruction should therefore start from the official loader and keep
Sonic's division of responsibilities:

- use the hardware-validated 11.60 Byepervisor hook and VMCB discovery only for
  the root-0 AP step;
- restore the official image-page aliases and `prepare_resume` step;
- port the high-firmware kernel wake shellcode deliberately; and
- remove the custom resumed-userland takeover.

## Public corroboration

- [Official PS5 Linux loader](https://github.com/ps5-linux/ps5-linux-loader)
- [Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn)
- [Sonic's S3 AP-launch write-up](https://github.com/soniciso1/ps5-hv-writeups/blob/main/s3-resume-startup_mp-ap-launch.md)

The write-up independently documents the post-`resumectx`, pre-
`acpi_wakeup_cpus` launch window, the S3-retained executable page at
`0x3ffff000`, and the need for dynamic alias discovery on 13.60.
