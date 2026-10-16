# 11.60 research workflow

This workflow describes the state machine. It does not provide a prebuilt
payload.

## Clean starting state

1. Fully reboot the console.
2. Connect the Linux USB drive directly.
3. Set Rest Mode USB power to `Always`.
4. Disable HDMI Device Link.
5. Run only the normal exploit and direct ELF loader needed for the test.
6. Do not preload a payload manager, kstuff, etaHEN, or another persistent
   payload unless the specific experiment is designed to coexist with it.
7. Start log capture before sending the first research payload.

## Official-loader bounded reconstruction

1. Start from a clean boot and use the official-loader-derived Stage 0 image
   reader only.
2. Require the exact Stage 0 PASS marker and a responsive UI.
3. Cold-reboot and obtain a fresh jailbreak before any later stage.
4. Run only the independently reviewed next bounded stage.
5. Require every advertised checkpoint, verified rollback, and a responsive UI.
6. Stop on any missing checkpoint, refusal, freeze, reboot, or rollback failure.

Stage 0, the reversible Stage 1A alias transaction, and the Stage 1B data-alias
read-through canary passed on 2026-10-15. Later Stage 2A/2B diagnostics and the
Sonic-style copy-to-kernel-text carrier also progressed to authenticated Linux
boots. This section remains the historical safe path that established those
boundaries; it is not the current display-test ladder.

The earlier pLinux-derived wake-coupled candidate is superseded and should not
be rerun under a new filename.

## Historical returning-diagnostic ladder

Run one diagnostic per clean boot and jailbreak state. A clean bypass state is
additionally required once a stage actually exercises the bypass. The intended
order is:

1. bounded loader-only USB and file validation (**passed**);
2. reversible syscore alias construction (**passed**);
3. data-only alias read-through through an exact mirrored subtree (**passed**);
4. high-firmware wake-shellcode staging without arming (**passed**);
5. ktext cave and resume-redirect preflight (**passed**);
6. AP/VMCB strike integration (**passed**);
7. Sonic-style copy-to-ktext, HV transition, and coupled Linux takeover
   (**passed with authenticated Linux userspace**).

Each returning diagnostic must report restoration of every object it actually
changed. Gate, IST, cave, or hypervisor-byte restoration is required only for
a stage that touches those objects. The final candidate is different: success
continues to Linux and therefore cannot produce a GameOS userland PASS message.

## Current no-UART display workflow

1. Use the exact Run 15 build (`PRE=5`, `OP=29`, clear disabled) and the
   current boot-media hashes. It is the hardware-verified Linux and physical
   display baseline.
2. Treat authenticated wired SSH as the Linux pass gate and direct observation
   of physical output as the display pass gate. Do not use LED color, ping,
   DRM connector state, or modeset return as a substitute for either.
3. Boot GameOS, run the exploit, send the hash-locked ELF, let the console
   enter Rest Mode automatically, wait for a steady orange light, then wake it
   once. A successful run turns the light white, shows video, and exposes SSH
   within about a minute.
4. Keep the runtime MP3 buffer clear disabled. The exact Run 13 build that
   enabled it is rejected after two no-SSH attempts; Run 14 isolated the
   failure to that clear.
5. Preserve Sonic's response-first MP3 buffer layout and the outer-call /
   leaf-tail-jump display dispatcher; Run 15 adopted both.
6. Run 14 (`PRE=3`, `OP=0`, clear disabled) remains the headless rollback
   control if a later change regresses Linux boot.
7. Split MP3 commands 21/22 or the 29-table into separate gates only to
   isolate a later regression or to find the minimal necessary subset.

Physical UART is not available. A USB serial adapter in a PS5 host port does
not expose the pre-Linux MMIO UART. Use retained memory breadcrumbs for a
failure before networking, and keep every candidate hash-locked.

## After a failure

- Save the complete log and payload hash.
- Record the last marker and console behavior.
- Fully reboot. Do not assume a failed handler or page-table experiment left a
  reusable state.
- Change one boundary for the next run.
- Never interpret silence after a marker as proof that the next operation ran.

Use [the run report template](../templates/run-report.md) for every console
test.
