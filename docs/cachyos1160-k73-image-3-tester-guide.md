# Testing the CachyOS image 3 source candidate on PS5 firmware 11.60

> **Not ready to flash.** Image 3 is a source candidate. There is no published
> image-3 archive, archive hash, raw-image hash or `bzImage` hash yet, and none
> of its new startup behavior has passed an exact-image console boot. Do not
> relabel image 2 or a local build as image 3. This warning stays in place until
> hosted CI produces one verified artifact and its identity is added here.

This document is the test plan for the next CachyOS prerelease. It describes
what the current source is intended to do, not what hardware testing has
already proved. The only identity-recorded hardware result for this CachyOS
7.3 profile remains Run 21, which used an earlier local image and manual
follow-up steps.

## Release identity

Do not start public testing until every field below has an exact value from the
same successful hosted-CI run.

| Item | Image 3 status |
|---|---|
| Release/tag | Not published |
| Source commit | `f7d6fbd9d630cddaceb83f3b861869d4453af8ca` on `main`; release tag pending |
| Hosted-CI run | [Kernel-cache run `39505071885`](https://github.com/gzimbric/ps5-linux-image/actions/runs/39505071885) in progress; full image run not started |
| Compressed archive size and SHA-256 | Not available |
| Raw image size and SHA-256 | Not available |
| `bzImage` SHA-256 | Not available |
| Exact hardware boot | Not attempted |

The final release must contain one `.img.xz`, not numbered parts. Build,
assembly, verification, compression and upload belong on the hosted runner;
testers should only download, verify and flash that single artifact.

## Intended image-3 behavior

The source candidate keeps Gaming Mode as the default and changes these areas:

- **Desktop handoff:** a narrow system-bus listener accepts only the expected
  display-manager `SwitchToUser` call for `doorstop` and a Plasma desktop. It
  writes the next-session token atomically and terminates exactly one `steam`
  session on `tty1`. It is intended to make Steam's **Switch to Desktop**
  action perform the manual handoff used in Run 21.
- **Linux sleep:** `sleep`, `suspend`, `hibernate`, `hybrid-sleep` and
  `suspend-then-hibernate` targets are masked. GameOS Rest Mode is only the
  carrier used by the loader before Linux starts. Once Linux is running, use a
  full power-off.
- **Wi-Fi:** the bounded loader still copies this console's own IW620 firmware
  to the USB drive. The enabled firmware service installs it before explicitly
  loading the pinned IW620 modules. NetworkManager uses `wifi.powersave=2`,
  which disables Wi-Fi power saving for this bring-up image. The image itself
  contains no console firmware.
- **Bluetooth:** the kernel build applies the exact source patch attached to
  [Bazzite Deck v1.0.3](https://github.com/VivaLaVent/ps5-bazzite-deck/releases/tag/v1.0.3),
  `ps5-btusb-quirks-fix.patch`, SHA-256
  `c01bdcc134f25a86825f2824d12a82da02db18e7b1940db722223b0c4611eed8`.
  It is rebuilt as part of this image's pinned Linux 7.3 kernel. It does not
  copy Bazzite's `btusb.ko`. The image also follows the working Bazzite BlueZ
  path with `AlwaysPairable=true`, `PairableTimeout=0`,
  `ControllerMode=dual`, `Privacy=device`, `JustWorksRepairing=always`,
  `AutoEnable=true`, and `UserspaceHID=true`. It uses the pairing agent
  supplied by KDE or `bluetoothctl` and the `uhid`/`hid-playstation` path;
  there is no custom pairing daemon and no `hidp` preload. The comparison base is Bazzite OCI digest
  `sha256:96301a1520b5bb63db95640896300c10ae3b1fcf8bf10681af154514395e1634`,
  built from [`ublue-os/bazzite` revision `2fab72c`](https://github.com/ublue-os/bazzite/tree/2fab72cbc9a3257d80c607e173f22527aea3b39b).
  Bazzite's 13.60 result supports this source combination but is not proof that
  it works on this 11.60 image.
- **Fan:** `ps5fan.service` requests fixed maximum servo pattern `3` at
  startup, before the performance policy. This is not a dynamic fan curve,
  and the console does not provide confirmed RPM feedback.
- **CPU/GPU scaling:** after the fan service succeeds,
  `ps5-performance.service` verifies `amdgpu dpm=0`, loads `ps5_gpufreq`
  before `ps5_cpufreq`, checks the GPU `simple_ondemand` governor, selects CPU
  `schedutil`, and keeps CPU boost off. A FAT-partition marker provides a
  persistent opt-out.

Every item above is a source assertion until the exact hosted artifact passes
the checks below.

## Hardware and loader requirements

- A regular retail PS5 on firmware 11.60, not PS5 Pro.
- Automatic system-software updates disabled.
- The 11.60 kernel exploit, leaving the ELF listener on TCP port 9021.
- The bounded Wi-Fi loader from
  [`firmware-11.60-dma-e820-bounded-run21`](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21):
  `ps5-linux-loader-1160-dma-e820-bounded-wifi.elf`, SHA-256
  `e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f`.
- A USB drive of at least 16 GB. Flashing erases the entire selected drive.
- Wired Ethernet connected throughout the run, even while testing Wi-Fi.
- HDMI, a USB keyboard and another computer on the same trusted LAN for SSH.
- Only one Linux USB drive attached to the console.

The final image-3 archive and its `SHA256SUMS` must come from the image-3
release once it exists. Do not combine image-2 boot files, a Run 21 local
image, or a third-party root filesystem with this test plan.

The default account is `steam` / `steam` and has passwordless `sudo`. Change
the password immediately and keep the console on a trusted network.

## Before each attempt

Begin with the PS5 fully powered off, not suspended. Keep GameOS HDMI Device
Link disabled and USB power in Rest Mode set to **Always**. Record:

- console model and firmware, without its serial number;
- image tag, archive hash and raw-image hash;
- loader filename and hash;
- USB model and PS5 port; and
- whether `/boot/efi/disable-ps5-performance` is present.

Run the exploit and send the bounded Wi-Fi ELF once. Confirm that the loader
prints its bounded boot-file checks, a 498,108-byte firmware dump and:

```text
11.60 Sonic-style Linux wake chain armed
```

Let GameOS enter Rest Mode, wait for a solid orange light, then wake it once
with the controller's PS button. Record light, HDMI, DHCP and SSH timing. A
white light with no picture may still be a headless Linux boot, so check DHCP
and SSH before powering off.

## Identity and startup checks

Before updating packages or changing a service, save the boot report and
verify the new startup policy:

```sh
uname -r
pacman -Q linux-ps5
sha256sum /boot/efi/bzImage
cat /proc/cmdline
systemctl --failed --no-pager
systemctl is-enabled ps5fan.service ps5-performance.service \
  ps5-iw620-firmware.service ps5-bt-quiet.service \
  ps5-session-switch-listener.service
systemctl status ps5fan.service ps5-performance.service \
  ps5-iw620-firmware.service ps5-bt-quiet.service \
  ps5-session-switch-listener.service --no-pager --full
systemctl is-enabled sleep.target suspend.target hibernate.target \
  hybrid-sleep.target suspend-then-hibernate.target
sudo /usr/local/sbin/ps5-boot-report
```

The release table must provide the expected `bzImage` hash before this can be
called an exact-image result. All five sleep targets should report `masked`.
Gaming Mode should appear without a manual session-selection command.

If the fan or performance service fails, save its full status and journal.
Do not work around it with manual module loads during that baseline boot.

## Fan and performance startup

The default image-3 path deliberately starts both frequency drivers. Verify
what actually happened:

```sh
systemctl status ps5fan.service ps5-performance.service --no-pager --full
journalctl -b -u ps5fan.service -u ps5-performance.service --no-pager
cat /sys/module/amdgpu/parameters/dpm
lsmod | grep -E '^(ps5_cpufreq|ps5_gpufreq)'
cat /sys/class/devfreq/ps5-gpufreq/governor
cat /sys/class/devfreq/ps5-gpufreq/available_frequencies
cat /sys/class/devfreq/ps5-gpufreq/cur_freq
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_driver
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies
cat /sys/devices/system/cpu/cpufreq/boost
sensors
```

The intended state is `amdgpu dpm=0`, GPU `simple_ondemand` with 400 MHz and
2230 MHz states, CPU `ps5-cpufreq` with 800 MHz and 3200 MHz states, CPU
`schedutil`, and boost `0`. A successful fan command only proves that the
request was sent; it does not prove an RPM or cooling response.

Keep a second terminal on temperature and clocks during any load:

```sh
watch -n 2 'sensors; echo GPU; cat /sys/class/devfreq/ps5-gpufreq/cur_freq 2>/dev/null || true; echo CPU; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || true'
```

Treat 80 °C as a conservative test stop, not a claimed hardware limit. Stop
earlier for a temperature that continues climbing, visual corruption, lost
input or network, a hung system, or new SMU, MP1, amdgpu, BUG or Oops lines.
Save logs and fully power off. Do not use `rmmod` as recovery; unloading these
drivers does not restore the clocks.

### Persistent performance opt-out

To prevent both frequency drivers from loading on the next boot:

```sh
sudo touch /boot/efi/disable-ps5-performance
sync
sudo poweroff
```

The service checks the marker only at startup. Creating it after either driver
has loaded does not undo that boot; fully power off. On the next run, confirm
that `ps5-performance.service` reports the marker and neither module is loaded.

To restore the default policy for a later cold boot:

```sh
sudo rm /boot/efi/disable-ps5-performance
sync
sudo poweroff
```

If `/boot/efi` is not mounted, the service is designed to fail closed rather
than load the drivers without access to the opt-out marker.

## Switch to Desktop

Complete the baseline checks first. Then choose **Switch to Desktop** once in
Steam and record the time until Plasma appears. Verify the constrained listener
and next-session token:

```sh
systemctl status ps5-session-switch-listener.service --no-pager --full
journalctl -b -u ps5-session-switch-listener.service --no-pager
cat /home/steam/.config/ps5-next-session
```

The token should be `plasma`. If Steam remains on **Switching to Desktop**,
do not trigger the button repeatedly. Recover over SSH:

```sh
sudo steamos-session-select plasma
cat /home/steam/.config/ps5-next-session
sudo systemctl restart getty@tty1.service
```

Press `Ctrl`+`Alt`+`F1` once if HDMI does not redraw. Save the listener journal
and report the automatic handoff as failed even if the manual recovery works.

## Wi-Fi

Leave Ethernet connected. The bounded loader must supply the console's own
firmware before the enabled service can load the driver:

```sh
cat /etc/NetworkManager/conf.d/20-ps5-iw620.conf
systemctl status ps5-iw620-firmware.service --no-pager --full
lsmod | grep -E '^(mlan|moal)'
sudo dmesg | grep -Ei 'mlan|moal|WLAN FW is active|firmware'
nmcli device status
```

The NetworkManager file should contain `wifi.powersave=2`. Try the KDE network
menu once. If it fails, record that result and use the known fallback:

```sh
sudo nmcli --ask device wifi connect "<network name>"
```

Never publish the SSID, BSSID or saved NetworkManager connection. Never upload
the loader-extracted `pcieuartiw620_combo_v1.bin` from either the FAT or Linux
filesystem.

## Bluetooth and DualSense

Do not attach an external Bluetooth adapter and do not copy another image's
`btusb.ko`. Before pairing, record:

```sh
bluetoothctl list
sudo btmgmt info
lsusb -d 1286:2059
lsusb -t
for module in btusb uhid hid_playstation; do modinfo -F vermagic "$module"; done
grep -E '^(AlwaysPairable|PairableTimeout|ControllerMode|Privacy|JustWorksRepairing|AutoEnable)=' /etc/bluetooth/main.conf
grep -E '^UserspaceHID=' /etc/bluetooth/input.conf
lsmod | grep -E '^(btusb|bluetooth|uhid|hid_playstation)' || true
grep -Rxs 'hidp' /etc/modules-load.d /usr/lib/modules-load.d || true
sudo dmesg | grep -Ei 'Bluetooth|btusb|hci[0-9]|1286|2059|opcode|xhci|usb.*disconnect|error -[0-9]+'
```

The target is exactly one internal controller, a real nonzero address, no
failed opcodes, no USB descriptor errors and no disconnect. If there is no
controller, two controllers, a zero address, opcode `0x2031` or `0x0c03`,
timeout `-110`, or a USB failure, stop. Save logs instead of repeatedly
restarting services or copying a binary module. The policy lines should be
exactly `AlwaysPairable=true`, `PairableTimeout=0`, `ControllerMode=dual`,
`Privacy=device`, `JustWorksRepairing=always`, `AutoEnable=true`, and
`UserspaceHID=true`. `btusb`, `uhid`, and `hid_playstation` should report the
running kernel's vermagic; `uhid` and `hid_playstation` may not appear in
`lsmod` until the controller connects. The `hidp` preload search should print
nothing.

With one healthy controller, first try KDE: open **System Settings →
Bluetooth**, choose **Add New Device**, hold **Create + PS** until the
controller flashes rapidly, and select **DualSense Wireless Controller**.
Wait through the brief repair/reconnect step before judging the result. If the
pair completes but KDE reports that the connection failed, press **PS once**
and allow the controller to initiate the reconnect.

For a clean command-line test, close KDE's pairing wizard first. Remove only a
clearly identified stale DualSense bond, put the controller back into pairing
mode with **Create + PS**, then run:

```text
bluetoothctl
power on
agent on
default-agent
pairable on
scan on
# Wait for the DualSense address, then substitute it below.
scan off
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
info XX:XX:XX:XX:XX:XX
quit
```

If only `connect` fails after a successful pair and trust, press **PS once**
instead of repeating the pairing loop; this tests the controller-initiated
reconnect used by the working path. Pairing in Linux may replace the GameOS
bond. USB-connect the controller and press PS in GameOS to pair it there again
if needed.

After the controller reconnects, verify the bond, transport and input device:

```sh
bluetoothctl devices Paired
bluetoothctl devices Connected
bluetoothctl info XX:XX:XX:XX:XX:XX
lsmod | grep -E '^(btusb|bluetooth|uhid|hid_playstation)'
grep -Ei -A8 'DualSense|Wireless Controller' /proc/bus/input/devices
sudo /usr/local/sbin/ps5-boot-report
```

Test buttons and sticks, then keep Bluetooth connected while Wi-Fi carries
ordinary traffic for at least 60 minutes. At the end, confirm that the HCI and
USB `1286:2059` device are still present.

## Required prerelease gates

Image 3 remains a source candidate until the same exact hosted-CI artifact
passes all of these on hardware:

1. Three to five launches that each begin after a full console power-off,
   reaching HDMI, Gaming Mode and SSH without boot-file changes.
2. Automatic **Switch to Desktop** handoff, plus a deliberate return to Gaming
   Mode if the UI provides it.
3. One internal Bluetooth controller and successful DualSense pairing.
4. Loader-supplied onboard Wi-Fi with `wifi.powersave=2` and a successful join.
5. At least 60 minutes of concurrent Wi-Fi traffic and Bluetooth input with no
   controller loss, USB disconnect or kernel error.
6. Default fan/performance startup and a bounded thermal load that remains
   stable below the conservative stop point.
7. A separate cold boot with `/boot/efi/disable-ps5-performance`, proving the
   opt-out leaves both frequency modules unloaded.
8. All sleep targets masked and clean shutdown through `sudo poweroff`.

Passing CI or the image verifier is software evidence only. One successful
boot is not enough to publish these integrations as hardware-proven.

## Reports and privacy

Before sharing logs, remove IP addresses, MAC addresses, SSIDs, BSSIDs, host
names, serial numbers, UUIDs, usernames and local paths. Keep the original
private copy so the redaction does not destroy evidence.

Include the exact image and loader hashes, PS5 model and firmware, USB port,
attempt number, light/HDMI/SSH timings, service status, desktop handoff result,
Bluetooth pairing and 60-minute result, Wi-Fi join result, temperatures, and
every change made after baseline. Clearly label failures and workarounds.

Do not upload console firmware, keys, private dumps, a FAT-partition image or
either copy of `pcieuartiw620_combo_v1.bin`.
