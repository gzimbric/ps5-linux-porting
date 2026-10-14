# Linux image layout

The 11.60 work used a CachyOS image produced for the PS5 Linux ecosystem. The
image itself is not redistributed here.

The validated layout had:

- a FAT boot partition containing `bzImage`, `initrd.img`, `cmdline.txt`, and
  `vram.txt`;
- a second Linux filesystem partition;
- a command line using `root=LABEL=cachyos`;
- a VRAM reservation of `0x20000000` bytes.

The loader successfully found and read a 12,702,720-byte bzImage and a
54,367,236-byte initrd from the first USB mount, then copied both into the
physical staging area.

This proves file discovery and staging for that image. It does not prove that
the later Linux boot parameters or drivers are correct for firmware 11.60.

For current image sources and supported distributions, use the upstream
[ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) project.
