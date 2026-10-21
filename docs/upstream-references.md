# Upstream references

The following revisions were checked through 2026-10-21. Historical branches
remain listed where they identify an exact tested artifact, but the active
forks use `main` as their default source branch.

| Project | Branch | Commit | Role |
|---|---|---|---|
| [pLabs5/pLinux5-NG](https://github.com/pLabs5/pLinux5-NG) | `master` | `3a7ea6f6c874773641b21d20f95f5df6f648ac40` | High-firmware Linux integration |
| [ps5-linux/ps5-linux-loader](https://github.com/ps5-linux/ps5-linux-loader) | `main` | `64637c177eaed277fb6ccce394cbb29dd047b893` | Established Linux boot path |
| [ps5-linux/ps5-linux-image](https://github.com/ps5-linux/ps5-linux-image) | `main` | `52db0a42302e4a6b5420a11fa00a84841ea5db56` | Upstream base for the custom Run 16 Ubuntu image |
| [PS5Dev/Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn) | `main` | `ea04f7132b837087f552c57261cb800481a3a910` | Upstream high-firmware bypass |
| [gzimbric/Byepervisor-Reborn](https://github.com/gzimbric/Byepervisor-Reborn) | `main` | `a1536c4e8c88536e7d7b676270603326efba098e` | Hardware-validated 11.60 bypass fork |
| [gzimbric/ps5-hv-bypass-porting](https://github.com/gzimbric/ps5-hv-bypass-porting) | `main` | `0a7f263d5cc4bb91984d0b00d68daaa0561a4542` | Bypass porting methods and evidence rules |
| [gzimbric/ps5-linux-loader](https://github.com/gzimbric/ps5-linux-loader) | `main` | `c70358f57e5a9d481fcde676454f4919e4e403b4` | Canonical 11.60 loader source, including the Run 15 baseline, DMA E820 and public bounded-loader tester guidance |
| [gzimbric/ps5-linux-image](https://github.com/gzimbric/ps5-linux-image) | `main` | `e82cefaac9f4c166b4b961ea64597bb5a2a1d1e3` | Current image source and exact source of the [`cachyos1160-k73-image-4`](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-4) tester prerelease. It keeps the Image 3 runtime path with the read-back-verified 65 C fan policy, narrow NetworkManager Polkit allowlist and pre-first-boot wait-online mask already present at `d9c4b31`, and adds the experimental MediaTek MT7921 path. CI-verified; no hardware boot recorded. The exact Image 3 release source remains the tag entry below. |
| [gzimbric/ps5-linux-image](https://github.com/gzimbric/ps5-linux-image/tree/ubuntu2404-1160-build-3) | `ubuntu2404-1160-build-3` (tag) | `ec8cd4e6d67d7dafb9bcee483fb34846eac549ca` | Exact source of the Ubuntu build 3 image that booted in Run 19 |
| [gzimbric/ps5-linux-image](https://github.com/gzimbric/ps5-linux-image/tree/cachyos1160-k73-image-2) | `cachyos1160-k73-image-2` (tag) | `346088a48f66eb956dafdec9de5085e73b2d44a5` | Exact CachyOS 7.3 image 2 public tester prerelease source; CI and release identities verified, with no identity-verified hardware boot recorded |
| [gzimbric/ps5-linux-image](https://github.com/gzimbric/ps5-linux-image/tree/cachyos1160-k73-image-3) | `cachyos1160-k73-image-3` (tag) | `16795eb85830dc32f712e44e9e0da28f7874b317` | Exact source of the Image 3 public tester prerelease; CI/release identities verified, followed by one identity-verified exact-image boot on the CFI-1115B |
| [gzimbric/ps5-linux-loader](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display) | `firmware-11.60-sonic-display` | `69657e6127db2ff9cc9ac2ad5e5aaebaa8019daf` | Historical Run 15 source provenance with the hash-pinned release check |
| [ps5-linux/ps5-linux-mwifiex](https://github.com/ps5-linux/ps5-linux-mwifiex) | `main` | `4aff9085530a3cdf7d5fbb124c006cc299ac3605` | PS5 IW620 driver patches used in Run 17 |
| [ps5-linux/ps5-linux-mwifiex](https://github.com/ps5-linux/ps5-linux-mwifiex) | `main` | `4bce848dd098bf74fbafd0078463da3d9f0d7f80` | IW620 patch-stack revision in the local image 3 hardware test, including its HE and TX follow-ups; the NXP driver base remains `a5fe4e1`; association worked after the separate stable-MAC NetworkManager live fix |
| [nxp-imx/mwifiex](https://github.com/nxp-imx/mwifiex) | `lf-6.18.2_1.0.0` | `a5fe4e194bf99315e349d81d77d6dfacec70757a` | NXP `mlan`/`moal` source patched for Run 17 |
| [rmuxnet/ps5-linux-patches-1](https://github.com/rmuxnet/ps5-linux-patches-1) | `meower` (default) | `36f173f39e5e76c00c4e366a7b909f33bc665ad5` | rmux's Linux 7.3 port of the PS5 patches and the PS5 CPU and GPU frequency drivers, used for the Run 21 kernel |
| [VivaLaVent/ps5-bazzite-deck](https://github.com/VivaLaVent/ps5-bazzite-deck/releases/tag/v1.0.3) | `v1.0.3` (tag) | `807d5bcaa834f574f6d927703ff95c1caffc96ba` | Source of the exact `ps5-btusb-quirks-fix.patch` asset rebuilt by image 3, asset SHA-256 `c01bdcc…`; its own paired-DualSense result is on firmware 13.60, while the separately rebuilt local image 3 has now paired a DualSense on 11.60 |
| [ublue-os/bazzite](https://github.com/ublue-os/bazzite/tree/2fab72cbc9a3257d80c607e173f22527aea3b39b) | source revision | `2fab72cbc9a3257d80c607e173f22527aea3b39b` | Source of the Bazzite base at OCI digest `sha256:96301a1520b5bb63db95640896300c10ae3b1fcf8bf10681af154514395e1634`; its effective BlueZ policy is mirrored by image 3 |
| [Valve Steam Offline Mode support](https://help.steampowered.com/en/faqs/view/0E18-319B-E34B-B2C8) | support article | checked 2026-10-20 | Boundary for testing offline use: first complete Steam setup and save the account/game state online, then test Offline Mode later; it does not make a fresh offline Gaming Mode bootstrap a supported path |
| [gzimbric/ps5-linux-loader](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-dma-e820) | `firmware-11.60-dma-e820` | `98925a2561ad43769a7a7445a0bd957b24e84073` | Exact historical source of the bounded Wi-Fi ELF that booted in Run 21 |

The local Linux research branch started from pLinux5-NG commit
`d5bd6b9f45c465e466e1e97083c9f162b94aad2c`. It is intentionally not published
as a working port and is now a superseded historical branch.

The active bounded diagnostics start from official loader commit
`64637c177eaed277fb6ccce394cbb29dd047b893`. The Stage 0 and Stage 1 hardware
passes were built from diagnostic source commit
`779af2f58aec61351278dd36cae9306e087ee873`. Their tested ELF hashes are
recorded in [the firmware status](11.60-status.md); the binaries and raw logs are
not redistributed here.

The later Sonic-style 11.60 source port remains based on that same official
loader lineage. Runs 11 through 13 were built from local commit
`5f922ead8859e2229d92e3d074e24fddf3f7932e`. Run 12 (`PRE=2`, `OP=0`)
reached authenticated Linux; the exact Run 13 (`PRE=3`, `OP=0`) ELF failed
twice. Run 14 was built from local commit
`87718a6565703079b96aa0b23a4996ec83308a4c` and passed authenticated Linux
with PRE3's runtime clear disabled while retaining `mp3_initialize(0)`. Run 15
was built from local commit `815b1fdc5c76088762e42ad0ad80b0099a54e60d` and
produced physical display output plus authenticated Linux with the full
Sonic-equivalent sequence. This repository records the commits and artifact
hashes as provenance but does not vendor the loader source or binaries.

## Published 11.60 loader source

The canonical loader source is published, without binaries, on
[`main`](https://github.com/gzimbric/ps5-linux-loader) in the
`gzimbric/ps5-linux-loader` fork. The historical
[`firmware-11.60-sonic-display`](https://github.com/gzimbric/ps5-linux-loader/tree/firmware-11.60-sonic-display)
branch preserves the exact Run 15 lineage on top of official commit
`64637c177eaed277fb6ccce394cbb29dd047b893`.

Before publication, the local commits were rewritten only to replace a
machine-local author address with a GitHub no-reply address. Commit messages,
dates, and file trees are unchanged, so each published commit has the same
tree hash as the local commit recorded in the evidence. The run-relevant
mappings are:

| Use | Local evidence commit | Published commit | Tree |
|---|---|---|---|
| Stage 2A | `a3c1d304daf0e297511846cc9aaab3ced8397954` | `656a9a9776277cddb88ae2a21cf1d99ad2884341` | identical |
| Run 10 | `c0233e2eeac10ac32982d2a20107b37c9cbda159` | `a776ba852a90df1d060c547d0b21a2737c333108` | identical |
| Runs 11-13 | `5f922ead8859e2229d92e3d074e24fddf3f7932e` | `b8e8243b2384ea42e06bffb142bb3c00f8c2b0c5` | identical |
| Run 14 | `87718a6565703079b96aa0b23a4996ec83308a4c` | `2c108c09a349ab95c015df93d268c1de04c826e6` | identical |
| Run 15 and release | `815b1fdc5c76088762e42ad0ad80b0099a54e60d` | `e0b7a2e9ac1fe6ec8de8f1883ba9470ad7ee690d` | `97e96d7d6fbec038812e0a1f9919b1d7c91a9410` |

To confirm the Run 15 source identity, check that
`git rev-parse e0b7a2e^{tree}` prints `97e96d7d6fbec038812e0a1f9919b1d7c91a9410`.
Commit `69657e6127db2ff9cc9ac2ad5e5aaebaa8019daf` adds the Run 15 diagnostic
gates as build defaults, invalidates stale objects when those gates change,
and makes `linux-1160-check` require the authenticated dumps and all three Run
15 artifact hashes. A clean build at that commit reproduced the tested outer
ELF, wake blob, and wake ELF byte for byte. Building requires the PS5 payload
SDK and authenticated 11.60 kernel-text and hypervisor dumps, which are not
distributed. See `PORTING_1160.md` on `main` for build details.

## Linux 7.3 patch set

The Linux 7.3.0 kernel used from Run 21 on is built from the work of rmux:
[rmuxnet/ps5-linux-patches-1](https://github.com/rmuxnet/ps5-linux-patches-1),
pinned at commit `36f173f39e5e76c00c4e366a7b909f33bc665ad5`. It ports the
ps5-linux PS5 patches to Linux 7.3 and adds rmux's PS5 CPU frequency
(`ps5_cpufreq`) and GPU frequency (`ps5_gpufreq`) drivers. The image build
applies `linux.patch` from that commit to mainline v7.3 and builds the two
frequency drivers as modules. The VCN firmware from the same commit is built
into the kernel. The patch is used as published, and its authorship and the
authorship of the drivers are unchanged.

The build profile is on the fork's default
[`main`](https://github.com/gzimbric/ps5-linux-image) branch. Image 2's exact
build source is preserved by the tag below. The build checks the patch, its
kernel config, and the VCN firmware by SHA-256 before using them. Nothing from
the patch set is copied into this repository.

Image 2 is pinned independently by tag `cachyos1160-k73-image-2` at
`346088a48f66eb956dafdec9de5085e73b2d44a5`. It uses rmux's `linux.patch` as
published at `36f173f`, then applies a separate local IW620 Bluetooth quirk
ordering follow-up with SHA-256
`54d7addbb4cd95c943f9a4485229ac5516ad08ebe0f4aa02fd72cf33298fa0a2`.
That follow-up is not represented as part of rmux's patch set. It restores
the IW620 quirks-table entry and post-lookup interface checks present in merged
[ps5-linux patch-set PR #35](https://github.com/ps5-linux/ps5-linux-patches/pull/35)
but absent from the pinned rmux 7.3 patch, while retaining rmux's 7.3 IW620
quirk flags; no identity-verified hardware result is recorded for that image.

[VivaLaVent's Bazzite Deck v1.0.3](https://github.com/VivaLaVent/ps5-bazzite-deck/releases/tag/v1.0.3)
independently reports a paired DualSense on a CFI-10xx PS5 running firmware
13.60 after the same core `btusb` correction. Its patch is not byte-identical
to the image 2 follow-up. That result corroborates the diagnosis, but it is
not an 11.60 hardware test of image 2. Workflow `39481460775` completed
successfully, and the
[public tester prerelease](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-2)
has one 1,943,471,712-byte image archive whose identity, together with the
12,582,912,000-byte raw image identity, was verified. No identity-verified
hardware boot of image 2 is recorded.

The local image 3 hardware build was assembled from
`f7d6fbd9d630cddaceb83f3b861869d4453af8ca`. The public prerelease was built
from `16795eb85830dc32f712e44e9e0da28f7874b317`; one identity-verified boot of
its exact artifact has now passed HDMI, wired SSH, Plasma Wi-Fi,
internal-Bluetooth DualSense input, startup scaling and both session directions.
Image 3 keeps rmux's `36f173f` Linux 7.3 base and uses package
identity `linux-ps5 7.3.0-3`. For Bluetooth it consumes the exact
`ps5-btusb-quirks-fix.patch` release asset attached to Bazzite Deck v1.0.3,
verified at SHA-256
`c01bdcc134f25a86825f2824d12a82da02db18e7b1940db722223b0c4611eed8`,
then rebuilds that source in its own kernel. Bazzite's prebuilt `btusb.ko` is
not part of this project and must not be copied into this image. The external
13.60 pairing report supplied the source lead. The exact local image 3 then
supplied the 11.60 result: the internal controller registered and a wireless
DualSense paired, bonded, trusted and connected, with gamepad, motion and
touchpad input and no USB DualSense present.

The matching userspace reference is the Bazzite base at OCI digest
`sha256:96301a1520b5bb63db95640896300c10ae3b1fcf8bf10681af154514395e1634`,
built from [`ublue-os/bazzite` revision `2fab72c`](https://github.com/ublue-os/bazzite/tree/2fab72cbc9a3257d80c607e173f22527aea3b39b).
Image 3 mirrors its effective Bluetooth settings:
`AlwaysPairable=true`, `PairableTimeout=0`, `ControllerMode=dual`,
`Privacy=device`, `JustWorksRepairing=always`, `AutoEnable=true`, and
`UserspaceHID=true`. It relies on the pairing agent supplied by KDE or
`bluetoothctl` and the `uhid`/`hid-playstation` path; it neither installs a
custom pairing daemon nor preloads `hidp`. Cold-boot reconnect and a full
Wi-Fi/Bluetooth coexistence soak remain pending.

The same candidate pins `ps5-linux-mwifiex` at
`4bce848dd098bf74fbafd0078463da3d9f0d7f80`, then applies the HE and TX
follow-ups. A live test showed that NetworkManager also needs
`wifi.scan-rand-mac-address=no`, `wifi.cloned-mac-address=permanent` and
`wifi.powersave=2` on IW620; with those settings, the normal Plasma menu passed
WPA3 association, DHCP and HTTPS. Current source carries that exact policy.
The published Image 3 artifact sends legacy fan servo pattern `3` before
guarded GPU-then-CPU scaling at startup. That request does not force or measure
maximum RPM; Linux exposes no RPM/tach reading, and the tested CFI-1115B
retained an 86 °C autoservo target. Its tester guide applies and verifies
65 °C after every boot, within a documented public range of 40-80 °C.
`/boot/efi/disable-ps5-performance` remains a persistent performance-policy
opt-out, and unsupported Linux sleep targets are masked.

For the session handoff, the working distinction is between `-steamos` and
`-steamos3`. The image launches `steam -steamos -gamepadui`; this enables
Steam's distro-neutral selector fallback without enabling SteamOS 3 atomic-
update polling. On hardware, Steam deliberately ran
`sudo /usr/bin/steamos-session-select plasma` through that fallback and
switched from Gamescope to Plasma/KWin. The earlier system-bus listener is
removed. A fresh image starts in Plasma so networking can be configured before
the first online Gaming Mode bootstrap; Valve's Offline Mode guidance applies
after credentials and local game state have been saved.

Hosted workflow `39521098451` successfully built, verified, compressed and
uploaded one `.img.xz` from `16795eb`. The
[`cachyos1160-k73-image-3` public prerelease](https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-3)
was published at `2026-10-21T00:48:20Z`. Its 1,943,937,164-byte archive has
SHA-256
`9e224aeb607ba050dd520ce32d50989d27013f7da2889ce7ed1ce247fea71e3c`;
its 12,582,912,000-byte raw image has SHA-256
`25a0ef68a85dbe6d976b5a97faaa323b64c4efbe1b220003772f25a264eb34a8`.
It contains the later Wi-Fi, Plasma-first, launcher and return-selector changes,
and one exact-image hardware test has passed those paths. The separate local
hardware image has raw
SHA-256
`5a904e02f6a2908be91054b7b73ebf6f891fece0edc1a88f2f9d60264d7556d4`.
The [image 3 tester guide](cachyos1160-k73-image-3-tester-guide.md) keeps these
identities and evidence boundaries separate.

The Run 21 image boots only with a bounded loader build, because its boot
files are not the sizes the earlier 11.60 loaders accept. Those targets are
now on loader `main`. The exact bounded Wi-Fi artifact used in Run 21 was
built at historical commit `98925a2`, and current `main` reproduces its hash.
It and the unbooted non-Wi-Fi A/B build are in the
[`firmware-11.60-dma-e820-bounded-run21` tester prerelease](https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21).
See the historical
[image 2 tester guide](cachyos1160-k73-image-2-tester-guide.md), the current
[image 3 tester guide](cachyos1160-k73-image-3-tester-guide.md), and
[Run 21 evidence](../evidence/11.60-cachyos-k73-run-21.md) for their separate
scope and evidence limits.

## Published Run 16 image source

Run 16 did not use the stock Ubuntu image from the upstream image builder. Its
custom Ubuntu 24.04 source is published on the
[`ubuntu2404-1160-tested`](https://github.com/gzimbric/ps5-linux-image/tree/ubuntu2404-1160-tested)
branch of the `gzimbric/ps5-linux-image` fork, based on upstream commit
`52db0a42302e4a6b5420a11fa00a84841ea5db56`.

The verified immutable source pin is:

```text
commit: 376d8da75e40930f5f687857172eedc60b3da9ba
tree:   47268dfca7b903d2fd6c4ee89cae8db67d0f24c0
```

The source branch contains no disk image or boot binaries. See the
[Run 16 Ubuntu USB guide](ubuntu2404-run16-usb.md) for the exact media
identities and the distinction between byte identity and loader compatibility.
The exact Run 16 bzImage came from a separate deterministic Run 15 kernel build
with fixed KBUILD user and host plus controlled date behavior. The image branch
now integrates that recipe. The Ubuntu USB guide records the separate kernel
and image-assembly validation results; it does not claim a one-command build
from empty caches.

The upstream control-flow comparison uses these source files directly:

- [`source/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/source/main.c)
  prepares the resume blob, arms the firmware-specific HV path, requests rest,
  and does not launch a second post-wake payload;
- [`shellcode_kernel/main.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/main.c)
  prepares Linux and invokes the all-core VMMCALL rendezvous in the resume
  context; and
- [`shellcode_kernel/boot_linux.c`](https://github.com/ps5-linux/ps5-linux-loader/blob/main/shellcode_kernel/boot_linux.c)
  installs the identity map and HV shellcode before staging the Linux inputs.
