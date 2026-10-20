# 11.60 maintenance backlog

This page tracks follow-up work after the first successful Run 15 HDMI boot,
the Run 16 Ubuntu control, the Run 17 Wi-Fi bring-up, the Run 18 DMA E820
boot, the Run 19 CI Ubuntu boot, and the Run 21 CachyOS 7.3.0 boot. Keep the
working boot chain unchanged while testing kernel fixes. A source-level defect
is not evidence that it caused an earlier failed boot.

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
[tested Run 15 CachyOS recipe](initrd-recipe.md). Issue #1 remains open until
someone else confirms the result on hardware.

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

This was a custom Ubuntu 24.04 build rather than the stock upstream image. The
[Run 16 Ubuntu USB guide](ubuntu2404-run16-usb.md) records its source revision,
partition layout, exact boot files, and read-only comparison procedure.

## Run 17 Wi-Fi

Run 17 brought up the IW620 (`1b4b:2b56`) with NXP `mlan`/`moal` built for the
exact Run 16 kernel and the console's 11.60 firmware. It scanned, joined a 5
GHz network, and carried an HTTPS download. The steps are in the
[Wi-Fi guide](ubuntu2404-wifi.md) and the result in the
[Run 17 evidence](../evidence/11.60-ubuntu-run-17-wifi.md).

| File | Size | SHA-256 |
|---|---:|---|
| `mlan.ko` | 1,491,280 | `e6f8e649974767f26d9bd8c60b3b49e1203d5282700493864b7e6fd7be482b23` |
| `moal.ko` | 2,112,848 | `3e00f26af4d71d6f459a56a1b99c435dcacb09d3ead28e0e722898a68a6347ed` |
| `pcieuartiw620_combo_v1.bin` | 498,108 | `eafef24af118f96f84a652e17aeed555ec4ac719b9fac11ff98a2de7e2b4b369` |

Next tests, one at a time:

1. Cold boot with autoload enabled and confirm that the driver loads and the
   saved network reconnects without SSH steps. On the 7.3 image in Run 21 the
   driver did come up at boot through the image's firmware service, after one
   failed probe, but the network was joined by hand. This Ubuntu setup has
   still not been seen across a reboot.
2. Run a soak of at least 30 minutes with mixed traffic, then unload and
   reload the driver once. The reload should report the firmware as already
   running.
3. Boot the loader build that adds only the 11.60 firmware offset
   (`0x1585D90`, `0x799BC`) to the Run 15 source. It differs from the Run 15
   ELF only in the build ID and those two fields. Check that the blob written
   to `lib/nxp/` on the FAT partition has the hash above. Partly done in Run
   21: the bounded Wi-Fi build, which sets the same two fields on top of the
   DMA map and the bounded boot-file checks, wrote a blob with exactly that
   hash. The build with only the offset change has not been booted, and no
   loader that copies the firmware has been booted with an Ubuntu image.
4. Build the modules in the Ubuntu image branch and stage the firmware from the
   FAT partition, so a new image has working Wi-Fi without manual steps. This
   changes the hash-gated kernel package, so it needs a full rebuild and boot.

## Run 18 DMA E820 build

Run 18 booted CachyOS with the opt-in DMA E820 loader build. It reserves
`[0x01000000, 0x40000000)` as upstream's 13.60 support does (upstream commit
`8cda4c1`), and Linux reported exactly that range as reserved. A 12 GiB write
and read-back check on the USB root matched. The result and its limits are in
the [Run 18 evidence](../evidence/11.60-cachyos-run-18-dma-e820.md).

| File | Size | SHA-256 |
|---|---:|---|
| DMA E820 loader ELF | 169,872 | `2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0` |

The build is opt-in for testers. Run 15 remains the release baseline. The
read/write errors reported by testers have not been reproduced on this
console, so Run 18 does not show that the reservation fixes them.

Next tests, one at a time:

1. Done in Run 19: the CI-built Ubuntu 24.04 image (build 3) booted with this
   ELF, using the [tester guide](ubuntu2404-tester-guide.md). The picture was
   directly observed, SSH worked, the e820 line was present, and the guide's
   I/O check passed. See the
   [Run 19 evidence](../evidence/11.60-ubuntu-ci-run-19.md).
2. Run the same write and read-back check with the Run 15 ELF on the same
   USB, as the A/B control that Runs 18, 19, and 21 did not have.
3. Get the exact error text from testers who saw read/write errors, and ask
   them to repeat their workload with this ELF.

## Run 19 CI Ubuntu image

Run 19 booted CI Ubuntu build 3 (`ubuntu2404-1160-build-3`, built from
`ps5-linux-image` commit `ec8cd4e`) with the DMA E820 ELF. Two image defects
were found. Neither blocked the boot or SSH. Both belong to the Ubuntu image
profile, not the loader, so fixing them needs a new CI build and a new boot.

1. Hostname. `/etc/hostname` in the image holds the 12-character ID of the CI
   build container, and Run 19 booted with that hostname. The Run 16 image also
   had a container-ID hostname, so this is a profile issue and not new to CI.
   Set the hostname in the profile instead of keeping the build container's,
   and check `/etc/hostname` in the next built image.
2. SSH host-key ordering cycle. At boot systemd logged
   `basic.target: Found ordering cycle on sockets.target/start` involving
   `ssh.socket` and `ps5-ssh-host-keys.service`, and deleted the
   `sockets.target` job to break the cycle. SSH still worked. This was not
   seen in Run 16. Fix the ordering of `ps5-ssh-host-keys.service` in the
   profile, then check that a fresh boot logs no ordering cycle, still creates
   the host keys, and starts SSH.

The other warnings seen in Run 19 are listed in the evidence.

## Run 21 CachyOS 7.3.0

Run 21 booted a local build of the CachyOS 7.3 image (`ps5-linux-image`
branch `cachyos-1160-k73`) with the bounded Wi-Fi loader build from
`gzimbric/ps5-linux-loader` commit `98925a2`. The kernel is Linux v7.3 with
the 7.3 port of the PS5 patches and the CPU and GPU frequency drivers by rmux
(Armandas Kvietkus), from
[rmuxnet/ps5-linux-patches-1](https://github.com/rmuxnet/ps5-linux-patches-1)
at `36f173f`. The picture, SSH, the DMA map, and onboard Wi-Fi with the
loader's firmware copy all worked. The result and its limits are in the
[Run 21 evidence](../evidence/11.60-cachyos-k73-run-21.md).

| File | Size | SHA-256 |
|---|---:|---|
| Bounded Wi-Fi loader ELF | 170,904 | `e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f` |
| `bzImage` (Linux 7.3.0) | 11,613,184 | `db8617da59ffe196fd2e6f9ef5a1a3872f77eaca7189858a395c91112b6629a7` |
| `initrd.img` | 51,900,862 | `56a8a0b91cfa46d4f666aba89055ec6621b3c86708c7b0c28ccf09ac23aa9bbc` |

CI build 1 of the branch (tag `cachyos1160-k73-image-1`) includes the review
fixes made after the local build. Its workflow completed successfully and
created a draft release after Run 21, but that image has not been booted and
is superseded by image 2.

Image 2 is the public tester prerelease tagged `cachyos1160-k73-image-2` at commit
`346088a48f66eb956dafdec9de5085e73b2d44a5`. Workflow run `39481460775`
completed successfully. The prerelease's one image archive is
`ps5-cachyos1160-k73.img.xz`, 1,943,471,712 bytes, SHA-256
`8b785243f79a32a4155cc1e39bed01d580e25ca514e88abbfed1a8a8157a281a`.
It expands to a 12,582,912,000-byte raw image with SHA-256
`3798c7dba96412c5301eb201d8bf8aa4edd1b2f80a743dfd7b90b2a79222c62d`.
The workflow and assets were checked, but the exact image has not been booted.
It is published as a prerelease for hardware testing, with one `.img.xz`; if
compression reaches 2 GiB, fail rather than splitting the image. Testers must
follow the [image 2 tester guide](cachyos1160-k73-image-2-tester-guide.md).

Included in the image 2 source:

1. Internal Bluetooth follow-up. The build still uses rmux's published 7.3
   patch set at `36f173f` as its base, then applies the separate hash-pinned
   `ps5-btusb-iw620-quirks.patch` (`54d7addb...`). The follow-up restores the
   IW620 quirks-table entry and post-lookup interface checks present in merged
   [ps5-linux patch-set PR #35](https://github.com/ps5-linux/ps5-linux-patches/pull/35)
   but absent from the pinned rmux 7.3 patch, while retaining rmux's 7.3 IW620
   quirk flags. [VivaLaVent's Bazzite Deck v1.0.3](https://github.com/VivaLaVent/ps5-bazzite-deck/releases/tag/v1.0.3)
   independently reports the same core correction with a paired DualSense on
   a CFI-10xx PS5 running firmware 13.60. Its patch is not byte-identical, and
   that result is not an 11.60 hardware test of image 2. The image 2 follow-up
   has build evidence only and still needs the cold-boot checks below.
2. IW620 driver load order. Alias-driven `moal` loading is blacklisted, the
   loader-dumped firmware is copied first, and the service then runs an
   explicit `modprobe moal`. A blacklist does not block that explicit load.
   NetworkManager is not ordered after the helper, so a blocked helper cannot
   delay Ethernet. This fix has not been booted.
3. Package identity. The changed kernel and modules are packaged as
   `linux-ps5 7.3.0-2` with `KBUILD_BUILD_VERSION=2`, rather than being shipped
   under the image 1 identity.
4. Frequency-driver policy. `ps5_cpufreq` and `ps5_gpufreq` stay manual-only.
   Run 21 reached 84.0 °C under load, including 30 five-second samples at or
   above 80 °C, and the drivers have no thermal-cooling integration.
5. Fan policy. `ps5fan.service` is enabled by default and requests tested
   maximum servo pattern `3`. It is a fixed bring-up setting, not a dynamic
   temperature curve, and command acceptance does not provide RPM telemetry.

Still unresolved after the image 2 source changes:

1. Steam desktop switch. Steam's Switch to Desktop hung on its switching
   screen because the image's `steamos-session-select` was not run, so the
   next-session token stayed `gamescope`. Setting it to `plasma` by hand and
   ending the tty1 session started KDE Plasma. Make Steam's switch call the
   image's session switch, then check that Switch to Desktop and the way back
   to Gaming Mode both work from the controller.
2. Wi-Fi join from the KDE menu. Joining from the KDE network menu failed
   twice with NetworkManager saying the access point was not in the scan list,
   while `sudo nmcli --ask device wifi connect <SSID>` joined the same network.
   Find out why the menu's request fails and fix it in the image, then join
   from the menu on a fresh boot.

Steam completed the install. Its content log recorded 53,229,366,208
downloaded bytes, staged-file verification, 347 committed files, and `No
Error`. The watcher collected 480 snapshots over about four hours; free space
moved from 213G to 159G and every snapshot had zero new matching storage-error
lines relative to the watcher's baseline. Its throughput and total counters
are invalid because it read
diskstats I/O-time fields 7 and 11 instead of sector fields 6 and 10. This was
not an independent read-back, hash check, or operator-run Steam integrity
check.

The game logger collected 540 five-second samples, including 88 with
`GameThread`, 76 at 2.23 GHz, and an 84.0 °C peak. It ended while the load was
active, without an operator-confirmed picture or gameplay. Treat it as
telemetry, not a thermal-equilibrium or stability result.

Suspend is not supported on this boot path. Run 21 held a `systemd-inhibit`
lock while testing.

### Bluetooth follow-up

Bluetooth did not work in Run 21 on its Linux 7.3 kernel. `btusb` binds the
USB companion `1286:2059` as `hci0` (interface 0) and `hci1` (interface 2),
and both fail at setup:

```text
hci0: Opcode 0x2031 failed: -22
hci1: Opcode 0x0c03 failed: -110
```

`0x0c03` is HCI Reset and `0x2031` is LE Set Default PHY. `btmgmt` lists no
controllers and `bluetoothctl` reports `No default controller`. Run 19 on
Linux 7.1.7 also logged opcode messages from `hci0` and `hci1`, but Bluetooth
was not tested there.

Image 2 contains a high-confidence kernel follow-up, but it has not been
booted. In the 7.3 fork, the `1286:2059` device entry is below a generic USB
class entry, so the generic match wins with no device flags. The interface
checks also run before the PS5 quirks-table lookup. The follow-up adds a quirks
entry with
`BTUSB_MARVELL`, `BTUSB_IFNUM_0`, `BTUSB_BROKEN_LE_DEFAULT_PHY`,
`BTUSB_BROKEN_READ_LOCAL_NAME`, and `BTUSB_NO_AUTOSUSPEND`, and moves both the
`BTUSB_IFNUM_2` and `BTUSB_IFNUM_0` checks after that lookup. It applies to the
pinned 7.3 source and a matching `btusb.ko` built without warnings. Image 2
carries it as a separate patch with SHA-256 `54d7addb...`, after rmux's base
patch. That is build evidence only, not a hardware result. `ps5-bt-quiet`
remains unchanged so the follow-up is the only Bluetooth variable.

For the image 2 hardware test:

1. Cold boot and require one `hci0`, no `0x2031` or `0x0c03` failures,
   `power/control=on`, successful DualSense pairing, working Wi-Fi alongside
   Bluetooth, and no later USB loss. Run beyond the roughly 51-minute point
   where Run 21 lost the Bluetooth USB device.

## Next controlled test: MTS Ethernet

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

### IW620 driver patches

Two upstream `ps5-linux-mwifiex` problems were found while building the Run 17
modules:

- `install.sh` applies `ps5-iw620-kernel72-compat.patch` to every kernel from
  7.0 on. On 7.1.7 the patched `remain_on_channel` has the wrong signature and
  the build fails.
- `ps5-iw620-kernel71-compat.patch` computes the TDLS discovery-response length
  without the category byte, so the frame is one byte short: the capability's
  high byte is lost and the IEs after it shift by one. There is no memory
  corruption. The frame is only sent when a TDLS peer asks for it, which Run
  17 did not exercise.

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

- The Run 15 loader does not reserve TMR ranges in e820, and the reference
  artifact behaves the same way. The opt-in DMA E820 build now reserves
  `[0x01000000, 0x40000000)` like upstream's 13.60 support, and Runs 18, 19,
  and 21 booted that map. That is not a TMR audit, and it does not show that
  missing reservations caused corruption. Capture the live e820 and TMR state
  before changing the Run 15 map.
- The Run 15 and DMA E820 loaders identify the tested kernel and initramfs by
  exact size. The bounded builds at loader commit `98925a2` replace that with
  checks on the `bzImage` setup header, the initrd format, `vram.txt`, and
  `cmdline.txt`, and Run 21 booted the bounded Wi-Fi build. The files are
  still not checked against a content manifest. The Run 15 release ELF is
  unchanged.
- Keep the existing `break_hv` error path unchanged. Adding a halt there can
  deadlock the all-CPU rendezvous.

## Evidence limits

Do not claim that an individual MP3 command or display-table entry was tested
separately, that the USB, ICC, or HDMI findings caused an observed failure,
that missing TMR reservations caused memory corruption, or that the DMA E820
reservation fixes the read/write errors reported by testers. Run 18 shows
that the DMA E820 build boots, applies the intended map, and passed a short
USB write and read-back check; it is not a visible-display result. Run 19
adds a directly observed picture with the CI Ubuntu image on the same
CFI-1115B; it is not a result for other models. Run 21 shows that a local
build of the CachyOS 7.3 image boots with the bounded Wi-Fi loader on that
console, with a directly observed picture and Wi-Fi from the loader's
firmware copy. It is not a result for either CI image, for Bluetooth, for
video decode, for file integrity, or for gaming stability. Image 2 remains an
unbooted candidate: its CI artifacts are verified, but it has not been tested
on hardware. The later watcher saw no
new matching storage-error lines after its baseline, but its rate and total
counters are invalid and
it did no read-back or hash check. The game logger captured load and an
84.0 °C peak without operator-confirmed gameplay or display, thermal
equilibrium, or a completed stability window. The current evidence also does
not support an HV-entry address
truncation, an initramfs identity-map overrun, a page-install overflow on the
tested path, or a fan left disabled for the next kernel.
