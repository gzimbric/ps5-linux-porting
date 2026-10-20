# Testing the 11.60 DMA build with the CI Ubuntu image

This page is for people with a retail PS5 on firmware 11.60 who want to test
one combination: the DMA E820 build of the 11.60 loader with the Ubuntu 24.04
image built by GitHub CI.

A CachyOS image on Linux 7.3.0 is in controlled testing, but it is not a
general tester release yet. Image 2 is pinned at
`cachyos1160-k73-image-2` / `346088a`. Its successful CI run and exact draft
image identity are verified, but it has not been booted. This guide still
covers only the hardware-tested Ubuntu build 3 pair.

## What this tests

The DMA E820 build (`ps5-linux-loader-1160-dma-e820.elf`) is the Run 15 loader
with one change taken from the 13.60 support in upstream
[`ps5-linux-loader`](https://github.com/ps5-linux/ps5-linux-loader) (commit
`8cda4c1`): in low memory, Linux gets RAM only at `[0x00100000, 0x01000000)`
and sees `[0x01000000, 0x40000000)` as reserved. Testers have reported
read/write errors on the 11.60 port. Other developers said this reservation
fixed the same problem on 13.60. No exact error text has been received and the
errors have not been reproduced on the test console, so this build is not a
known fix. [Run 18](../evidence/11.60-cachyos-run-18-dma-e820.md) booted it
with CachyOS on one console: Linux received the intended memory map and
passed a short USB write and read check.
[Run 19](../evidence/11.60-ubuntu-ci-run-19.md) then booted this ELF with the
build 3 image from this guide on the same CFI-1115B. A picture appeared on the
monitor, SSH worked, the e820 check showed the `device reserved` line, and the
optional I/O check passed. Other models have no recorded result with this
pair yet. Reports from other consoles are still needed.

Expect about 1008 MiB less usable RAM than with the Run 15 loader.

## Status

| Console | Status |
|---|---|
| Original model, digital edition | This ELF booted on one CFI-1115B: with CachyOS in Run 18, and with the build 3 image from this guide in Run 19 (picture, SSH, e820 line, and I/O check pass). No other console has a recorded result yet. |
| Original model, disc edition | Should work: same chip, board, and firmware as the digital edition. Not tested. |
| Slim (CFI-2xxx) | Allowed by the loader, but nobody has booted a Slim with the 11.60 port. The display path is the most likely failure, which would look like Linux running with no picture. |
| Pro (CFI-7xxx) | Refused. The loader stops before it changes anything. |
| Any firmware other than retail 11.60 | Refused before setup. |

What has run on hardware so far:

| Combination | Result |
|---|---|
| Run 15 ELF with the Run 16 Ubuntu image | Booted in Runs 16 and 17. That image has the same kernel, command line, and VRAM file as the CI image, and a different initrd build of the same size. |
| DMA ELF with CachyOS | Booted in Run 18 |
| DMA ELF with the CI Ubuntu image (build 3) | Booted in Run 19 on one CFI-1115B: picture on the monitor, SSH, the `device reserved` e820 line, and the I/O check passed |
| Run 15 ELF with the CI Ubuntu image | Not booted |
| Any other CI build | Not booted |

## Requirements

- A retail PS5 on firmware 11.60, original model or Slim, not a Pro. Keep
  automatic system software updates off.
- The kernel exploit you use on 11.60, as long as it leaves the
  ps5-payload-sdk ELF loader listening on port 9021.
- A USB drive of 32 GB or larger. Flashing erases it.
- Wired Ethernet. The image has no Wi-Fi.
- A computer on the same network, with `socat` (or `nc`, or a payload sender
  app) and `ssh`.
- A monitor or TV on the PS5's HDMI port, and a controller paired with the
  console.
- These PS5 settings:
  - Settings > System > Power Saving > Features Available in Rest Mode >
    Supply Power to USB Ports: **Always**.
  - Settings > HDMI > Enable HDMI Device Link: **off**.
- Only one Linux USB drive plugged into the PS5. The loader takes each boot
  file from the first USB drive that has it, so a second Linux drive can
  supply the wrong files.

## Downloads

### Loader ELF

Download `ps5-linux-loader-1160-dma-e820.elf` from the loader release
[`firmware-11.60-dma-e820-run18`](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-run18).

| File | Size | SHA-256 |
|---|---:|---|
| `ps5-linux-loader-1160-dma-e820.elf` | 169,872 bytes | `2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0` |

The Run 15 ELF has the same size, so check the hash. In the folder with the
file, on Linux:

```sh
echo "2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0  ps5-linux-loader-1160-dma-e820.elf" | sha256sum -c
```

On macOS:

```sh
echo "2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0  ps5-linux-loader-1160-dma-e820.elf" | shasum -a 256 -c
```

Both print `ps5-linux-loader-1160-dma-e820.elf: OK` when the file matches. On
Windows, run either of these and compare the result with the table (case does
not matter):

```text
certutil -hashfile ps5-linux-loader-1160-dma-e820.elf SHA256
Get-FileHash ps5-linux-loader-1160-dma-e820.elf -Algorithm SHA256
```

The first works in Command Prompt or PowerShell, the second in PowerShell.
Test the release file. A rebuild with a different toolchain is not expected
to give the same hash.

### Ubuntu image

The image is on the release
[`ubuntu2404-1160-build-3`](https://github.com/gzimbric/ps5-linux-image/releases/tag/ubuntu2404-1160-build-3).
Its title starts with "Ubuntu 24.04 for PS5 firmware 11.60". A later build
would have a title that starts the same way and a different tag; write down
the tag you used.

| File | Size | SHA-256 |
|---|---:|---|
| `ps5-ubuntu2404.img.xz` | 1,917,204,004 bytes | `133819629e535a782ae8e3f83946eb2d69f523419aaf9f6fffee3454604a629e` |
| `ps5-ubuntu2404.img` (after decompressing) | 16,777,216,000 bytes | `cb01a4f53dedc390a07cdcd42b93dda0762e0c4dee8efe0130af7bdb36ba7fda` |

1. Download `ps5-ubuntu2404.img.xz` and `SHA256SUMS` into one folder.
2. Check the download. On Linux:

   ```sh
   sha256sum -c --ignore-missing SHA256SUMS
   ```

   On macOS:

   ```sh
   shasum -a 256 -c --ignore-missing SHA256SUMS
   ```

   The output must include `ps5-ubuntu2404.img.xz: OK` and no `FAILED` line.
   On Windows, run `certutil -hashfile ps5-ubuntu2404.img.xz SHA256` and
   compare the result with the table. If the check fails, download the file
   again.
3. Keep the tag and the `ps5-ubuntu2404.img` line from `SHA256SUMS` for your
   report. They identify the build.

Every release uses one `ps5-ubuntu2404.img.xz`. The image workflow stops
before creating a release if the compressed file reaches GitHub's 2 GiB
per-file limit; it does not publish numbered parts.

### Flashing

balenaEtcher and Raspberry Pi Imager can flash `ps5-ubuntu2404.img.xz`
directly, without decompressing it first. In Raspberry Pi Imager, choose
"Use custom" as the operating system. If it offers OS customisation, choose
No; it would change files on the boot partition.

After flashing, macOS may say the disk is not readable by this computer.
Click **Ignore**. Windows may offer to format the drive; cancel. Do not
initialize or format it.

Use `dd` only if you know exactly which device is the USB drive. **`dd`
writes to whatever device you name, without asking. The wrong name erases
that disk, and it can be your computer's own drive.**

On Linux, run `lsblk -o NAME,SIZE,TRAN,MODEL,MOUNTPOINT` before and after
plugging the drive in. The USB drive is the new disk with `TRAN` `usb` and
the size you expect, for example `sdb`. Use the whole disk, not a partition
such as `sdb1`. Unmount any of its partitions that show a mount point with
`sudo umount`, then:

```sh
xz -dc ps5-ubuntu2404.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

On macOS, run `diskutil list` before and after plugging the drive in. The USB
drive is the new `/dev/diskN (external, physical)` entry with the size you
expect. Then:

```sh
diskutil unmountDisk /dev/diskN
xz -dc ps5-ubuntu2404.img.xz | sudo dd of=/dev/rdiskN bs=4m
sync
diskutil eject /dev/diskN
```

`xz` is not always installed on macOS. If it is missing, use balenaEtcher.

Test the image as released. Do not edit `cmdline.txt`, `vram.txt`, or other
files on the boot partition, and do not add Wi-Fi before reporting. The
official `ps5-linux-image` releases do not work with the 11.60 loader: their
`initrd.img` is not the size it requires.

## Boot

1. Plug the USB drive into a rear Type-A port or the front Type-C port. The
   front top Type-A port is USB 2.0 and slower. Leave any other Linux USB
   drive unplugged.
2. Connect the Ethernet cable.
3. Cold boot: turn the PS5 off completely (Turn Off PS5, not Rest Mode), then
   turn it on.
4. Run only the kernel exploit, so that the ELF loader is listening on port
   9021. Do not load etaHEN, kstuff, Byepervisor, a payload manager, FTP, or
   any other payload first. The loader does its own hypervisor step.
5. Send the ELF once from your computer. Replace `PS5_IP` with the console's
   address, shown in PS5 OS under Settings > Network > Connection Status >
   View Connection Status:

   ```sh
   socat -t 99999999 - TCP:PS5_IP:9021 < ps5-linux-loader-1160-dma-e820.elf
   ```

   `nc` or a payload sender app that sends to port 9021 also works. `socat`
   is not installed by default on macOS or Windows. On macOS, install it with
   Homebrew (`brew install socat`) or use `nc`. On Windows, use a payload
   sender app; the `<` in the command above does not work in PowerShell.

   If your sender shows the loader's output, it should include
   `11.60 Sonic-style Linux wake chain armed`. The lines
   `PS5 WiFi firmware offset missing for firmware 1160` and
   `Something went wrong while dumping device firmwares - Continuing` are
   expected: this build cannot copy the Wi-Fi firmware, and the boot carries
   on. If the output does not include the `wake chain armed` line, copy all
   of it into your report. You can stop `socat` with Ctrl+C once the console is in Rest
   Mode.
6. The console enters Rest Mode by itself. Wait until the orange light stops
   blinking and stays solid.
7. Turn the monitor on and set it to the PS5 input.
8. Press the PS button on the controller once. Do not use the power button on
   the console, although upstream's README mentions it.
9. The light should turn white and a picture should appear. SSH should answer
   within about a minute.
10. Log in from your computer. The password is `ubuntu`. Under Linux, your
    router may give the console a different address than it had in PS5 OS;
    if `ssh` does not connect, see "No SSH" under
    [Troubleshooting](#troubleshooting).

    ```sh
    ssh ps5@PS5_IP
    ```

11. Change the password straight away, and keep SSH on a trusted local
    network:

    ```sh
    passwd
    ```

## Checks once Linux is up

Run these in the SSH session.

1. Memory map. This is the main check.

   ```sh
   sudo dmesg | grep BIOS-e820
   ```

   The output must include the `device reserved` line below. These are the
   relevant lines from Run 18, without timestamps; other lines are printed
   too:

   ```text
   BIOS-e820: [mem 0x0000000000100000-0x0000000000ffffff]  System RAM
   BIOS-e820: [mem 0x0000000001000000-0x000000003fffffff]  device reserved
   BIOS-e820: [mem 0x0000000040000000-0x000000005fffffff]  System RAM
   ```

   If there is no `0x0000000001000000-0x000000003fffffff` line and a
   `System RAM` line ends at `0x000000003fffbfff` instead, the old Run 15
   loader was sent. Check the ELF hash and boot again.

2. Memory size.

   ```sh
   free -h
   grep -E 'MemTotal|HardwareCorrupted' /proc/meminfo
   ```

   The `Mem:` total should be about 14 GiB. Run 18 reported a `MemTotal` of
   14,783,608 kB and a `HardwareCorrupted` of 0 kB. With the Run 15 loader,
   Run 16 had about 15 GiB.

3. Kernel, command line, and drive layout.

   ```sh
   uname -r
   cat /proc/cmdline
   lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
   ```

   The kernel should be `7.1.7` and the command line should be:

   ```text
   root=LABEL=ubuntu2404 rw rootwait console=ttyTitania0 console=tty0 consoleblank=0 mitigations=off idle=halt preempt=full
   ```

   `lsblk` should show the ext4 `ubuntu2404` root mounted at `/` and grown to
   about the size of the drive, and the FAT `boot` partition.

4. Storage errors.

   ```sh
   sudo dmesg | grep -iE 'I/O error|EXT4-fs (error|warning)|reset .*USB device|xhci.*(error|dead|died|not responding)|IO_PAGE_FAULT'
   ```

   Run 18's scan for these found nothing. Paste any line this prints into
   your report.

5. Optional I/O check, similar to Run 18. The script below writes up to three
   4 GiB files of random data under `/var/tmp`, flushes them, drops the page
   cache, re-reads them, and compares SHA-256. It refuses to start unless
   `/var/tmp` is on ext4 and at least 12 GiB is free, writes fewer files when
   space is short so that at least 8 GiB stays free, and deletes its files at
   the end, including after a failure or Ctrl+C. Run 18 wrote and re-read
   12 GiB in about 2 minutes; a slower drive takes longer.

   If the console hangs or loses power during the check, report that as the
   result. The test files then stay behind. Remove them with
   `sudo rm -rf /var/tmp/ps5-io-check` before running the check again.

   Paste this whole block into the SSH session. It only creates the script:

   ```sh
   cat > ~/ps5-io-check.sh <<'EOF'
   #!/bin/bash
   # Write up to three 4 GiB files under /var/tmp, flush them, drop the page
   # cache, re-read and compare SHA-256, then delete them.
   set -euo pipefail

   dir=/var/tmp/ps5-io-check
   file_gib=4
   max_files=3
   keep_free_gib=8
   storage_errors='I/O error|EXT4-fs (error|warning)|reset .*USB device|xhci.*(error|dead|died|not responding)|IO_PAGE_FAULT'

   if [ "$(id -u)" -ne 0 ]; then
     echo "Run this with sudo." >&2
     exit 1
   fi
   if [ -e "$dir" ]; then
     echo "$dir is left from an earlier run. Remove it with: sudo rm -rf $dir" >&2
     exit 1
   fi
   fstype=$(findmnt -no FSTYPE -T /var/tmp)
   if [ "$fstype" != ext4 ]; then
     echo "/var/tmp is on $fstype, not the ext4 USB root. Stopping." >&2
     exit 1
   fi

   avail=$(df --output=avail -B1 /var/tmp | tail -n 1 | tr -d ' ')
   avail_gib=$(( avail / 1024 / 1024 / 1024 ))
   count=$(( (avail_gib - keep_free_gib) / file_gib ))
   if [ "$count" -gt "$max_files" ]; then count=$max_files; fi
   if [ "$count" -lt 1 ]; then
     echo "Only $avail_gib GiB free under /var/tmp. Need at least $(( keep_free_gib + file_gib )) GiB." >&2
     exit 1
   fi
   echo "Free under /var/tmp: $avail_gib GiB. Writing $count x $file_gib GiB."

   mkdir -- "$dir"
   trap 'rm -rf -- "$dir"; echo "Removed $dir."' EXIT
   trap 'exit 130' INT TERM
   marker="ps5-io-check start $$-$(date +%s)"
   echo "$marker" > /dev/kmsg

   for i in $(seq 1 "$count"); do
     start=$(date +%s)
     sum=$(head -c $(( file_gib * 1024 * 1024 * 1024 )) /dev/urandom | tee "$dir/file$i" | sha256sum | cut -d ' ' -f 1)
     sync
     printf '%s  %s\n' "$sum" "$dir/file$i" >> "$dir/written.sha256"
     echo "Wrote file$i in $(( $(date +%s) - start )) s."
   done

   sync
   echo 3 > /proc/sys/vm/drop_caches
   echo "Page cache dropped. Re-reading."
   start=$(date +%s)
   if sha256sum -c "$dir/written.sha256"; then result=PASS; else result=FAIL; fi
   echo "Re-read in $(( $(date +%s) - start )) s."

   if dmesg | sed -n "/$marker/,\$p" | grep -iE "$storage_errors"; then
     echo "Storage error lines were logged during the test (above)."
   else
     echo "No storage error lines were logged during the test."
   fi
   echo "Result: $result ($count x $file_gib GiB)"
   EOF
   ```

   Then run it:

   ```sh
   sudo bash ~/ps5-io-check.sh
   ```

6. If you saw read/write errors with the old loader, repeat what you were
   doing when they appeared and note whether they come back.

## When you are done

Copy your results out of the SSH session first, then run:

```sh
sudo poweroff
```

If the light is still on after a minute, hold the console's power button
until it turns off. The loader runs only when you send it, so the next
power-on starts PS5 OS. PS5 OS may show a "Repairing" screen or say the
console was not turned off properly; upstream describes that as harmless.

To change a PS5 setting such as HDCP, turn the console off this way, change
the setting in PS5 OS, and repeat the [Boot](#boot) steps from a cold boot.

## Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| `Something went wrong while initiating` right after `Welcome` | A payload manager ran the ELF through its own loader, which lacks the SDK ELF loader's kernel read/write | Cold boot, run only the kernel exploit, and send to port 9021 with `socat`, `nc`, or a sender that targets 9021 |
| `Something went wrong while installing linux files` right after `File 'bzImage' found` and `File 'initrd.img' found` | The USB does not have the 11.60 image. The loader only accepts an `initrd.img` of exactly 54,376,639 bytes and refuses anything else; a payload menu does not show the refusal line. The official `ps5-linux-image` releases have the same kernel but a different initrd, so they fail here | Flash the image from this guide's release and do not edit the boot partition. On a computer, `initrd.img` on the `boot` partition must be exactly 54,376,639 bytes |
| `File bzImage not found at default paths` | The loader did not find a USB drive with the boot files | Use a rear Type-A or the front Type-C port, replug the drive, and cold boot |
| The console freezes instead of entering Rest Mode | etaHEN or kstuff is running | Hold the power button until the console is off, then cold boot without them |
| It boots back to PS5 OS after the PS button | The button was pressed before the orange light was solid, or Supply Power to USB Ports is not set to Always | Check the setting, cold boot, and repeat. Wait for solid orange |
| Pulsing blue light after wake and no network | Seen once in Run 17 on a first wake; the cause was not isolated | Hold the power button until the console is off, then repeat from a cold boot. Mention it in your report |
| White light but no picture | The display path or the monitor. This is the most likely failure on a Slim | Try SSH first. If it answers, Linux is up; report that. Then try another monitor or TV, and HDCP both on and off in the PS5 settings (see [When you are done](#when-you-are-done)) |
| The loader refuses because carrier state is stale | The loader already ran in this PS5 OS boot | Cold boot. Do not send it again in the same boot |
| No SSH | The cable, a different DHCP address under Linux, or Linux did not start | Check the cable, wait another minute, and look for a new device in your router's client list. The image has no Wi-Fi |
| SSH warns that the host key has changed | Another system answered at that address before | Run `ssh-keygen -R PS5_IP` and connect again |
| The loader refuses a PS5 Pro | The Pro is not supported | Nothing was changed on the console. There is no workaround |
| The e820 check shows the old map | The Run 15 ELF was sent | Check the ELF hash, cold boot, and send the DMA ELF |

## Reporting

Open an issue in the
[porting repository](https://github.com/gzimbric/ps5-linux-porting/issues)
titled `DMA build test: CFI-xxxx` with your console model, and paste the
template below into it. Report failures as well as passes.
Remove IP addresses, MAC addresses, hostnames, and serial numbers before
posting.

```text
Console model: CFI-
Edition: disc / digital
Firmware: 11.60
Loader ELF SHA-256:
Image release tag:
ps5-ubuntu2404.img line from SHA256SUMS:
USB drive (make, size) and port:
Sent with: socat / nc / app name
Loader output showed "wake chain armed": yes / no / sender shows no output
Attempts (cold boots and sends before this result):
Woke with: controller PS button / console power button
Light after wake: white / pulsing blue / other
Picture on the monitor: yes / no (monitor make and model)
SSH: yes / no, about how long after the wake
Kernel (uname -r):
e820 line for 0x0000000001000000:
free -h total:
/proc/cmdline:
Storage error lines (or "none"):
I/O check: PASS / FAIL / not run, number of files
Read/write errors seen before with the old loader (exact text, if any):
Anything else:
```

## Limits

- This build is not a confirmed fix for the reported read/write errors. Runs
  18 and 19 did not reproduce them and had no A/B control: the Run 15 ELF was
  never run through the same check.
- Runs 18 and 19 were one boot each on the same console, a CFI-1115B original
  digital edition. Each I/O check wrote 12 GiB to the USB root in about 2
  minutes. There was no soak test, no M.2 or NVMe test, no GPU or gaming load,
  and no sustained Wi-Fi traffic. Run 19 is the only recorded boot of this ELF
  with a directly observed picture.
- Other models, including the disc edition and the Slim, have no recorded test
  with this ELF or with any CI image.
- The CI image is a rebuild of the tested profile, not the Run 16 control
  image. The [Run 16 Ubuntu USB guide](ubuntu2404-run16-usb.md) describes the
  control image. The CI image's root filesystem and image hash change with
  every build, and only build 3 has a recorded boot.
  `tools/check_ubuntu2404_usb.py` checks the exact Run 16 hashes, so its initrd
  check fails on a CI image. Do not use it as a pass or fail check here.
- Build 3 has two known image defects, seen in Run 19. The hostname is the ID
  of the CI build container. At boot, systemd logs an ordering cycle involving
  `ssh.socket` and `ps5-ssh-host-keys.service`; SSH still worked in Run 19.
- The image has no Wi-Fi driver or firmware. The
  [Wi-Fi guide](ubuntu2404-wifi.md) documents the Run 17 build for
  developers. There is no published way yet to get the firmware off your own
  console, so Wi-Fi is not part of this test. Never share that firmware.
