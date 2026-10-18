# Linux image layout

The 11.60 work used a CachyOS image produced for the PS5 Linux ecosystem. The
image itself is not redistributed here.

The validated layout had:

- a FAT boot partition containing `bzImage`, `initrd.img`, `cmdline.txt`, and
  `vram.txt`;
- a second Linux filesystem partition;
- a command line using `root=LABEL=cachyos`;
- a VRAM reservation of `0x20000000` bytes.

An earlier loader run successfully found and read a 12,702,720-byte bzImage
and a 54,367,236-byte initrd from the first USB mount, then copied both into
the physical staging area.

A later official-loader-derived bounded test used the same 12,702,720-byte
bzImage and a 28,777,476-byte trimmed initrd. Stage 0 read both files and
returned normally. Stage 1 preflighted 2,534 logical 16 KiB pages: one
`linux_info` page, 776 bzImage pages, and 1,757 initrd pages. It installed and
verified the corresponding aliases and then fully rolled them back.

This proves file discovery, source physical translation, and reversible alias
page-table construction for that test set. It was not persistent physical
Linux staging, did not read through the target virtual aliases, and does not
prove that later boot parameters or drivers are correct for firmware 11.60.

## Current authenticated boot media

Runs 10, 12, 14, and 15 used the following active inputs. All four reached
authenticated Linux userspace over wired Ethernet, and Run 15 also produced
physical display output:

| File | Size | SHA-256 |
|---|---:|---|
| `bzImage` | 12,702,720 bytes | `11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde` |
| `initrd.img` | 54,376,639 bytes | `c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f` |
| `cmdline.txt` | 118 bytes | `aec7a85e9ebcf36e4bdaeb89242b898e17817acd40c16db57a3bb9c3117b1da8` |
| `vram.txt` | 11 bytes | `bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0` |
| `kexec.sh` | 136 bytes | `0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52` |

The attached 248,145,510,400-byte physical USB device was resolved separately
from the older read-only backup image that shares its volume name and UUID.
Its 523,239,424-byte FAT32/EFI boot partition passed `diskutil verifyVolume`.
A read-only snapshot of that physical partition produced the exact active-file
hashes above, so no replacement was needed. This directly verifies the boot
partition; macOS did not mount or inspect every file in the Linux root
partition.

The active command line is:

```text
root=LABEL=cachyos rw rootwait console=ttyTitania0 console=tty0 consoleblank=0 mitigations=off idle=halt preempt=full
```

The active VRAM reservation remains `0x20000000`.

The working initramfs is a rebuild of the original 54,367,236-byte 7.1.7
image. See the [tested 11.60 initramfs recipe](initrd-recipe.md) for the exact
firmware and module-option changes. The 9,403-byte size difference is expected
for the recorded build.

For current image sources and supported distributions, use the upstream
[ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) project.
