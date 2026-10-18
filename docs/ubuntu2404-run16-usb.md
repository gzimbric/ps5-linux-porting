# Run 16 Ubuntu USB build and verification

Run 16 did not use an untouched image from the upstream
[`ps5-linux-image`](https://github.com/ps5-linux/ps5-linux-image) repository.
It used a custom Ubuntu 24.04 build based on upstream commit
`52db0a42302e4a6b5420a11fa00a84841ea5db56`. That upstream revision provides
Ubuntu 26.04, not the tested Ubuntu 24.04 profile.

The custom source is published on the
[`ubuntu2404-1160-tested`](https://github.com/gzimbric/ps5-linux-image/tree/ubuntu2404-1160-tested)
branch. Its immutable source pin is:

```text
commit: 376d8da75e40930f5f687857172eedc60b3da9ba
tree:   47268dfca7b903d2fd6c4ee89cae8db67d0f24c0
```

Use the full commit above when recording this exact source state; the branch
may move as development continues.

The exact Run 16 `bzImage` was supplied by the separate deterministic Run 15
kernel reproduction. That build fixed the KBUILD user and host and used a date
shim. The public image branch now integrates the same kernel recipe. Kernel
reproduction and image assembly remain separate stages; their validation status
and limits are recorded below.

## Public image login

The public Ubuntu profile starts with these credentials:

```text
username: ps5
password: ubuntu
```

Change the password immediately after the first login:

```sh
passwd
```

Do not expose SSH beyond a trusted local network while the default password is
still active. The recorded Run 16 disk used an operator-specific SSH key and
key-only login, so its root filesystem is not byte-identical to a public build
that uses the portable default credentials above. The source repository does
not redistribute the disk image, kernel, initrd, or firmware files.

## What the public profile changes

The public profile combines:

- an Ubuntu 24.04 Noble userspace and GNOME desktop;
- the PS5 Linux 7.1.7 kernel used in Run 15;
- a bounded initramfs module list for the USB root, ext4, input, and early
  amdgpu startup;
- the raw Cyan Skillfish firmware and
  `dpm=0 gpu_recovery=0 force_1080p=1` amdgpu options in the initramfs;
- a distinct EFI initrd made by zero-extending the real Ubuntu initramfs to the
  size accepted by the current 11.60 loader;
- wired Ethernet, graphical login, automatic fan setup, bounded display
  re-detection, first-boot root expansion, and a bounded local boot report.

Boot reports and related log bundles can contain local IP and MAC addresses,
hostnames, journal identifiers, and other machine-specific details. Review and
redact them before sharing.

Ethernet is the expected network path for this profile. The console tested in
Run 16 has onboard Marvell IW620-family hardware, but the required firmware is
not available in this image. The public profile therefore blacklists the
onboard wireless driver and does not attempt to load it; it does not provide
working onboard Wi-Fi.

During boot, the fan service automatically requests the tested ICC servo
pattern `3`. Run 16 established that the service completed and that the request
was accepted. It did not provide fan RPM telemetry or establish a particular
temperature or cooling-performance result.

Matching the USB files is not enough to reproduce the complete boot chain.
Run 16 also used the 169,872-byte Run 15 loader with SHA-256
`422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336`.
The verifier on this page does not inspect the separately sent loader ELF.

## Exact evidence versus loader compatibility

There are two different standards to keep separate:

1. **Byte-identical Run 16 boot files** have every size and SHA-256 value in
   the table below. This is the strongest comparison with the successful run.
2. **A loader-compatible variation** may have a different initrd or command
   line. The current 11.60 loader gates the bzImage and initrd by size, not by
   SHA-256. That only means the loader will read them; it does not establish
   that a different kernel, initramfs, root filesystem, or command line will
   boot or display correctly.

These hashes identify the files from the successful run. They do not mean that
unrelated root-filesystem metadata matters to the loader.

## Tested partition layout

The source image was 16,777,216,000 bytes and used 512-byte logical sectors
with this GPT layout:

| Partition | Filesystem | Label | Start sector | End sector | Size (sectors) | Role |
|---|---|---|---:|---:|---:|---|
| 1 | ext4 | `ubuntu2404` | 1,024,000 | 32,765,951 | 31,741,952 | Linux root filesystem |
| 2 | FAT32/EFI | `boot` | 2,048 | 1,023,999 | 1,021,952 | Loader-visible boot files |

Partition 2 begins at 1 MiB and partition 1 begins at 500 MiB, so their
physical order is the reverse of their partition numbers. On the tested boot,
Linux mounted the root as `/dev/sda1` and the EFI partition as `/dev/sda2`.
Those device names are observations, not portable instructions: identify a
drive by filesystem label and size instead of guessing a device name.

The root partition expanded after the image was written to the larger physical
USB drive. A different final drive capacity therefore does not need to match
the source image size.

## Tested boot-file identities

The FAT/EFI partition root contained:

| File | Size | SHA-256 |
|---|---:|---|
| `bzImage` | 12,702,720 | `11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde` |
| `initrd.img` | 54,376,639 | `2eef0352879e091083450b799c75514a450f4110cbc747f640962fdde2dc06c8` |
| `cmdline.txt` | 121 | `6b3c09112fe049d3cbeada65fb3c82bb0f5fcaddce6c0709051df3d9f5a79f6d` |
| `vram.txt` | 11 | `bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0` |
| `kexec.sh` | 136 | `0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52` |

`kexec.sh` is part of the exact image inventory but is not consumed by the
initial PS5 loader.

The unpadded root-filesystem copy was:

| File | Size | SHA-256 |
|---|---:|---|
| `/boot/initrd.img-7.1.7` | 50,803,483 | `996bc02a64404bc84d06c8df0c4143b66932d8af8549f39c82c71677fdec58c9` |

The EFI `initrd.img` is that exact 50,803,483-byte file followed by 3,573,156
zero bytes. Only the EFI copy is padded; the real initramfs under `/boot`
remains unchanged.

The exact command line, including its terminating newline in the file, is:

```text
root=LABEL=ubuntu2404 rw rootwait console=ttyTitania0 console=tty0 consoleblank=0 mitigations=off idle=halt preempt=full
```

The exact `vram.txt` value is `0x20000000`, also followed by a newline.

For provenance only, the complete 16,777,216,000-byte source image had
SHA-256
`bf4bca3ab6583c74eb06b17e8c3e4243972690a38fa40bd9a652c6d71a7ee347`.
The whole-image hash can change with operator-specific or package metadata and
is not a loader gate.

## Build validation status

The published branch records the custom Ubuntu profile and is the source base
for continued work. Its clean kernel-only build reproduced the exact
12,702,720-byte `bzImage`, and a separate clean userspace and full-image
assembly reused that clean-validated package. The resulting image passed the
raw-image checks, including the root initramfs, zero-padded EFI copy, and exact
kernel, command-line, VRAM, and `kexec.sh` identities. The release check allows
a rebuilt initrd with different bytes when its inspected contents and tested
loader-size envelope pass; use the strict mounted-partition comparison below
before calling an initrd byte-identical to Run 16.

This is not a claim that one command starting with empty caches reproduces the
complete image. The validated full-image assembly intentionally reused the
package from the separate clean kernel gate. The public profile also differs
from the recorded operator disk in credentials and SSH configuration, so its
root filesystem and whole-disk hash are not expected to be byte-identical.

Package repositories and archive timestamps can change a compressed initramfs.
Treat a different hash as a different artifact even when its inspected contents
are equivalent. Do not claim a byte-identical reproduction unless all five EFI
files match the table. The branch documents the two-stage build and provides
files to compare; it is not evidence of an empty-cache one-command or
byte-identical whole-disk reproduction.

## Read-only verification

Before flashing a newly built raw image, use the image-source branch's
[raw-image verifier](https://github.com/gzimbric/ps5-linux-image/blob/ubuntu2404-1160-tested/scripts/verify-ubuntu2404-boot.sh).
It opens the image read-only and checks the GPT geometry, filesystem labels,
boot files, installed kernel tree, services, account policy, and recipe marker:

```sh
./scripts/verify-ubuntu2404-boot.sh \
  --image output/ps5-ubuntu2404.img
```

After mounting the FAT/EFI partition from a flashed drive, run this repository's
strict boot-file verifier against its mount point:

```sh
python3 tools/check_ubuntu2404_usb.py /path/to/mounted-efi
```

On a Linux system that also has the ext4 root mounted, verify the unpadded
initramfs and its relationship to the EFI copy:

```sh
python3 tools/check_ubuntu2404_usb.py /path/to/mounted-efi \
  --root-initrd /path/to/mounted-root/boot/initrd.img-7.1.7
```

The mounted-partition verifier opens files read-only. It does not mount, copy,
rename, truncate, or otherwise modify the image or USB drive. It compares file
identities only; it does not inspect GPT geometry or filesystem labels. A
failure reports the observed size or hash without attempting a repair.

Also confirm the filesystem labels from Linux:

```sh
lsblk -o NAME,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

The exact Run 16 command line requires a root filesystem labeled
`ubuntu2404`. If the root label differs, copying the exact command line will
point Linux at the wrong filesystem.

## Adapting another image

Do not copy the Run 16 Ubuntu initrd onto a different distribution's root
filesystem. Build the initramfs from that root filesystem with its matching
modules and firmware, then stage a separate EFI copy. The current 11.60 loader
requires the EFI copy to be exactly 54,376,639 bytes.

If the real initramfs is smaller, expanding a staged copy with `truncate` adds
zero bytes. Verify that the staged file begins with the complete real
initramfs before replacing the EFI copy. If the real initramfs is larger than
54,376,639 bytes, stop: truncating it would corrupt the archive, and the
current loader will reject its real size.

The command line must use the actual root label for that image. Such an
adaptation will have different hashes and is a new test candidate, not an exact
Run 16 reproduction. Keep the
[Run 15 CachyOS initramfs recipe](initrd-recipe.md) separate; it uses
`mkinitcpio` and does not produce this Ubuntu initramfs.
