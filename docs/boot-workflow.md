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

## Current no-UART display ladder

1. Preserve the Run 12 carrier, current boot-media hashes, and `OP=0`.
2. Treat authenticated wired SSH as the Linux pass gate. Do not use LED color,
   ping, DRM connector state, or modeset return as a substitute.
3. Run 12 `PRE=2` is the rollback baseline. It includes VBIOS copy,
   transmitter control, and the timed wait.
4. The exact Run 13 `PRE=3` build is rejected after two no-SSH attempts; it
   added both a wake-time buffer clear and `mp3_initialize(0)`.
5. The next candidate suppresses only the redundant clear while retaining the
   initializer call.
6. After an authenticated pass, add MP3 command 21 and command 22 separately.
7. Do not execute a 29-table entry until the complete preamble passes.

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
