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

A later official-loader-derived bounded test used the same 12,702,720-byte
bzImage and a 28,777,476-byte trimmed initrd. Stage 0 read both files and
returned normally. Stage 1 preflighted 2,534 logical 16 KiB pages: one
`linux_info` page, 776 bzImage pages, and 1,757 initrd pages. It installed and
verified the corresponding aliases and then fully rolled them back.

This proves file discovery, source physical translation, and reversible alias
page-table construction for that test set. It was not persistent physical
Linux staging, did not read through the target virtual aliases, and does not
prove that later boot parameters or drivers are correct for firmware 11.60.

For current image sources and supported distributions, use the upstream
[ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) project.
