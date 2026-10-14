# PS5 Linux Porting

Source-first notes, evidence, and small tools for porting the PS5 Linux loader
to additional firmware.

This is a research companion to
[pLinux5-NG](https://github.com/pLabs5/pLinux5-NG),
[ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader), and
[Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn). It is not a
Linux distribution, jailbreak bundle, or ready-to-run payload release.

## Current result

The active case study is a regular PS5 on firmware 11.60.

Linux does not boot yet. The port has passed every reversible checkpoint up to
the final hypervisor handoff:

| Boundary | 11.60 result |
|---|---|
| Byepervisor resume strike | Pass, 16 of 16 GameOS VMCBs written and verified |
| Kernel hook and cleanup | Pass |
| Executable kernel-text cave | Pass |
| All-core no-op rendezvous | Pass |
| All-core stock VMMCALL | Pass |
| Linux files found and loaded from USB | Pass |
| bzImage and initrd staged in physical memory | Pass |
| Live VMMCALL handler identity | Pass |
| Modified handler to identity-CR3 shellcode entry | Not yet isolated |
| Linux `startup_64` reached | Not observed |

The last captured run reached `Linux images staged successfully` and then the
console stopped responding. That makes the modified hypervisor handler and the
first instructions after its redirect the current investigation boundary.

See [the full 11.60 status](docs/11.60-status.md) before attempting another
hardware run.

## Why this repository exists

A working hypervisor bypass is necessary for high-firmware Linux, but it is
not the whole Linux port. The loader must also:

1. preserve a known-good bypass state across the operator-controlled rest and
   wake cycle;
2. load and stage the kernel, initrd, boot parameters, and identity map;
3. move every CPU out of the hypervisor through a controlled VM exit;
4. prevent one CPU from reaching the Linux barrier before its peers;
5. switch to the identity page table and a valid per-CPU stack;
6. park secondary CPUs and let one bootstrap CPU enter Linux;
7. provide firmware-appropriate memory, ACPI, IOMMU, VRAM, and command-line
   data.

Most of the repeated 11.60 crashes came from treating one of those boundaries
as if it were only an offset substitution.

## Repository map

| Path | Purpose |
|---|---|
| `docs/` | Architecture, workflow, failure ledger, current status, and upstream pins |
| `evidence/` | Sanitized hardware evidence without raw console data |
| `firmwares/` | Machine-readable firmware status manifests |
| `templates/` | Consistent run reports for console testing |
| `tools/` | Publication checks, manifest validation, link checks, and log classification |

## Quick checks

```sh
make check
```

To classify a locally captured 11.60 log without publishing it:

```sh
python3 tools/classify_1160_log.py /path/to/capture.log
```

The classifier reports the last known checkpoint and does not modify the log.

## Safe testing rule

Change one irreversible boundary at a time. Each diagnostic should either
return and prove restoration or clearly state that it is the final takeover
attempt. A successful return from a diagnostic proves only the path that the
diagnostic actually exercised.

## What is intentionally excluded

This repository does not contain:

- kernel or hypervisor images;
- decrypted firmware or console keys;
- Linux disk images;
- raw console logs, private network addresses, or local paths;
- built ELF or shellcode binaries;
- the unvalidated 11.60 takeover patch.

Hashes and small factual offsets are included only as provenance or validation
metadata. See [publication policy](docs/publication-policy.md).

## Related work

- [pLinux5-NG](https://github.com/pLabs5/pLinux5-NG)
- [ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader)
- [ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image)
- [Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn)
- [PS5 Hypervisor Bypass Porting](https://github.com/gzimbric/ps5-hv-bypass-porting)

## License

Original documentation and tools in this repository are available under the
MIT License. Upstream projects and any future derived patches retain their own
licenses. See [LICENSES/README.md](LICENSES/README.md).
