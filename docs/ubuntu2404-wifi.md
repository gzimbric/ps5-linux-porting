# Onboard Wi-Fi on the Ubuntu 24.04 image

Run 17 brought up the console's onboard Wi-Fi on the Run 16 Ubuntu USB. The
same loader and USB were used. The driver was an out-of-tree NXP build made for
the exact Run 16 kernel, and the firmware came from the console's own 11.60
kernel data. See the [Run 17 evidence](../evidence/11.60-ubuntu-run-17-wifi.md)
for what was observed.

The published image contains neither the modules nor the firmware and still
blacklists the driver. This repository does not redistribute either.

## Hardware

| Function | Identifier |
|---|---|
| PCI wireless function `40:00.7` | `1b4b:2b56` (NXP/Marvell IW620; the driver reports `PCIEIW620`) |
| USB Bluetooth/WLAN companion | `1286:2059`, bound by `btusb` |

No module in the Run 16 kernel has an alias for the PCI function. The driver
used in Run 17 is NXP's `mlan`/`moal` pair with the PS5 patches from
[`ps5-linux-mwifiex`](https://github.com/ps5-linux/ps5-linux-mwifiex). The
`ps5-mt7921-wifi` mt76/MT7921 driver cannot bind these IDs.

## Driver source

| Source | Branch | Commit |
|---|---|---|
| [ps5-linux/ps5-linux-mwifiex](https://github.com/ps5-linux/ps5-linux-mwifiex) | `main` | `4aff9085530a3cdf7d5fbb124c006cc299ac3605` |
| [nxp-imx/mwifiex](https://github.com/nxp-imx/mwifiex) | `lf-6.18.2_1.0.0` | `a5fe4e194bf99315e349d81d77d6dfacec70757a` |

Apply these `ps5-linux-mwifiex` patches to the NXP tree, in this order:

| Patch | SHA-256 |
|---|---|
| `ps5-iw620.patch` | `ce5e7f72c15785b18948761474735ec26d80458d9e6dc39b207bf0ad31688f3a` |
| `ps5-iw620-cmd-timeout-recover.patch` | `3cf0a8fe9a15a139c37367c20f3cd5567e44e55d948fc7cb54f62c0c2bec7053` |
| `ps5-iw620-kernel71-compat.patch` | `7c091f69db2725b2fa52d01bb21126fe21c8bf97c9ec9ce87ca3340d29c5017c` |
| `ps5-iw620-rtnl-bounded-wait.patch` | `9b63bdd86301ca65768836dc6f7baa94797e5981d6d572c44f53e0512cc1fe1a` |

Do not apply `ps5-iw620-kernel72-compat.patch` to a 7.1.7 build. Upstream
`install.sh` applies it to every 7.x kernel, but it changes
`woal_cfg80211_remain_on_channel` to take six arguments, while
`cfg80211_ops.remain_on_channel` in 7.1.7 takes five. With the Run 16 compiler
that is a hard `-Wincompatible-pointer-types` error. Its `strncpy` to
`strscpy` conversions also copy one byte less than the length they are given,
which drops the last character of SSIDs in the scheduled-scan and background
scan paths. The other four patches apply cleanly without it.

## Building the modules

The modules must be built against the exact Run 16 kernel tree, not just a
matching version string:

- Linux `v7.1.7` (`c7ba9d6de43e9d9bd755b1f3c19501a38898c6b6`) with
  `ps5-linux-patches` commit `56922cf` `linux.patch` applied with
  `git apply --exclude=Makefile`;
- that commit's `.config`, which after `make olddefconfig` has SHA-256
  `a2444227c03aaedc240be4631bab29922b901a4b80a1a200f991c73b9d88c641`;
- the `ps5-kernel-builder` image from the
  [Ubuntu image branch](https://github.com/gzimbric/ps5-linux-image/tree/ubuntu2404-1160-tested)
  (`x86_64-linux-gnu-gcc (Debian 14.2.0-19) 14.2.0`, GNU ld 2.44);
- `make modules_prepare` in that tree, plus a `Module.symvers` for the shipped
  kernel.

The kernel uses `CONFIG_MODVERSIONS` with `GENDWARFKSYMS` and extended
modversions, and module signing is off. The kernel's module loader therefore
checks the symbol CRCs, not a signature, and refuses a module whose imported
CRCs do not match this kernel. The `Module.symvers` used for Run 17 was
decoded from the shipped Run 16 `bzImage` and its in-tree modules. It matched,
entry for entry, the modpost-generated `Module.symvers` shipped in the official
ps5-linux 7.1.7 image's kernel metadata. A full `make bzImage modules` of the
Run 16 tree was not run for this comparison.

Build with objtool enabled. Upstream `install.sh` passes `CONFIG_OBJTOOL=`,
which leaves the modules without `.return_sites`. This kernel has
`MITIGATION_RETHUNK`, `MITIGATION_UNRET_ENTRY`, and `MITIGATION_SRSO` set, so
from the 7.1.7 source such a module would trigger
`Unpatched return thunk in use` on first use and taint the kernel `W`. That
case was not tested on the console. Inside the builder, with the prepared tree
at `/src`:

```sh
cd nxp-mwifiex
make -C "$PWD" KERNELDIR=/src ARCH=x86 -j12
x86_64-linux-gnu-strip --strip-debug mlan.ko moal.ko
```

The build reported no compiler, objtool, or modpost warnings. The stripped
modules from Run 17 were:

| Module | Size | SHA-256 |
|---|---:|---|
| `mlan.ko` | 1,491,280 | `e6f8e649974767f26d9bd8c60b3b49e1203d5282700493864b7e6fd7be482b23` |
| `moal.ko` | 2,112,848 | `3e00f26af4d71d6f459a56a1b99c435dcacb09d3ead28e0e722898a68a6347ed` |

A second build from separate clones of the same sources was byte-identical.
Both modules report version `542.p8` and vermagic
`7.1.7 SMP preempt mod_unload modversions`.

## Firmware

The driver loads `nxp/pcieuartiw620_combo_v1.bin`. It is Sony/NXP firmware and
is not published here. On 11.60 it sits in kernel data at these locations:

| Item | Value |
|---|---|
| Kernel-text-relative offset | `0x1585D90` |
| Size | `0x799BC` (498,108 bytes) |
| Offset in a kernel-data dump | `0x855D90` (kernel text starts `0xD30000` before kernel data) |
| SHA-256 | `eafef24af118f96f84a652e17aeed555ec4ac719b9fac11ff98a2de7e2b4b369` |
| Embedded version | `17.130.3.p47` |

The 11.60 helper at kernel-text offset `0x4ECFD0` returns exactly this pointer
and length, and the first 64 bytes of the blob occur only at that offset in
the dump. The upstream loader can write the blob to `lib/nxp/` on the FAT
partition when its offset table has an entry for the running firmware. A
loader build with the 11.60 entry exists, but its dump path has not run on
hardware, so it is not published. Run 17 copied a blob carved from this
console's own kernel-data dump.

## Loading

Copy `mlan.ko`, `moal.ko`, and `pcieuartiw620_combo_v1.bin` into one directory
on the console, together with [`tools/iw620_load.sh`](../tools/iw620_load.sh).
The script checks the files against the hashes above, installs the firmware,
and loads the driver once. Run 17 used a shorter version of this script with
the same file checks and options; the kernel-version and vermagic checks added
here have not run on the console. The options are:

```text
fw_name=nxp/pcieuartiw620_combo_v1.bin pcie_int_mode=1 drv_mode=1
cfg80211_wext=4 sta_name=mlan ext_scan=1 auto_fw_reload=0 wifi_reset_config=0
sched_scan=0 ps_mode=2 auto_ds=2 amsdu_disable=1 drvdbg=0x7
```

These match the options in upstream `install.sh` and `test-iw620.sh`.
`pcie_int_mode=1` selects MSI; the PS5 kernel patch disables legacy INTx on
this bus, and upstream issue #3 reports that `pcie_int_mode=0` fails probe.
`ps_mode=2` and `auto_ds=2` keep the chip out of power save, which upstream
issue #3 reports drops the link within seconds.

```sh
sudo ./iw620_load.sh
```

The script does not change anything that runs at boot. The interface comes up
as `wlp64s0f7` and is managed by NetworkManager, so a network can be joined
from the GNOME Wi-Fi menu. In Run 17 the wired default route kept its lower
metric, so SSH stayed on Ethernet.

## Loading at every boot

Once a network has connected, run
[`tools/iw620_persist.sh`](../tools/iw620_persist.sh). It installs the modules
under `/lib/modules/7.1.7/updates/ps5-iw620`, writes the same options to
`/etc/modprobe.d/ps5-iw620.conf`, adds `moal` to `modules-load.d`, and clears
the image's blacklist.

```sh
sudo ./iw620_persist.sh
```

The blacklist file is overwritten with a single comment line rather than
deleted, because the image's initramfs hook copies it and fails if it is
missing. The original is saved as `/etc/ps5-iw620-noautoload.conf.orig`. The
initramfs, EFI files, and loader are not modified.

Run 17 made the same changes with an earlier version of this script and
checked them with `modprobe --show-depends moal`, but did not reboot
afterwards, so loading at boot has not been observed.

## Known limits

- Upstream issue [#3](https://github.com/ps5-linux/ps5-linux-mwifiex/issues/3)
  reports that the firmware can stop servicing both DMA rings under heavy
  concurrent traffic. Neither a firmware reset nor a driver reload recovers
  it; only a reboot does.
- Unload the driver before a warm reboot through `kexec.sh`
  (`sudo modprobe -r moal mlan`). With `moal` loaded, its PCI shutdown hook
  starts an in-band chip reset. `ps5-linux-tools` pull request
  [#3](https://github.com/ps5-linux/ps5-linux-tools/pull/3) unloads the driver
  first for the same reason.
- Do not use PCI function-level reset, `auto_fw_reload`, or PCI remove and
  rescan. Upstream reports that each one leaves the device unusable until
  reboot.
- Firmware versions other than p47, and console firmware other than 11.60,
  were not tested.
