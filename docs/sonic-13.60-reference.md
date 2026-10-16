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

The embedded wake blob is `0x6910` bytes with SHA-256
`c342595b2842d12fb165983482efc7266bc2f914c435368df44f929ba346e740`.

### Source correspondence

Static reconstruction shows that the blob is an extension of the public wake
shellcode, not a replacement design:

| Sonic blob offset | Public-source equivalent | Observed change |
|---:|---|---|
| `0x1000` | `shellcode_kernel/main.c::main` | Adds 13.xx acceptance, diagnostics, and the 13.xx display sequence |
| `0x1690` | `patch_hv` | Retains the parameter-driven VM-exit redirect and identity-CR3 trampoline |
| `0x1740` | `boot_linux` | Adds diagnostics, partial NULL guards, a delay, and 13.xx display operations |
| `0x1f10` | `hv_defeat_0304` | Preserves the legacy 3.xx/4.xx IOMMU path; high firmware does not use it |
| `0x2260` | `activate_uart` | Remains unsafe when `kernel_uart_override` is absent |
| `0x23a0` | `init_global_pointers` | Copies the same `0x98`-byte argument ABI |

The 13.xx display program contains 29 firmware-specific calls. Static
reconstruction also establishes the preamble order: copy the 64-KiB VBIOS,
issue the exact transmitter enable structure, wait through TSC delta
349,999,999, call `mp3_initialize(0)`, invoke MP3 commands 21 and 22, stage
Linux, and dispatch the ordered table. Sonic's MP3 request and response
buffers are pre-zeroed static storage; the wake routine does not clear them at
runtime.

The 11.60 source now contains structurally matched targets and the exact
29-record table, but the table has not been executed in a hardware-authenticated
incremental run. Reconstructed offsets are static evidence until a bounded
hardware test validates them.

### Firmware-specific inputs

The outer ELF supplies the blob with 13.60-specific kernel and physical
addresses. Examples include `printf` at `ktext+0x25d410`, SMP rendezvous at
`ktext+0xb03ba0`, the no-barrier callback at `ktext+0x261e08`, the CFI handler
at `ktext+0x44f8c0`, the VM-exit handler at physical `0x62847375`, and the HV
cave at physical `0x62806f00`. These values are evidence about 13.60 only.

For the exact-11.60 source port, the measured inputs include
`printf=ktext+0x535a50`, `smp_rendezvous=ktext+0xb739d0`, the no-barrier CFI
alias at `ktext+0x316318`, the CFI handler at `ktext+0x4ebeb0`, VM-exit handler
PA `0x62847551`, and Sonic's identity-mapped HV padding at PA `0x62806f00`.
The failed earlier `0x6284ac20` candidate is not the current cave. Display
inputs are `G_VBIOS=ktext+0x3db7a40`, transmitter control at
`ktext+0xc800c0`, MP3 initialization at `ktext+0xa88270`, and MP3 invocation at
`ktext+0xa86e70`. Their individual provenance and remaining proof obligations
are recorded in the
[11.60 status](11.60-status.md); listing them here does not promote them all to
hardware-validated wake-context inputs.

## Implication for the 11.60 port

The superseded pLinux5-NG-derived 11.60 path was not a direct port of this
design. It skipped image-page installation and `prepare_resume`, redirected the
MP-startup hook into a new wake wrapper, constructed retained copy lists and a
cloned PML4, staged Linux from that hook context, and retained a userland
post-resume path.

Those changes pursued the same final objective, but their execution context,
memory contract, and ordering differed from the known-working reference. The
11.60 reconstruction therefore started from the official loader and kept
Sonic's division of responsibilities:

- use the hardware-validated 11.60 Byepervisor hook and VMCB discovery only for
  the root-0 AP step;
- restore the official image-page aliases and `prepare_resume` step;
- port the high-firmware kernel wake shellcode deliberately; and
- remove the custom resumed-userland takeover.

That reconstruction was subsequently implemented on the official loader
lineage. Its Sonic-style carrier, HV transition, Linux staging, and final
rendezvous reached authenticated Linux userspace on 11.60 in Runs 10, 12, 14,
and 15. Run 15 also produced physical display output, validating the complete
display path as well as the architecture.

The current display work uses 11.60-native homologs rather than transplanting
13.60 addresses. Run 12 validates the containing VBIOS/transmitter/wait stage.
The combined Run 13 PRE3 block failed twice after adding both a non-Sonic
runtime buffer clear and MP3 initialization. Run 14 removed only that clear,
kept the direct 11.60 `mp3_initialize(0)` call, and reached authenticated Linux.
This validates the initializer and shows why production must retain Sonic's
pre-zeroed-buffer behavior without a wake-time clear. Run 15 then matched
Sonic's response-first buffer layout and outer-call/leaf-tail-jump dispatcher,
enabled commands 21 and 22 and all 29 table records, and produced physical
HDMI plus authenticated Linux. No call, argument, or ordering step from Sonic's
recovered sequence is omitted.

## Public corroboration

- [Official PS5 Linux loader](https://github.com/ps5-linux/ps5-linux-loader)
- [Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn)
- [Sonic's S3 AP-launch write-up](https://github.com/soniciso1/ps5-hv-writeups/blob/main/s3-resume-startup_mp-ap-launch.md)

The write-up independently documents the post-`resumectx`, pre-
`acpi_wakeup_cpus` launch window, the S3-retained executable page at
`0x3ffff000`, and the need for dynamic alias discovery on 13.60.
