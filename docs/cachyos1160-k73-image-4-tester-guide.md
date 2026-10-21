# CachyOS Image 4 tester guide for PS5 firmware 11.60

> **Image 4 is a public tester prerelease, not a hardware-validated release.**
> CI built and structurally verified the exact unified image linked below, but
> it has not been booted on a PS5. MediaTek Wi-Fi is still experimental and
> MediaTek Bluetooth is unknown. Do not report Image 3 results as Image 4
> results. [Image 3](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-3)
> remains the latest download with an identity-verified hardware boot.

## Scope and current evidence

Image 4 is a single image for both PS5 Wi-Fi variants. It does not need a
separate MediaTek edition.

| Area | Image 4 status before its first hardware run |
|---|---|
| Kernel package | `linux-ps5 7.3.0-4` in current source |
| Exact unified artifact | Hosted CI build and structural verifier passed; public tester prerelease exists; no hardware boot recorded |
| Marvell IW620 Wi-Fi | Existing exact-ID-gated path retained; Image 3 proved the older artifact, not Image 4 |
| MediaTek MT7921 Wi-Fi | In-tree `mt7921e`, packaged firmware and `disable_aspm=1` path structurally validated; not hardware-tested on firmware 11.60 |
| IW620 Bluetooth | The known Image 3 path is retained, but the new artifact still needs regression testing |
| MediaTek Bluetooth | Hardware identity and working driver path are unknown; no support claim yet |

Passing a source check, kernel build or image verifier is not a console boot.
The first Image 4 report must identify the exact downloadable artifact and the
chipset path used.

## Exact artifact identity

Do not test a file described only as "latest" or "Image 4." Use this exact
release and record it with every result:

| Item | Required value |
|---|---|
| Release tag and URL | [`cachyos1160-k73-image-4`](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-4) |
| Source commit | `e82cefaac9f4c166b4b961ea64597bb5a2a1d1e3` on `main` |
| Successful workflow run | [`39536824124`](https://github.com/gzimbric/ps5-linux-image/actions/runs/39536824124) |
| Archive filename, byte size and SHA-256 | `ps5-cachyos1160-k73.img.xz`; 1,942,499,200 bytes; `bc83fc06b78c4b1f34498fc4f9657bcf84483ee5c3268e48047ad844dd8b7380` |
| Expanded raw-image byte size and SHA-256 | 12,582,912,000 bytes; `b8346c5d8c34e643926f7c6a5d58c0017b0de8b18f944dcf7869a31759e971d5` |
| `bzImage` byte size and SHA-256 | 11,613,184 bytes; `19293156bfabdb1d347991dafdbe5eb927828d7cb7d3453cac2b3389d2bfeb8b` |
| `initrd.img` byte size and SHA-256 | 51,902,154 bytes; `03f4fce8d79178922fbd03ed02cb9ce220f5db58b19435b68567236f694ddef9` |
| `cmdline.txt` byte size and SHA-256 | 118 bytes; `aec7a85e9ebcf36e4bdaeb89242b898e17817acd40c16db57a3bb9c3117b1da8` |
| `vram.txt` byte size and SHA-256 | 11 bytes; `bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0` |
| `kexec.sh` byte size and SHA-256 | 136 bytes; `0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52` |
| Root-change manifest | `cachyos1160-k73-root-changes.txt`; 7,704 bytes; `3e3efd4d3510b250aabc167a2e1fb49e50db4ec4023d5ec0563260193f67f380` |
| `SHA256SUMS` SHA-256 | `95a0e050f7a69e5bcdff8bc26babcd7f5e8eda33e70cb7b0e4b04c78ab3114a2` |

The release contains one `.img.xz`, not numbered pieces. GitHub's recorded
digest for that asset matches the archive line in `SHA256SUMS`. Verify
`SHA256SUMS` before flashing, then verify the archive and expanded image
against that same release. Keep the downloaded archive until the flashed-drive
readback has been recorded.

## Choose the loader by Wi-Fi chipset

Both loader files come from the
[`firmware-11.60-dma-e820-bounded-run21` prerelease](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21).
They are not interchangeable for a chipset-specific test.

| Console Wi-Fi hardware | Loader | SHA-256 | Reason |
|---|---|---|---|
| Marvell/NXP IW620, PCI `1b4b:2b56` | `ps5-linux-loader-1160-dma-e820-bounded-wifi.elf` | `e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f` | Copies that console's own IW620 firmware to the USB before Linux probes the device |
| MediaTek MT7921, known PS5 PCI ID `14c3:7961` | `ps5-linux-loader-1160-dma-e820-bounded.elf` | `1c80b040c5a808b3f09418728424a875d5598fe6b2a5d68adeb4db5979a7541a` | Does not dump IW620 firmware; Image 4 packages the firmware used by `mt7921e` |

The bounded Wi-Fi loader has already booted the IW620 console path. The
bounded non-Wi-Fi loader has not been booted on hardware, so the first
MediaTek run also tests that loader path. If the chipset is not already known
from an earlier Linux boot, do not guess and do not label the result as an
IW620 or MediaTek pass.

Use a freshly flashed Image 4 drive for each chipset track. An IW620 firmware
file left on the FAT partition by an earlier bounded-Wi-Fi run invalidates a
claim that the MediaTek test started with only packaged firmware. Never share
or upload `pcieuartiw620_combo_v1.bin`.

## Requirements

- Regular retail PS5 on firmware 11.60, not PS5 Pro.
- Automatic system-software updates disabled.
- The 11.60 exploit with the ELF listener on TCP port 9021.
- The reviewed Image 4 archive and checksum files linked above.
- The loader selected from the chipset table above and verified locally.
- USB drive of at least 16 GB. Flashing erases the selected drive.
- HDMI and a wired USB keyboard.
- Ethernet available for recovery and SSH even when testing Wi-Fi.
- Only one Linux USB drive attached to the console.

The expected initial account is `steam` / `steam` with passwordless `sudo`.
Keep the console on a trusted network and change the password after the
baseline test.

## Flash and first boot

Use the verification commands printed in the release notes. At minimum, check
the manifest and archive in the same directory:

```sh
shasum -a 256 -c --ignore-missing SHA256SUMS
```

After flashing, read the entire target drive back and hash it before changing
the filesystem. The readback must match the release's expanded-image SHA-256.
Record the target drive size and USB port as well.

Start from a full PS5 power-off. Send the selected loader once, let GameOS
enter Rest Mode, wait for solid orange, then wake once with the controller.
Record the loader's complete on-screen report or a clear photo. For IW620, the
report should include the bounded firmware dump. For MediaTek, the run must use
the non-Wi-Fi loader and must not be credited with an IW620 firmware dump.

Do not use Linux suspend, hibernate or GameOS Rest Mode after Linux has
started. Use a full Linux power-off between attempts.

## Capture the common baseline

Before updating packages or applying a workaround, save this output:

```sh
date -u
uname -a
pacman -Q linux-ps5
cat /proc/cmdline
sudo lspci -nnk
lsusb
sha256sum /boot/efi/bzImage /boot/efi/initrd.img \
  /boot/efi/cmdline.txt /boot/efi/vram.txt /boot/efi/kexec.sh
cat /home/steam/.config/ps5-next-session
systemctl --failed --no-pager
systemctl is-enabled ps5fan.service ps5-performance.service \
  ps5-iw620-firmware.service ps5-bt-quiet.service
systemctl is-enabled systemd-networkd-wait-online.service
systemctl is-enabled sleep.target suspend.target hibernate.target \
  hybrid-sleep.target suspend-then-hibernate.target
systemctl status NetworkManager.service sshd.service --no-pager --full
sudo /usr/local/sbin/ps5-boot-report
```

The package must report `linux-ps5 7.3.0-4`. Record the time from wake to white
light, HDMI, Plasma, DHCP and SSH. A white light alone is not a complete boot
result.

The Image 4 source is intended to start in Plasma, keep all unsupported
sleep targets masked, prevent the unused networkd wait-online unit from
delaying boot, include the narrow NetworkManager PolicyKit rule, and apply a
65 C fan target before the clock policy. Verify those behaviors on the exact
artifact rather than assuming source intent reached the image.

## IW620 track

Use only the bounded Wi-Fi loader for this track. Capture:

```sh
sudo lspci -nnk -d 1b4b:2b56
lsusb -d 1286:2059
systemctl status ps5-iw620-firmware.service --no-pager --full
lsmod | grep -E '^(mlan|moal|mt7921e|mt7921_common|mt76)'
sudo dmesg | grep -Ei 'mlan|moal|PCIEIW620|WLAN FW is active|firmware|mt7921|mt76'
nmcli device status
```

Expected device gating is `mlan`/`moal` on PCI `1b4b:2b56`, with no
`mt7921e` bind. Do not post the firmware file, its contents, a FAT-partition
image or an unredacted boot report.

Join Wi-Fi once through the normal Plasma menu. Record whether association,
DHCP and traffic bound to the Wi-Fi interface work. If the menu fails, save
NetworkManager's journal before trying `nmcli`:

```sh
journalctl -b -u NetworkManager --no-pager
WIFI_IFACE="$(LC_ALL=C nmcli -t -f DEVICE,TYPE device status |
  awk -F: '$2 == "wifi" { print $1; exit }')"
test -n "$WIFI_IFACE" || { echo "No Wi-Fi interface found" >&2; exit 1; }
ping -c 3 -I "$WIFI_IFACE" 1.1.1.1
```

Image 3's successful IW620 result is useful regression context, but it does
not make the new `7.3.0-4` artifact a pass.

## MediaTek MT7921 track

Use only the bounded non-Wi-Fi loader on a fresh Image 4 flash for this track.
Capture the exact PCI ID and driver state:

```sh
sudo lspci -nnk -d 14c3:
cat /etc/modprobe.d/ps5-mt7921e.conf
modinfo -F parm mt7921e
modinfo -F alias mt7921e
modinfo -F firmware mt7921e
lsmod | grep -E '^(mt7921e|mt7921_common|mt792x_lib|mt76|mlan|moal)'
systemctl status ps5-iw620-firmware.service --no-pager --full
sudo dmesg | grep -Ei 'mt7921|mt76|firmware|ASPM|mlan|moal'
nmcli device status
```

The configuration should contain:

```text
options mt7921e disable_aspm=1
```

For the known `14c3:7961` device, `lspci -nnk` should show `mt7921e` as the
kernel driver in use. The driver must be selected by PCI modalias rather than
force-loaded. `mlan` and `moal` should not bind, and the exact-ID-gated IW620
firmware service should not run its copy/load path.

Save the first probe's complete kernel log before reloading a module or
changing a parameter. Then test the normal Plasma Wi-Fi menu and record scan,
association, DHCP and traffic bound to that interface using the same commands
as the IW620 track. A working scan without association is not a Wi-Fi pass.

The known MediaTek PCI ID is not proof that every packaged `mt7921e` alias is
PS5 hardware. Report the ID actually observed.

## Bluetooth and DualSense

Do not attach an external Bluetooth adapter. Before pairing, capture:

```sh
bluetoothctl list
sudo btmgmt info
lsusb
lsmod | grep -E '^(btusb|bluetooth|uhid|hid_playstation|btmtk)'
for module in btusb uhid hid_playstation; do modinfo -F vermagic "$module"; done
sudo dmesg | grep -Ei 'Bluetooth|btusb|btmtk|hci[0-9]|opcode|xhci|usb.*disconnect|error -[0-9]+'
```

For IW620, test discovery, pairing, reconnect and controller input as a
regression against Image 3. For MediaTek, treat every result as discovery:
MediaTek Bluetooth hardware identity and its usable driver/firmware path are
unknown. Do not describe it as supported merely because MediaTek Wi-Fi works.
Record the USB or PCI identity, bound modules, HCI state, pairing result and
whether `hid-playstation` exposes gamepad, motion and touchpad devices.

Linux pairing may replace the GameOS bond. Connect the controller by USB and
press PS in GameOS to pair it there again if necessary.

## Common regression checks

For each chipset track, test these separately and report the result rather
than folding them into a single "boots" answer:

1. Visible HDMI and authenticated wired SSH.
2. Plasma first, GUI network control without an authentication prompt, and no
   failed `systemd-networkd-wait-online` unit.
3. Plasma to Gaming Mode after Steam's first online bootstrap.
4. **Switch to Desktop** once, allowing time for Gamescope to exit and Plasma
   to start. Do not click repeatedly.
5. DualSense discovery, pairing, input and reconnect through the internal
   Bluetooth controller.
6. Startup fan-target readback, GPU and CPU frequency policy.
7. Clean `sudo poweroff` with unsupported sleep targets still masked.

The wait-online unit should report `masked`. After returning from Gaming Mode
to Plasma, verify that the desktop can rescan without `sudo` or a PolicyKit
password prompt:

```sh
systemctl is-enabled systemd-networkd-wait-online.service
WIFI_IFACE="$(LC_ALL=C nmcli -t -f DEVICE,TYPE device status |
  awk -F: '$2 == "wifi" { print $1; exit }')"
test -n "$WIFI_IFACE" || { echo "No Wi-Fi interface found" >&2; exit 1; }
nmcli --wait 15 device wifi rescan ifname "$WIFI_IFACE"
```

Capture the policy state before a load test:

```sh
cat /sys/bus/platform/devices/ps5-fan/target_temp
cat /sys/module/amdgpu/parameters/dpm
lsmod | grep -E '^(ps5_cpufreq|ps5_gpufreq)'
cat /sys/class/devfreq/ps5-gpufreq/governor
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
cat /sys/devices/system/cpu/cpufreq/boost
sensors
```

The intended state is fan target `65`, GPU `simple_ondemand`, CPU `schedutil`
and CPU boost `0`. Linux exposes no fan RPM or tachometer reading on the tested
hardware. Do not begin a long stress test during the first bring-up.

If a session handoff, network join or pairing attempt fails, save the relevant
journal before applying any workaround. A recovery can be useful, but it does
not turn the original automatic path into a pass.

## First reports needed

The first useful Image 4 reports are:

1. One exact-artifact cold boot on known IW620 hardware using the bounded
   Wi-Fi loader, followed by Wi-Fi and IW620 Bluetooth regression checks.
2. One exact-artifact cold boot on known `14c3:7961` hardware using the
   bounded non-Wi-Fi loader, followed by a complete first-probe Wi-Fi log.
3. A separate MediaTek Bluetooth inventory and pairing attempt, reported as
   unknown/experimental until the hardware and driver path are established.
4. Two to four additional cold boots per hardware path, then cold reconnect
   and a Wi-Fi/Bluetooth coexistence soak only after the baseline is stable.

Each report should include the release tag, source commit, workflow, archive
and raw-image hashes, loader filename and hash, PS5 model and firmware, exact
PCI/USB IDs, USB port, attempt number, timing to each startup milestone,
driver/module state, GUI Wi-Fi result, Bluetooth result, session-switch result,
fan/clock readback, failed units and every change made after baseline.

Before sharing logs, remove IP addresses, MAC addresses, SSIDs, BSSIDs, serial
numbers, UUIDs, personal usernames and local paths. Do not upload console
firmware, keys, private dumps or partition images.
