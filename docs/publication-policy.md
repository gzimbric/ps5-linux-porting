# Publication policy

Publish methods, source, sanitized evidence, hashes, small factual offsets,
and clearly labeled negative results.

Do not publish:

- proprietary kernel, hypervisor, firmware, or boot images;
- decrypted update contents;
- console keys or secrets;
- raw logs containing private addresses, usernames, or local paths;
- Linux disk images copied from another project;
- built payloads whose source and tested state are not reproducible;
- a crash-prone research branch presented as a working release.

A binary hash is useful evidence but is not a substitute for source. If a
future 11.60 patch is published, it should identify its upstream base, retain
the correct upstream license, build from a clean checkout, and reproduce the
tested binary hash.
