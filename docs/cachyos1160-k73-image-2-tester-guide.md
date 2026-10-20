# Testing CachyOS image 2 on PS5 firmware 11.60

> **Public prerelease for testers.** This exact CI-built image has not booted
> on hardware yet. Run 21 used an earlier local image from the same profile.
> Crashes and data loss are possible. Use this only on a regular retail PS5
> running firmware 11.60. The loader refuses PS5 Pro and every other firmware.

This guide tests one exact pair: CachyOS image 2 and the bounded 11.60 loader.
Do not substitute an older image, the Run 18 DMA loader, or the similarly
named unbounded Wi-Fi target.

## What is and is not proven

The bounded Wi-Fi loader booted an earlier local CachyOS 7.3 image once on a
CFI-1115B in Run 21. That run reached HDMI, SSH and onboard Wi-Fi. Image 2 was
built later with the Bluetooth and Wi-Fi load-order follow-ups. Its CI build,
archive, raw image and boot files passed their software checks, but this exact
image remains unbooted.

Image 2 enables `ps5fan.service` by default. It requests the tested maximum
fan servo pattern (`3`) used during bring-up. This is a fixed maximum request,
not a dynamic fan curve. The CPU and GPU frequency drivers remain manual and
must not be loaded for the first pass.

The first public tests need to answer four questions:

1. Does the exact image reach HDMI and SSH?
2. Does internal Bluetooth expose one working controller and stay present for
   at least 60 minutes?
3. Does loader-supplied IW620 firmware start Wi-Fi before the first probe?
4. Do Bluetooth and Wi-Fi work at the same time without USB dropping out?

Steam's **Switch to Desktop** action and joining Wi-Fi from KDE's network menu
are already known open issues. Record them, but do not confuse them with a
loader failure.

## Recover from the Switch to Desktop hang

On image 2, Steam can stay forever on **Switching to Desktop** because the
power-menu action does not call the image's session-switch helper. Linux is
usually still running. Do not put the console into Rest Mode and do not rerun
the payload.

From another computer, SSH to the console over wired Ethernet:

```sh
ssh steam@LINUX_IP
sudo steamos-session-select plasma
cat /home/steam/.config/ps5-next-session
sudo systemctl restart getty@tty1.service
```

The `cat` command must print `plasma`. Restarting tty1 deliberately closes the
stuck Gamescope/Steam session, so the SSH command may briefly appear to pause;
the SSH connection itself should remain available. KDE Plasma should then
appear on HDMI. If it does not, press `Ctrl`+`Alt`+`F1` once.

With a USB keyboard, the same recovery can be run locally: press
`Ctrl`+`Alt`+`F2`, log in as `steam`, run the four commands above starting at
`sudo steamos-session-select plasma`, then press `Ctrl`+`Alt`+`F1` if needed.

If `steamos-session-select` reports that `/etc/ps5-use-tty-sessions` is
missing, or the token does not read back as `plasma`, stop and save that exact
output. Do not repeatedly restart tty1. Image 3 is intended to wire the Steam
button to this already-tested handoff automatically; this section is the
image-2 fallback.

## Requirements

- A regular retail PS5 on firmware 11.60: original model or Slim, not Pro.
- Automatic system-software updates disabled.
- The 11.60 kernel exploit, leaving the ps5-payload-sdk ELF listener on TCP
  port 9021.
- One USB drive of at least 16 GB. A 32 GB drive or external SSD is preferred.
  Flashing erases the selected drive.
- Wired Ethernet, even when testing onboard Wi-Fi. Keep it connected as the
  diagnostic and SSH fallback.
- A computer on the same trusted LAN with SSH and a payload sender such as
  `socat` or `nc`.
- A monitor or TV on the PS5 HDMI output and a paired controller.
- Only one Linux USB drive attached to the PS5.

Set these in GameOS before starting:

- **Settings > System > Power Saving > Features Available in Rest Mode >
  Supply Power to USB Ports: Always**.
- **Settings > HDMI > Enable HDMI Device Link: off**.

## Exact downloads

Download the image and loader into **separate folders**. Both releases have a
file named `SHA256SUMS`; putting them together would overwrite one of the
checksum files.

### Image 2

Release:
[`cachyos1160-k73-image-2`](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-2)

Source tag `cachyos1160-k73-image-2` resolves to commit
`346088a48f66eb956dafdec9de5085e73b2d44a5`.

| File | Size | SHA-256 |
|---|---:|---|
| `ps5-cachyos1160-k73.img.xz` | 1,943,471,712 bytes | `8b785243f79a32a4155cc1e39bed01d580e25ca514e88abbfed1a8a8157a281a` |
| `ps5-cachyos1160-k73.img` after decompression | 12,582,912,000 bytes | `3798c7dba96412c5301eb201d8bf8aa4edd1b2f80a743dfd7b90b2a79222c62d` |

Download `ps5-cachyos1160-k73.img.xz` and `SHA256SUMS` from that release.

### Bounded loader

Release:
[`firmware-11.60-dma-e820-bounded-run21`](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21)

| File | Size | SHA-256 | Use |
|---|---:|---|---|
| `ps5-linux-loader-1160-dma-e820-bounded-wifi.elf` | 170,904 bytes | `e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f` | Recommended first test; this target booted Run 21 and copies the console's own IW620 firmware to the USB |
| `ps5-linux-loader-1160-dma-e820-bounded.elf` | 170,904 bytes | `1c80b040c5a808b3f09418728424a875d5598fe6b2a5d68adeb4db5979a7541a` | Non-Wi-Fi A/B build; it does not copy firmware and has not booted on hardware |

Use the bounded Wi-Fi ELF unless the test plan specifically calls for the
non-Wi-Fi A/B build. If the Wi-Fi ELF has run on a drive, its firmware copy
persists. Reflash the image before claiming a clean non-Wi-Fi test.

The loader release contains no Wi-Fi firmware. The Wi-Fi ELF reads each
console's own 498,108-byte IW620 firmware at runtime and writes it to
`lib/nxp/` on that console's USB drive. Never redistribute that file.

Do not use any of these with image 2:

- `ps5-linux-loader-1160-dma-e820.elf` from Run 18;
- `linux-1160-dma-e820-wifi`, which is not the bounded Wi-Fi build; or
- any earlier exact-size 11.60 loader.

They refuse image 2's boot files.

## Verify the downloads

Run the check once in the image folder and again in the loader folder.

Linux:

```sh
sha256sum -c --ignore-missing SHA256SUMS
```

macOS:

```sh
shasum -a 256 -c --ignore-missing SHA256SUMS
```

Windows PowerShell:

```powershell
# Run in the image folder:
Get-FileHash .\ps5-cachyos1160-k73.img.xz -Algorithm SHA256
# Run in the loader folder:
Get-FileHash .\*.elf -Algorithm SHA256
```

Every file used in the run must match the table above. Record both hashes in
the report.

## Flash the image

balenaEtcher and Raspberry Pi Imager can flash the `.img.xz` directly. In
Raspberry Pi Imager choose **Use custom** and decline OS customisation.

After flashing, macOS may call the disk unreadable; choose **Ignore**. Cancel
any Windows offer to initialize or format it.

`dd` erases whichever disk is named. Confirm the whole USB device before
running either command.

Linux:

```sh
lsblk -o NAME,SIZE,TRAN,MODEL,MOUNTPOINTS
# Unmount every mounted partition on the selected USB first.
xz -dc ps5-cachyos1160-k73.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

macOS:

```sh
diskutil list
diskutil unmountDisk /dev/diskN
xz -dc ps5-cachyos1160-k73.img.xz | sudo dd of=/dev/rdiskN bs=4m
sync
diskutil eject /dev/diskN
```

Record the drive model and PS5 port. For the first attempt, do not edit
`cmdline.txt`, `vram.txt`, or any other boot-partition file.

## Boot the exact pair

1. Turn the PS5 fully off. Do not begin from Rest Mode.
2. Attach only the newly flashed Linux USB. Prefer a rear Type-A port or the
   front Type-C port; the front top Type-A port is USB 2.0.
3. Connect Ethernet and select the PS5 HDMI input.
4. Boot GameOS and run only the kernel exploit. Do not load etaHEN, kstuff,
   FTP, a payload manager, or another payload first. This loader performs its
   own hypervisor step.
5. Send the selected ELF once to port 9021, replacing `PS5_IP` with the
   GameOS address:

   ```sh
   socat -t 99999999 - TCP:PS5_IP:9021 < ps5-linux-loader-1160-dma-e820-bounded-wifi.elf
   ```

   `nc` or a payload-sender application is also fine. Save the complete sender
   output locally.
6. Confirm that the output includes the bounded `bzImage` setup line and:

   ```text
   11.60 Sonic-style Linux wake chain armed
   ```

   The Wi-Fi build should also report a 498,108-byte firmware dump. The
   non-Wi-Fi build should instead report that the firmware offset is missing,
   continue booting, and write no firmware.
7. Let the console enter Rest Mode. Wait until the orange light stops blinking
   and remains solid.
8. Press the controller's PS button once. Do not press the console power
   button. Record the wake time.
9. Expect a white light, HDMI output and SSH. First boot can remain at a text
   console for a minute or two while Steam updates. Linux may receive a
   different DHCP address from GameOS, so check the router if SSH does not
   answer at the old address.

Login is `steam` / `steam`:

```sh
ssh steam@LINUX_IP
passwd
```

The account has passwordless `sudo`, so change its password immediately and
keep the console on a trusted LAN.

## First-pass checks

Before updating packages, joining Wi-Fi, editing the command line, switching
desktops, or loading either frequency driver, record whether HDMI, Gaming
Mode and SSH work and how long each took. Then save:

```sh
uname -r
pacman -Q linux-ps5
cat /proc/cmdline
sudo dmesg | grep -E 'BIOS-e820|device reserved'
grep -E 'MemTotal|HardwareCorrupted' /proc/meminfo
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
findmnt /
findmnt /boot/efi
systemctl --failed --no-pager
systemctl is-enabled ps5fan.service
systemctl status ps5fan.service --no-pager
lsmod | grep -E '^(ps5_cpufreq|ps5_gpufreq)' || true
sudo dmesg | grep -Ei 'BUG:|Oops:|I/O error|Buffer I/O|EXT4-fs error|amdgpu|vcn|xhci|btusb|Bluetooth|mlan|moal'
sudo /usr/local/sbin/ps5-boot-report
```

Expected identities:

- `uname -r`: `7.3.0`
- `pacman -Q linux-ps5`: `linux-ps5 7.3.0-2`
- `/proc/cmdline`:

  ```text
  root=LABEL=cachyos rw rootwait console=ttyTitania0 console=tty0 consoleblank=0 mitigations=off idle=halt preempt=full
  ```

- the e820 log includes:

  ```text
  BIOS-e820: [mem 0x0000000001000000-0x000000003fffffff]  device reserved
  ```

- `HardwareCorrupted` is `0 kB`; and
- `ps5fan.service` is enabled and its log shows that fixed servo pattern `3`
  was requested; and
- `ps5_cpufreq` and `ps5_gpufreq` are not loaded.

Do not load the frequency drivers during the first pass. Their Run 21 thermal
test did not reach equilibrium. A successful fan command provides no RPM
telemetry and does not prove cooling performance. If the fan service fails or
the console becomes hot or unstable, save the available evidence and run
`sudo poweroff`.

## What starts automatically

| Feature | Image 2 behavior |
|---|---|
| Fan | `ps5fan.service` is enabled and requests fixed maximum servo pattern `3` at boot. It is not a dynamic curve. |
| Wi-Fi | Conditional. The bounded Wi-Fi loader copies the console's own firmware to the USB boot partition. `ps5-iw620-firmware.service` then copies an exact-size file into `/lib/firmware/nxp/` and explicitly loads `moal`. The image contains no IW620 firmware. |
| Bluetooth | The kernel fix is built in and `btusb` should probe automatically. No patch, firmware copy or manual module load is required. Verify the result before changing the service state. |
| CPU/GPU frequency control | Off by default. Both modules are installed but have no alias or modules-load entry. Use the opt-in procedure below only after completing the baseline. |

With the bounded Wi-Fi ELF, no manual driver command is part of the baseline.
If the firmware service or driver fails, collect its status and kernel lines
before trying a reload. With the non-Wi-Fi ELF on a freshly flashed drive,
missing IW620 firmware and no Wi-Fi are expected.

## Optional frequency-driver test

These drivers talk to the SMU directly, have no thermal-cooling integration,
and remain experimental. Run 21 tried both in sequence, but did not establish
thermal equilibrium. For public testing, test **one module per cold boot**.
Do not load both in the same boot, and do not enable either at startup.

First finish every baseline check above. Confirm that neither module is loaded,
that the fixed maximum fan request succeeded, and that amdgpu power management
is disabled:

```sh
lsmod | grep -E '^(ps5_cpufreq|ps5_gpufreq)' || true
systemctl status ps5fan.service --no-pager
cat /sys/module/amdgpu/parameters/dpm
sensors
sudo /usr/local/sbin/ps5-boot-report
```

The `dpm` value must be `0`. If it is not, do not load a frequency module:
amdgpu would be using the same mailbox. Keep the system idle and record the
temperature every 30 seconds for 10 minutes before the module load. The only
temperature available in Run 21 was `k10temp`/Tctl; it is not a separate GPU
sensor.

Choose one of these two tests. They are alternatives, not a sequence.

GPU test:

```sh
sudo modprobe ps5_gpufreq
lsmod | grep '^ps5_gpufreq'
cat /sys/class/devfreq/ps5-gpufreq/governor
cat /sys/class/devfreq/ps5-gpufreq/available_frequencies
cat /sys/class/devfreq/ps5-gpufreq/cur_freq
sudo dmesg | grep -Ei 'ps5-gpufreq|SMU|MP1|amdgpu|BUG:|Oops:' | tail -n 80
```

CPU test, after a full power-off and a separate clean boot:

```sh
sudo modprobe ps5_cpufreq
lsmod | grep '^ps5_cpufreq'
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_driver
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq
sudo dmesg | grep -Ei 'ps5-cpufreq|SMU|MP1|amdgpu|BUG:|Oops:' | tail -n 80
```

Keep a second terminal on the temperature and clock while the module is loaded:

```sh
watch -n 2 'sensors; echo GPU; cat /sys/class/devfreq/ps5-gpufreq/cur_freq 2>/dev/null || true; echo CPU; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || true'
```

For this prerelease test, treat 80 °C as a conservative stop point, not as a
claimed hardware limit. Stop earlier for a rising temperature that does not
settle, visual corruption, loss of input or network, a hung system, or new SMU,
MP1, amdgpu, BUG or Oops lines. Run 21 reached 84 °C during an incompletely
observed load, so do not use that run as permission to continue past 80 °C.

At the end, save a new boot report and relevant kernel lines, then fully power
off:

```sh
sudo /usr/local/sbin/ps5-boot-report
sudo dmesg | grep -Ei 'ps5-(cpu|gpu)freq|SMU|MP1|amdgpu|BUG:|Oops:' | tail -n 120
sudo poweroff
```

Do not rely on `rmmod` as recovery: unloading these modules does not restore
the clocks (`ps5_cpufreq` only unregisters itself). Do not suspend, enter Rest
Mode, or start the other module before the console has fully powered off.

## Bluetooth hotfix for image 2

If KDE reports that setting up a DualSense failed, do not copy `btusb.ko`
from Bazzite or any other image. A kernel module must match the exact kernel
build, configuration and symbol versions that load it. A module built for a
different image can fail to load or make the diagnosis less clear even when
both kernels report `7.3.0`.

First confirm that this is the published image-2 kernel, then try the safe
userspace reset once:

```sh
sha256sum /boot/efi/bzImage
sudo rfkill unblock bluetooth
sudo systemctl restart bluetooth.service
sudo systemctl restart ps5-bt-quiet.service
bluetoothctl list
```

The expected image-2 `bzImage` SHA-256 is
`8cc74e8d29a9a2a2e8bd7fd0a2834b4b898868711816ab77194c05f66c6f757e`.
Stop and report the actual hash if it differs.

Continue only if `bluetoothctl list` shows exactly one internal controller.
Close KDE's pairing wizard, unplug the DualSense USB cable and hold the
controller's PS button for about ten seconds to turn it off. Then open the
terminal pairing tool:

```text
bluetoothctl
power on
agent on
default-agent
devices Paired
```

If `devices Paired` lists an old **DualSense Wireless Controller** entry,
remove only that entry with `remove XX:XX:XX:XX:XX:XX`. Do not remove an
unknown device. Hold **Create + PS** on the controller until its blue light
flashes rapidly, then run:

```text
scan on
devices
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
info XX:XX:XX:XX:XX:XX
scan off
quit
```

Replace the example address with the DualSense address shown by `devices`.
Redact that address from any public report. Pairing the controller in Linux
may replace its GameOS bond. If GameOS no longer connects wirelessly later,
attach the controller by USB and press PS in GameOS to pair it there again.

If `bluetoothctl list` shows no controller or more than one controller, or the
kernel log contains failed HCI opcodes, timeouts, USB disconnects or USB
descriptor errors, stop. Repeating the service restart or KDE wizard cannot
repair a failed kernel or USB probe. Save a diagnostic report instead:

```sh
stamp=$(date -u +%Y%m%dT%H%M%SZ)
report="$HOME/ps5-bluetooth-$stamp.txt"
sudo -v
{
  echo '[identity]'
  date -u
  uname -a
  pacman -Q linux-ps5 bluez bluez-utils bluedevil 2>&1 || true
  sha256sum /boot/efi/bzImage 2>&1 || true
  echo '[usb-and-module]'
  lsusb -d 1286:2059 2>&1 || true
  lsusb -t 2>&1 || true
  btusb=$(modinfo -n btusb 2>/dev/null || true)
  echo "btusb=$btusb"
  [ -z "$btusb" ] || sha256sum "$btusb" 2>&1 || true
  modinfo -F vermagic btusb 2>&1 || true
  lsmod | grep -E '^(btusb|btintel|btbcm|btrtl|btmtk|bluetooth|hid_playstation)' || true
  echo '[controllers]'
  bluetoothctl list 2>&1 || true
  bluetoothctl show 2>&1 || true
  bluetoothctl devices 2>&1 || true
  bluetoothctl devices Paired 2>&1 || true
  sudo btmgmt info 2>&1 || true
  rfkill list bluetooth 2>&1 || true
  echo '[services-and-journal]'
  systemctl status bluetooth.service ps5-bt-quiet.service --no-pager --full 2>&1 || true
  sudo journalctl -b -u bluetooth.service -u ps5-bt-quiet.service --no-pager 2>&1 || true
  sudo journalctl -b -k --no-pager 2>&1 |
    grep -Ei 'Bluetooth|btusb|hci[0-9]|1286|2059|opcode|xhci|usb.*disconnect|error -[0-9]+' |
    tail -n 250 || true
  echo '[desktop-journal]'
  journalctl --user -b --no-pager 2>&1 |
    grep -Ei 'bluez|bluetooth|bluedevil|pair|authentication' |
    tail -n 200 || true
} 2>&1 | tee "$report"
chmod 600 "$report"
echo "Saved $report"
```

The report contains Bluetooth MAC addresses and may contain other private
identifiers. Redact it before attaching it to a public issue. A single healthy
controller that pairs in `bluetoothctl` points to a stale bond or KDE pairing
problem. No controller, two controllers, a zero address, failed opcodes such
as `0x2031` or `0x0c03`, timeout `-110`, or a USB disconnect points to the
kernel/USB path and needs a new image rather than another userspace reset.

## Bluetooth test

Use no external Bluetooth adapter. The kernel should probe the internal device
without a manual module load. Record these before pairing:

```sh
bluetoothctl list
hciconfig -a 2>/dev/null || true
sudo dmesg | grep -Ei 'Bluetooth|btusb|xhci|0x2031|0x0c03'
for d in /sys/bus/usb/devices/*; do
  if [ "$(cat "$d/idVendor" 2>/dev/null)" = 1286 ] && \
     [ "$(cat "$d/idProduct" 2>/dev/null)" = 2059 ]; then
    echo "$d power/control=$(cat "$d/power/control" 2>/dev/null)"
  fi
done
```

The target result is one internal controller (`hci0`), no second controller,
no failed opcode `0x2031` or `0x0c03`, and `power/control=on` for USB
`1286:2059`. Pair a DualSense, test its buttons and sticks, and redact the
controller address from anything shared.

If an internal controller exists but `bluetooth.service` is inactive, first
save its status and journal, then this may be tried once as a clearly labeled
follow-up:

```sh
systemctl status bluetooth.service --no-pager
sudo journalctl -b -u bluetooth.service --no-pager
sudo systemctl start bluetooth.service
sudo bluetoothctl power on
```

If `bluetoothctl list` still shows no controller, service restarts cannot repair
a failed kernel probe. Save the kernel lines and report the failure without
repeated resets.

Keep the system running for at least 60 minutes, then confirm that `hci0` and
the USB device are still present. Run 21 lost the internal USB device at about
51 minutes, so a short pairing test is not enough.

## Wi-Fi and coexistence test

This section is only for the bounded Wi-Fi ELF. Leave Ethernet connected.

```sh
systemctl is-enabled ps5-iw620-firmware.service
systemctl status ps5-iw620-firmware.service --no-pager
lsmod | grep -E '^(mlan|moal)'
sudo dmesg | grep -Ei 'mlan|moal|WLAN FW is active|firmware'
nmcli device status
```

Try joining once from KDE's network menu and record the exact result. If it
fails, use the known workaround:

```sh
sudo nmcli --ask device wifi connect "<network name>"
```

Do not publish the SSID, BSSID or saved NetworkManager connection. After the
join, verify ordinary HTTPS traffic over Wi-Fi and recheck Bluetooth input and
the 60-minute stability result while Wi-Fi remains active.

## Reports and privacy

The boot report is written to `/var/log/ps5-boot-report.txt` and, when the
boot partition is mounted, `/boot/efi/ps5-boot-report.txt`. It masks Wi-Fi
names and MAC addresses, but it retains IP addresses. **Never post it raw.**

Before sharing any output, remove:

- IPv4 and IPv6 addresses;
- MAC, BSSID and controller addresses;
- SSIDs, router names and host names;
- serial numbers, filesystem UUIDs, usernames and local paths; and
- journal identifiers or anything else unique to the console or network.

Never upload or redistribute any of these:

- `/boot/efi/lib/nxp/pcieuartiw620_combo_v1.bin`;
- `/lib/firmware/nxp/pcieuartiw620_combo_v1.bin`;
- a complete FAT-partition dump;
- raw console firmware, keys, private dumps or unsanitized logs.

Open a
[porting issue](https://github.com/gzimbric/ps5-linux-porting/issues/new)
with the title `CachyOS image 2 test: CFI-xxxx`. Include:

- console model and firmware, without a serial number;
- image tag, archive hash, loader filename and loader hash;
- USB model/port and number of attempts;
- loader's bounded line, firmware-dump result and final wake marker;
- light, HDMI, Gaming Mode and SSH results with timings;
- kernel/package identity, e820 result and important errors;
- `ps5fan.service` enabled/status output and whether the pattern `3` request
  succeeded;
- Bluetooth pairing, input and 60-minute stability result;
- KDE Wi-Fi result, `nmcli` result and Bluetooth/Wi-Fi coexistence result;
- every modification made after the first pass; and
- only sanitized excerpts or a sanitized boot report.

Report failures as carefully as passes. A white light with no picture may be
a headless Linux boot, so check DHCP and SSH before powering off.

## Recovery and known issues

- **No HDMI:** wait two minutes, then check DHCP and SSH. If SSH works, save
  `sudo dmesg` and the boot report before changing anything. A VCN-disabled
  retry is a second, modified test; follow the image release notes and label it
  clearly.
- **Pulsing blue or no network:** fully power off before another attempt. Do
  not reuse a stale carrier or begin from Rest Mode.
- **No Wi-Fi with the non-Wi-Fi ELF:** expected. That build never copies the
  firmware.
- **KDE Wi-Fi join fails:** record it once, then use the `nmcli` workaround.
- **KDE says DualSense setup failed:** use the one-time userspace reset and
  terminal pairing steps in [Bluetooth hotfix for image 2](#bluetooth-hotfix-for-image-2).
  Never install another image's `btusb.ko`.
- **Switch to Desktop hangs:** this is a known image issue. Do not repeatedly
  trigger it during the baseline run.
- **Suspend or Rest Mode inside Linux:** unsupported. Finish with
  `sudo poweroff`, not suspend or Rest Mode.

