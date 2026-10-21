# Testing CachyOS image 3 on PS5 firmware 11.60

> **Release still pending.** A local image 3 build has booted on one CFI-1115B,
> and hosted CI has produced a separate draft artifact. The Wi-Fi menu fix,
> Plasma-first startup and corrected Steam launcher and return-selector paths
> were added after both images were assembled. Do not publish either older
> artifact as the finished image 3 release. The next hosted build needs a new
> identity and the remaining acceptance tests below.

This guide keeps three things separate:

1. the exact local image that was flashed and tested on October 20;
2. the completed but unpublished hosted-CI artifact; and
3. the newer source that contains the fixes found during that hardware run.

## Current identities

| Item | Status |
|---|---|
| Local hardware-test image | Source `f7d6fbd9d630cddaceb83f3b861869d4453af8ca`; raw image 12,582,912,000 bytes; SHA-256 `5a904e02f6a2908be91054b7b73ebf6f891fece0edc1a88f2f9d60264d7556d4`; not published |
| Local boot files | `bzImage` `945a4f2a03c4771313e466dccfb8272e0345cf7d143516a36a0bc75b2b219d0a`; `initrd.img` `912600c22a203a744d4d44fcd4b5caacd86ea8b0c3ef8202ed9c0ff2ba146dd0` |
| Final live-tested selector | 3,736-byte `steamos-session-select`; SHA-256 `1d099eeacc19bbf575e5a636fc81087a46f72af64390172e437372b493bde1c1`; a live follow-up, not part of either older image above |
| Hosted draft | [Workflow `39510517216`](https://github.com/gzimbric/ps5-linux-image/actions/runs/39510517216), source `1d581dfce5ab89c3bd35a7fdad0514f5575f0723`, completed successfully; draft only and not hardware-tested |
| Hosted draft archive | 1,943,469,912-byte `ps5-cachyos1160-k73.img.xz`; SHA-256 `8cdbe317334ec8f2a53adad7c59d580ddf5711cdda03c15b642de6347fa8a1a9` |
| Hosted draft raw image | 12,582,912,000 bytes; SHA-256 `82088537470f698b01aa198319b205d347de928fbe3acd3c7a49a9a8acf0e314` |
| Finished public release | Not published; a replacement hosted build is required after the current fixes are committed |

The local and hosted raw-image hashes differ, so a local result must not be
reported as a test of the hosted draft. They do share the boot-file identities
above. The hosted draft also predates the Wi-Fi, Plasma-first, Steam launcher
and return-selector fixes, so it is not the release candidate testers should
receive.

The finished release must contain one `.img.xz`, not numbered parts. Hosted CI
owns image assembly, verification, compression and upload. A tester should only
need to download, verify and flash that one archive.

## What the October 20 hardware run proved

The exact local image listed above:

- booted Linux 7.3.0 with a directly observed HDMI picture and authenticated
  wired SSH;
- brought up the loader-supplied IW620 firmware and onboard Wi-Fi;
- paired, bonded, trusted and connected a DualSense through the internal
  Bluetooth controller, with no USB DualSense present;
- exposed working gamepad buttons, motion sensors and touchpad input; and
- kept Bluetooth input working during one short concurrent Wi-Fi traffic
  check.

The first normal KDE Wi-Fi join failed because NetworkManager changed the
IW620 scan address and KDE tried an access-point object that the next scan had
already invalidated. A live configuration change fixed it: scan MAC
randomization was disabled, the permanent address was retained and power
saving stayed disabled. The normal Plasma menu then completed WPA3
association, DHCP and an HTTPS request over Wi-Fi.

The original **Switch to Desktop** integration did not pass. Its listener
watched a display-manager D-Bus call that Steam never sent in this tty-based
session. Manual selector plus a tty1 restart opened Plasma, proving that the
tty handoff itself worked. The live launcher was then changed from
`steam -gamepadui` to `steam -steamos -gamepadui`. With that flag Steam's
session integration deliberately used its legacy selector fallback and ran
`sudo /usr/bin/steamos-session-select plasma`. Gamescope exited and
Plasma/KWin started. The built-in Steam button therefore passed through
Steam's own legacy selector path.

A later remote selector test returned from Plasma to Gamescope/Steam by
stopping the owning user `graphical-session.target`; KDE exited in 0.086
seconds and no overlapping compositor remained. The current source keeps that
single target stop and performs no later process kill or login-session
termination. The actual desktop shortcut then passed with the same final
selector: its token changed from `plasma` to `gamescope` at 5.709 seconds, and
0.563 seconds later Gamescope was running with no KWin or Plasma shell. Still
pending: Bluetooth/Wi-Fi soak, controller reconnect after a cold boot, and a
cold boot of a replacement hosted artifact that contains all of these live
fixes.

## Why official gaming images switch sessions differently

SteamOS-style images normally ship a complete session stack around Steam,
including their selector and display-manager integration. This CachyOS port
deliberately uses a small tty1 launcher without SDDM. The original listener
guessed one display-manager D-Bus request, but Steam never sent it in this
environment.

Starting Steam with `-steamos` enables Steam's own distro-neutral legacy
fallback, which invokes the already working `steamos-session-select` helper.
That exact route passed on the console. `-steamos3` is intentionally not used
because it also enables SteamOS-specific atomic-update behavior that does not
match a pacman-managed CachyOS image.

## Behavior of the next build

- **Plasma first.** A freshly flashed image opens CachyOS Plasma on its first
  Linux boot. Configure networking there before launching Gaming Mode. When
  the desktop session ends, the one-shot token changes to Gaming Mode for later
  starts.
- **Steam bootstrap.** The first Gaming Mode setup needs internet access. Valve
  documents Offline Mode as a later-use feature that depends on saved account
  credentials and local game data; see [Steam Offline Mode](https://help.steampowered.com/en/faqs/view/0E18-319B-E34B-B2C8).
- **Desktop switching.** Gamescope launches `steam -steamos -gamepadui`.
  `-steamos` enables Steam's distro-neutral session integration without the
  SteamOS 3 atomic-update polling enabled by `-steamos3`. On this system Steam
  then uses its legacy `sudo steamos-session-select plasma` fallback, which is
  the path that passed live. The obsolete system-bus listener is not the
  working mechanism. In the reverse direction, the selector stops the owning
  user `graphical-session.target`; both a remote invocation and the actual
  desktop shortcut passed live without compositor overlap.
- **Wi-Fi.** `/etc/NetworkManager/conf.d/20-ps5-iw620.conf` disables scan MAC
  randomization, keeps the permanent address and sets `wifi.powersave=2`.
  The image does not contain console firmware; the bounded loader copies the
  firmware from that console before the image loads `mlan` and `moal`.
- **Bluetooth.** The image rebuilds the exact Bazzite Deck v1.0.3 IW620
  `btusb` source correction in its own Linux 7.3 kernel and uses the audited
  BlueZ policy. It does not copy another image's prebuilt `btusb.ko`.
- **Thermals and clocks.** The fixed maximum fan request runs before guarded
  GPU-then-CPU scaling. This is a bring-up policy, not a calibrated fan curve.
  `/boot/efi/disable-ps5-performance` remains the persistent opt-out.
- **Sleep.** Linux suspend and hibernate targets remain masked. Fully power off
  Linux before another loader attempt; do not use Linux sleep or GameOS Rest
  Mode after Linux has started.

## Requirements

- Regular retail PS5 on firmware 11.60, not PS5 Pro.
- Automatic system-software updates disabled.
- The 11.60 exploit, leaving the ELF listener on TCP port 9021.
- `ps5-linux-loader-1160-dma-e820-bounded-wifi.elf` from the
  [`firmware-11.60-dma-e820-bounded-run21`](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21)
  prerelease, SHA-256
  `e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f`.
- USB drive of at least 16 GB. Flashing erases the selected drive.
- HDMI and a wired USB keyboard. Keep Ethernet available for recovery even
  though the normal first-boot path should let you configure Wi-Fi in Plasma.
- Only one Linux USB drive attached to the console.

The default account is `steam` / `steam` with passwordless `sudo`. Keep the
console on a trusted local network and change the password after the baseline
test.

## Flash and boot

Verify the replacement release's published `SHA256SUMS` before flashing. Do
not combine image-2 files, the local image hash above or a third-party root
filesystem with this guide.

Start from a full PS5 power-off. Send the bounded Wi-Fi loader once, let GameOS
enter Rest Mode, wait for solid orange and wake once with the controller. The
loader should report bounded boot-file checks, a 498,108-byte Wi-Fi firmware
dump and:

```text
11.60 Sonic-style Linux wake chain armed
```

Check DHCP and SSH before treating a white light with no picture as a failed
boot.

On a fresh image, Plasma should appear first. Connect to the network from the
normal Plasma menu. Do not start the first Gaming Mode session until the
network is working.

## Identity and startup checks

Before updating packages or changing a service, save:

```sh
uname -r
pacman -Q linux-ps5
sha256sum /boot/efi/bzImage
cat /proc/cmdline
cat /home/steam/.config/ps5-next-session
systemctl --failed --no-pager
systemctl is-enabled ps5fan.service ps5-performance.service \
  ps5-iw620-firmware.service ps5-bt-quiet.service
systemctl is-enabled sleep.target suspend.target hibernate.target \
  hybrid-sleep.target suspend-then-hibernate.target
sudo /usr/local/sbin/ps5-boot-report
```

The first-session token should initially be `desktop`. After leaving Plasma it
should become `gamescope`. All five sleep targets should report `masked`.

## First Gaming Mode start and Offline Mode

Start Gaming Mode only after Plasma shows a working internet connection. Allow
Steam to complete its one-time bootstrap and sign in with saved credentials if
you intend to use Offline Mode later. Do not use an unplugged Ethernet cable as
the only offline test: disable every active connection and confirm Steam has
already saved the needed account and game state.

If Steam remains on an update/launch console for several minutes during the
first start, reconnect Ethernet. That recovery does not make an offline first
boot a pass. Return to Plasma using the recovery steps below and report that
the first Gaming Mode bootstrap had no network.

## Switch to Desktop and recovery

After Steam is fully initialized, choose **Power → Switch to Desktop** once.
Do not press it repeatedly. The tested path should use Steam's selector
fallback and then hand tty1 to Plasma. Record:

Give the transition time to finish while Steam and Gamescope exit and Plasma
starts. One clean measured pass took about 2.4 seconds; an earlier transition
that needed additional cleanup took about 27 seconds. Those are observations,
not a promised timeout, and a first transition may take longer. Do not click
again or power-cycle merely because **Switching to Desktop** remains visible
for several seconds.

```sh
ps -eo pid,args | grep '[s]team -steamos -gamepadui'
journalctl -b --no-pager | grep -E 'steamos-session-select|Switching to Desktop'
cat /home/steam/.config/ps5-next-session
```

If Steam remains on **Switching to Desktop**, use a wired USB keyboard:

1. Press `Ctrl`+`Alt`+`F2`. On a compact keyboard, also hold `Fn`. If tty2 does
   not appear, try `Ctrl`+`Alt`+`F3`.
2. Log in as `steam` with password `steam`.
3. Run:

   ```sh
   sudo steamos-session-select plasma
   sudo systemctl restart getty@tty1.service
   ```

4. Wait about ten seconds. If HDMI does not redraw, press
   `Ctrl`+`Alt`+`F1` once.

The same commands may be run over SSH. A successful manual recovery does not
turn the automatic button test into a pass. There is no known reliable
controller-only shortcut for this recovery.

To return to Gaming Mode from a terminal:

```sh
steamos-session-select gamescope
```

The live-tested selector stops the owning user `graphical-session.target`.
That remote selector path made KDE exit and Gamescope/Steam start without an
overlapping compositor. The actual desktop shortcut also passed: 0.563 seconds
after the token changed, Gamescope was running and both KWin and Plasma shell
were gone. The replacement artifact must still reproduce both directions.

## Wi-Fi

Check the image policy and driver before joining:

```sh
cat /etc/NetworkManager/conf.d/20-ps5-iw620.conf
systemctl status ps5-iw620-firmware.service --no-pager --full
lsmod | grep -E '^(mlan|moal)'
sudo dmesg | grep -Ei 'mlan|moal|WLAN FW is active|firmware'
nmcli device status
```

The file must contain:

```ini
[device]
wifi.scan-rand-mac-address=no

[connection]
wifi.powersave=2
wifi.cloned-mac-address=permanent
```

Join once through the normal Plasma menu. A pass requires association, DHCP
and traffic explicitly bound to Wi-Fi. If the menu fails, collect
NetworkManager's journal before trying a command-line workaround:

```sh
journalctl -b -u NetworkManager --no-pager
sudo nmcli --ask device wifi connect "<network name>"
```

Never publish the SSID, BSSID, MAC address, saved NetworkManager profile or the
loader-extracted firmware file.

## Bluetooth and DualSense

Do not attach an external Bluetooth adapter and do not copy another image's
`btusb.ko`. Record the baseline:

```sh
bluetoothctl list
sudo btmgmt info
lsusb -d 1286:2059
for module in btusb uhid hid_playstation; do modinfo -F vermagic "$module"; done
grep -E '^(AlwaysPairable|PairableTimeout|ControllerMode|Privacy|JustWorksRepairing|AutoEnable)=' /etc/bluetooth/main.conf
grep -E '^UserspaceHID=' /etc/bluetooth/input.conf
sudo dmesg | grep -Ei 'Bluetooth|btusb|hci[0-9]|1286|2059|opcode|xhci|usb.*disconnect|error -[0-9]+'
```

In Plasma, open **System Settings → Bluetooth → Add New Device**, hold
**Create + PS** until the controller flashes rapidly, then choose
**DualSense Wireless Controller**. If pairing succeeds but the wizard reports
a failed connection, close it, press **PS once** and allow the controller to
initiate the reconnect.

Verify that the controller is paired, bonded, trusted and connected, that no
USB DualSense is present, and that `hid-playstation` exposes the gamepad,
motion and touchpad devices:

```sh
bluetoothctl devices Paired
bluetoothctl devices Connected
bluetoothctl info XX:XX:XX:XX:XX:XX
lsmod | grep -E '^(btusb|bluetooth|uhid|hid_playstation)'
grep -Ei -A8 'DualSense|Wireless Controller' /proc/bus/input/devices
```

Linux pairing may replace the GameOS bond. Connect the controller by USB and
press PS in GameOS to pair it there again if necessary.

## Fan, clocks and opt-out

Verify the default policy before a load test:

```sh
systemctl status ps5fan.service ps5-performance.service --no-pager --full
journalctl -b -u ps5fan.service -u ps5-performance.service --no-pager
cat /sys/module/amdgpu/parameters/dpm
lsmod | grep -E '^(ps5_cpufreq|ps5_gpufreq)'
cat /sys/class/devfreq/ps5-gpufreq/governor
cat /sys/class/devfreq/ps5-gpufreq/cur_freq
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
cat /sys/devices/system/cpu/cpufreq/boost
sensors
```

The intended state is GPU `simple_ondemand`, CPU `schedutil` and CPU boost
`0`. A successful fan command proves only that the request was sent; no RPM
feedback or calibrated temperature curve is available.

Treat 80 °C as a conservative test stop, not a claimed hardware limit. Stop
earlier for a continuing rise, visual corruption, lost input or network, or a
new SMU, MP1, amdgpu, BUG or Oops line. Do not unload the frequency modules as
a rollback; that does not restore the clocks.

To skip the performance policy on the next cold boot:

```sh
sudo touch /boot/efi/disable-ps5-performance
sync
sudo poweroff
```

To restore it for a later cold boot:

```sh
sudo rm /boot/efi/disable-ps5-performance
sync
sudo poweroff
```

## Remaining release gates

The replacement hosted artifact is not ready for a public release until that
same exact image passes:

1. Three to five cold launches to Plasma, with HDMI and SSH.
2. Wi-Fi joining from the Plasma menu with the stable-MAC configuration.
3. First Gaming Mode bootstrap with internet, then a later start in configured
   Steam Offline Mode without Ethernet or Wi-Fi.
4. Reproduce the already observed full live round trip from the exact rebuilt
   artifact: Steam **Switch to Desktop**, then the desktop shortcut back to
   Gaming Mode, with no compositor overlap.
5. Internal Bluetooth pairing plus DualSense buttons, sticks, motion and
   touchpad input, followed by a cold-boot reconnect.
6. At least 60 minutes of concurrent Wi-Fi traffic and Bluetooth input with no
   controller, HCI, USB or network loss.
7. Default fan/performance startup and a bounded thermal load below the
   conservative stop point.
8. A separate cold boot with the FAT opt-out marker, proving that both
   frequency modules stay unloaded.
9. Clean `sudo poweroff` with every unsupported sleep target still masked.

Passing CI or the image verifier is software evidence only. The short
Wi-Fi/Bluetooth coexistence check already completed is encouraging, but it is
not the required soak.

## Reports and privacy

Include the exact image and loader hashes, PS5 model and firmware, USB port,
attempt number, light/HDMI/SSH timing, first-session result, Wi-Fi join,
desktop handoff, Bluetooth input, reconnect and soak results, temperatures,
and every change made after baseline.

Before sharing logs, remove IP addresses, MAC addresses, SSIDs, BSSIDs, serial
numbers, UUIDs, personal usernames and local paths. Do not upload console
firmware, keys, private dumps, a FAT-partition image or either copy of
`pcieuartiw620_combo_v1.bin`.
