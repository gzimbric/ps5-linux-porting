# Tested 11.60 initramfs recipe

Run 15 did not use the untouched 7.1.7 initramfs. The original root-filesystem
copy was 54,367,236 bytes. The working copy was rebuilt after adding the raw
Cyan Skillfish GPU firmware and the PS5 amdgpu module options, and was
54,376,639 bytes.

The exact 9,403-byte difference strongly matches the older, unmodified
initramfs. Confirm it by hash: the original root-filesystem copy used here was
`ba6dd1d0e69149e6be60bfd655b4bfc8cac0eee546e1ba478f3bdd1240965a56`.

## What changed

The 7.1.7 PS5 kernel requested bare `cyan_skillfish2_pfp.bin` and
`cyan_skillfish2_sdma.bin` names during early KMS startup and logged error
`-2`. The image had matching `.bin.zst` package files. The rebuild below made
the raw files explicit and the next image initialized amdgpu; that result does
not isolate why the kernel's compressed-firmware fallback did not satisfy the
first probe. The working initramfs contains:

- raw `ce`, `me`, `mec`, `pfp`, `rlc`, `sdma`, and `sdma1` firmware files;
- `cyan_skillfish2_mec2.bin` as a link to `cyan_skillfish2_mec.bin`;
- `/etc/modprobe.d/ps5-amdgpu.conf` with
  `dpm=0 gpu_recovery=0 force_1080p=1`.

It was built on the running Arch/CachyOS PS5 image with `mkinitcpio` for kernel
7.1.7. The firmware came from the image's installed `linux-firmware-amdgpu`
package; no firmware blob is stored in this repository.

The exact package set used for the recorded image was:

```text
linux-ps5 7.1.7-1
linux-firmware-amdgpu 20260810-2
mkinitcpio 41.1-1
mkinitcpio-busybox 1.36.1-1
zstd 1.5.7-3
```

`/etc/mkinitcpio.conf` used `MODULES=(amdgpu)` and
`HOOKS=(base udev modconf kms keyboard block filesystems fsck)`. Its
compression settings were commented, so mkinitcpio 41.1 used its zstd
default. The build script checks these inputs before changing anything.

## Build

White light with no HDMI can still be a headless Linux boot. Connect wired
Ethernet first, check the router's DHCP leases or the expected address, and
try SSH. If it answers, clone this repository on the PS5 and run:

```sh
sudo ./tools/build_1160_initrd.sh 7.1.7 /tmp/ps5-initrd-1160.img
```

The script refuses package, kernel, mkinitcpio, pre-existing-file, and output
mismatches. It expands the seven installed Cyan Skillfish `.bin.zst` files
without deleting them, creates the `mec2` link, installs the tested module
options, builds the new image, and prints an inventory and hash.

The Run 15 result was:

```text
54376639 bytes
c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f
```

Package versions and archive timestamps can change a compressed initramfs, so
check its contents as well as its size. The published 11.60 loader defaults to
the exact Run 15 size and will refuse a different size rather than attempting
an untested boot.

If SSH never comes up, do the same work from another Linux installation. Use
`lsblk` to identify the PS5 USB device, mount its Linux root partition, mount
the FAT partition at that root's `/boot/efi`, bind-mount `/dev`, `/proc`,
`/sys`, and `/run`, then enter it with `arch-chroot`. Do not guess device names;
on the tested image the Linux root was partition 1 and the FAT boot partition
was partition 2.

## Install

Keep both the root-filesystem and FAT boot copies in sync. The following uses
new backup and staging names, verifies the staged copies, and only then renames
them into place. Backups stay outside `/boot` so a script that selects an
`initrd.img*` file cannot mistake a backup for the active image.

```sh
new=c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f
test "$(sha256sum /tmp/ps5-initrd-1160.img | awk '{print $1}')" = "$new"
sudo test ! -e /var/backups/ps5-linux/initrd.img-7.1.7.before-1160-display
sudo test ! -e /var/backups/ps5-linux/efi-initrd.img.before-1160-display
sudo test ! -e /boot/initrd.img-7.1.7.1160-staging
sudo test ! -e /boot/efi/initrd.img.1160-staging
sudo install -d -m 0700 /var/backups/ps5-linux
sudo cp -a /boot/initrd.img-7.1.7 /var/backups/ps5-linux/initrd.img-7.1.7.before-1160-display
sudo cp -a /boot/efi/initrd.img /var/backups/ps5-linux/efi-initrd.img.before-1160-display
sudo install -m 0644 /tmp/ps5-initrd-1160.img /boot/initrd.img-7.1.7.1160-staging
sudo install -m 0644 /tmp/ps5-initrd-1160.img /boot/efi/initrd.img.1160-staging
sudo sync
test "$(sudo sha256sum /boot/initrd.img-7.1.7.1160-staging | awk '{print $1}')" = "$new"
test "$(sudo sha256sum /boot/efi/initrd.img.1160-staging | awk '{print $1}')" = "$new"
sudo mv /boot/initrd.img-7.1.7.1160-staging /boot/initrd.img-7.1.7
sudo mv /boot/efi/initrd.img.1160-staging /boot/efi/initrd.img
sudo sync
sudo sha256sum /boot/initrd.img-7.1.7 /boot/efi/initrd.img
```

The tested command line did not contain a forced `video=DP-1:...` mode:

```text
root=LABEL=cachyos rw rootwait console=ttyTitania0 console=tty0 consoleblank=0 mitigations=off idle=halt preempt=full
```

The exact successful boot-media identities are recorded in
[Linux image layout](image-layout.md#current-authenticated-boot-media).

## Scope

This recipe reproduces the initramfs change made between the first headless
7.1.7 boot and the later display tests. The Run 15 loader's complete pre-Linux
display sequence was also required for the observed HDMI result. Rebuilding
the initramfs alone does not turn an older loader into the Run 15 loader.

The tested root filesystem also had a bounded connector re-detection service.
It completed successfully in Run 15, but the run did not establish whether it
was necessary because it preserves an already connected link. It is therefore
not folded into the initramfs recipe.
