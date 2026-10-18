# 11.60 maintenance backlog

This page tracks follow-up work after the first successful Run 15 HDMI boot and
the Run 16 Ubuntu control. Keep the working boot chain unchanged while testing
kernel fixes. A source-level defect is not evidence that it caused an earlier
failed boot.

## Run 15 CachyOS loader baseline

| File | Size | SHA-256 |
|---|---:|---|
| Loader ELF | 169,872 | `422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336` |
| `bzImage` | 12,702,720 | `11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde` |
| `initrd.img` | 54,376,639 | `c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f` |
| `cmdline.txt` | 118 | `aec7a85e9ebcf36e4bdaeb89242b898e17817acd40c16db57a3bb9c3117b1da8` |

The loader is built from the
[`firmware-11.60-sonic-display`](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display)
branch. Commit `e0b7a2e` contains the tested Run 15 source, and commit `69657e6`
adds the reproducible release check without changing the resulting ELF.

Run 15 is one successful complete display run. It is not yet a
repeatability or multi-monitor result. Commands 21 and 22 and the 29-entry
display table were present in the working path, but their individual returns
were not recorded.

The matching initramfs can be rebuilt with the
[tested 11.60 recipe](initrd-recipe.md). Issue #1 remains open until someone
else confirms the result on hardware.

## Run 16 Ubuntu control

Run 16 kept the exact Run 15 loader and kernel but booted Ubuntu 24.04.5 from a
separate image. It reached authenticated wired SSH and a directly observed
GDM/GNOME Wayland desktop. This establishes a second working distribution on
the same console without changing the loader.

| File | Size | SHA-256 |
|---|---:|---|
| Loader ELF | 169,872 | `422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336` |
| `bzImage` | 12,702,720 | `11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde` |
| Ubuntu EFI `initrd.img` | 54,376,639 | `2eef0352879e091083450b799c75514a450f4110cbc747f640962fdde2dc06c8` |
| Ubuntu `cmdline.txt` | 121 | `6b3c09112fe049d3cbeada65fb3c82bb0f5fcaddce6c0709051df3d9f5a79f6d` |

The Ubuntu EFI initrd is a 50,803,483-byte Ubuntu initramfs followed by
3,573,156 zero bytes. Matching the Run 15 size satisfies the current loader
gate, but the content and hash differ from the CachyOS initrd. Do not use Run
16 as confirmation of the exact Issue #1 recipe.

## Next controlled test: fan detection

Run 16 logged:

```text
FanServo: B-Eiger/Denali Unknown Vendor/Revision 0x6/0xb0
FanServo: Not update
```

The pinned 7.1.7 patch set predates
[`7f695e4`](https://github.com/ps5-linux/ps5-linux-patches/commit/7f695e4b99509667bdf1059c2e1df8e059eaf2a5),
which masks the decoded GDDR6 revision to its low nibble. For this hardware,
that should turn revision `0xb0` into revision `0` and select the existing
B-Eiger/Denali Hynix servo table.

Backport only the fan-detection hunk for the first test. Keep the maximum-fan
service enabled as a fallback until a clean boot identifies the vendor and
revision, omits `FanServo: Not update`, and exposes a working
`/sys/bus/platform/devices/ps5-fan/target_temp` read/write path. The current
service proves that the maximum-setting ioctl returned successfully; there is
no fan RPM readback, so it does not prove the physical curve response.

## Second controlled test: MTS Ethernet

The image builder pins `ps5-linux-patches` commit
`56922cf9af91142cdcf7d54cbcfb3d46bdfb397a`. The later MTS fix in
`9322b9d478e46101670b4ff21858a8cfd9c93c76` applies cleanly on that exact
7.1.7 base. Run 15 used the older driver; its kernel log contains the old
`rx_mode: flags=` message removed by the fix.

The patch corrects interrupt-mask polarity, implements multicast filtering,
increases the RX ring, improves RX/IRQ recovery, and changes NAPI shutdown
ordering. Run 15 already had working IPv4 and SSH, so this is driver hardening,
not a fix for a failure observed in that run.

Build the full kernel with the same 7.1.7 tree, configuration, builder
toolchain, and generated `Module.symvers` so module versions and BTF data
match. For the first test, extract and replace only `mts.ko` or `mts.ko.zst`
on the root filesystem. Do not install the whole kernel package: its
post-install step replaces `bzImage` and regenerates the initramfs, which would
change more than one variable and fail the current loader's exact-size checks.
The tested initramfs does not contain the MTS module, so it does not need to be
rebuilt for this test.

Before rebooting:

1. Find the active file with `modinfo -n mts` and keep a local backup.
2. Compare the old and new `vermagic` values as a sanity check; matching them
   does not replace the exact-tree and `Module.symvers` requirement.
3. Replace the module atomically and run `depmod -a 7.1.7`.
4. Leave the loader, `bzImage`, initramfs, and command line unchanged.
5. Do not unload the driver over the only SSH connection.
6. Have the old module ready to restore from local display or offline Linux
   before rebooting.

The test should cover IPv4 DHCP and SSH, IPv6 neighbor discovery, forward and
reverse `iperf3`, interrupt and packet-error counters, and one interface
down/up cycle. Rollback is the original module followed by `depmod` and a cold
boot.

## Kernel work

These findings are confirmed in the source but have not been reproduced on the
11.60 console.

### Wireless hardware and driver target

Run 16 identified PCI wireless function `1b4b:2b56` and USB Bluetooth/WLAN
companion `1286:2059`. This is Marvell hardware, not MediaTek MT7921 hardware.
The pairing is consistent with the
[PS5 IW620 mwifiex path](https://github.com/ps5-linux/ps5-linux-mwifiex).
The linked mt76/MT7921 driver does not contain these IDs and cannot bind this
hardware.

The current 7.1.7 installation exposed no module alias for the PCI function and
created no WLAN interface. Continue wireless investigation in the `mwifiex`
and IW620 path; do not add an MT7921 driver to this image as a test for this
console.

The 11.60 loader also lacks the Wi-Fi firmware offset and size. The available
11.60 kernel-text capture ends at `0xD30000`, before the range containing the
known firmware blobs on supported versions. Capture at least `0x1800000` bytes,
preferably `0x2000000`, from a fresh authenticated GameOS session before
attempting to identify the 11.60 blob. Do not guess or reuse the 13.60 offset.

### Salina xHCI event handling

The PS5 event loop marks the Salina controller `DYING` after the 33rd valid
event processed in one poll pass. Later URBs fail until the controller is
restarted or rebound. This affects the Salina controller, not the separate AMD
xHCI controller used by the root drive.

Replace the fixed self-kill path with bounded rescheduling, then test a backlog
of more than 32 valid events and sustained traffic on Salina-connected devices.

### ICC mailbox

The mailbox accepts replies without matching request ID, service, and type. It
also trusts message lengths too early. During shutdown, the PCI callback masks
the ICC interrupt before the later platform power request, while the emergency
restart path uses a blocking mutex and waitqueue despite its atomic-safe
contract.

Add bounded header parsing and reply matching first. Clean shutdown and
emergency restart need separate implementations: the emergency path must not
sleep or depend on a mutex held by another CPU. Test malformed lengths, a late
reply after timeout, clean reboot and poweroff, and only then panic restart.

The configured query timeout is 12 seconds. The actual failure mode may be a
delay, repeated delays, or a hang; none has been established on this console.

### HDMI hotplug and EDID ownership

The PS5 path skips normal DRM hotplug setup. HDMI notifications replace a
global EDID without sufficient bounds checks, ownership, synchronization, or a
DRM hotplug event. HDMI transaction errors are also discarded. This can affect
display-off-at-boot, receiver, input-switch, cable-reconnect, and monitor-swap
cases, but it does not explain the earlier black-screen runs by itself.

Fix EDID validation and ownership before adding a process-context DRM hotplug
path. Propagate the first failed HDMI transaction instead of continuing through
the rest of a sequence. Test cold boot first, then display-off boot, cable
reconnect, input switching, receiver chains, and a monitor swap.

### Crash capture

The current kernel has DRM panic and netconsole support, but no pstore and no
build-specific local version. Add persistent or network capture before taking
larger driver risks, and record the exact kernel build in every report.

### SSH access

The CachyOS image source enables password login, ships an initial `steam`
password, and grants passwordless sudo to `wheel`. Check the live system rather
than assuming those defaults are still active. Confirm key-based login, change
the password, disable password and keyboard-interactive authentication, and
keep a tested local recovery path before closing the current SSH session.

## Deferred

- The HDMI link-training fix in `fe852d3` is already an ancestor of the pinned
  7.1.7 patch set, and Run 16 produced visible output. The later VCN work is
  media acceleration on a newer kernel base, not a display-output fix.
- Do not wholesale backport `0d2ed27`: it disables the Salina initialization
  path that currently enumerates the internal Marvell device. The separate AMD
  xHCI path already boots the USB root drive.
- Upstream loader commit `8cda4c1` patches the 13.60 e820 map so only 1 MiB
  through 16 MiB remains usable below 1 GiB, while 16 MiB through 1 GiB is
  reserved. A matching 11.60
  A/B should remain a separate loader-only experiment: it costs about 1008 MiB
  of usable RAM and is not needed for display.
- The 11.60 loader does not reserve TMR ranges in e820, but the reference
  artifact behaves the same way and no corruption has been observed. Capture
  the live e820 and TMR state before changing the map.
- The loader currently identifies the tested kernel and initramfs by exact
  size. Add setup-header and content-manifest validation in a separate loader
  experiment; do not change the Run 15 release ELF.
- Keep the existing `break_hv` error path unchanged. Adding a halt there can
  deadlock the all-CPU rendezvous.

## Evidence limits

Do not claim that an individual MP3 command or display-table entry was tested
separately, that the USB, ICC, or HDMI findings caused an observed failure, or
that missing TMR reservations caused memory corruption. The current evidence
also does not support an HV-entry address truncation, an initramfs identity-map
overrun, a page-install overflow on the tested path, or a fan left disabled for
the next kernel.
