# Publication policy

Publish methods, source, sanitized evidence, hashes, small factual offsets,
and clearly labeled negative results. Reproducible derivatives of public,
redistributable bases may also be published when the release identifies its
source revision, preserves the applicable licenses, provides the complete
build recipe, and clearly separates build verification from hardware testing.
An unbooted artifact belongs in a prerelease, not a hardware-validated release.

Do not publish:

- proprietary PS5 kernel, hypervisor, system-software, firmware, or boot
  images, including firmware extracted from a console at runtime;
- decrypted update contents;
- console keys or secrets;
- raw logs containing private addresses, usernames, or local paths;
- Linux disk images copied from another project without redistribution rights
  and a reproducible derivation;
- built payloads whose source and tested state are not reproducible;
- a crash-prone research branch presented as a working release.

A binary hash is useful evidence but is not a substitute for source. Published
11.60 patches, loaders, and Linux images should identify their upstream bases,
retain the correct upstream licenses, build from clean checkouts, and reproduce
the released hashes. A public Linux image may contain redistributable upstream
firmware under its own license; it must never contain private PS5 dumps, console
keys, or the loader-extracted IW620 firmware.
