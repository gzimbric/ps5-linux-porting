# Linux image layout

The successful 11.60 work used two Linux USB images: CachyOS in Run 15 and a
custom Ubuntu 24.04 build in Run 16. Neither disk image is redistributed here.

## Run 15 CachyOS layout

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

## Run 15 CachyOS authenticated boot media

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

The Run 15 248,145,510,400-byte physical USB device was resolved separately
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
image. See the [tested Run 15 initramfs recipe](initrd-recipe.md) for the exact
firmware and module-option changes. The 9,403-byte size difference is expected
for the recorded build.

## Run 16 Ubuntu layout

Run 16 used the same loader and bzImage with a custom Ubuntu 24.04 root
filesystem. It did not use the stock image produced by the pinned upstream
`ps5-linux-image` revision.

Its source image used an ext4 partition 1 labeled `ubuntu2404` for the root and
a FAT32/EFI partition 2 labeled `boot` for the loader-visible files. Partition
2 was physically first on the disk. The root partition later expanded to the
larger USB media.

| File | Size | SHA-256 |
|---|---:|---|
| `bzImage` | 12,702,720 bytes | `11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde` |
| EFI `initrd.img` | 54,376,639 bytes | `2eef0352879e091083450b799c75514a450f4110cbc747f640962fdde2dc06c8` |
| `cmdline.txt` | 121 bytes | `6b3c09112fe049d3cbeada65fb3c82bb0f5fcaddce6c0709051df3d9f5a79f6d` |
| `vram.txt` | 11 bytes | `bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0` |
| `kexec.sh` | 136 bytes | `0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52` |

The unpadded Ubuntu initramfs was 50,803,483 bytes with SHA-256
`996bc02a64404bc84d06c8df0c4143b66932d8af8549f39c82c71677fdec58c9`.
The EFI copy is that exact content followed by 3,573,156 zero bytes. The
command line uses `root=LABEL=ubuntu2404`.

See the [Run 16 Ubuntu USB guide](ubuntu2404-run16-usb.md) for the custom source,
complete command line, build-validation scope, and read-only verifiers.
The upstream
[ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) project remains
the source base and supports other distributions, but its stock image at the
pinned base commit is not the Run 16 image.
