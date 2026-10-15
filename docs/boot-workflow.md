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

Stage 0 and the reversible Stage 1 alias transaction passed on 2026-10-15. The
next authorized design boundary is alias read-through with controlled
translation-cache handling. Do not skip to `prepare_resume`, HV code, rest
mode, or the ordinary loader.

The earlier pLinux-derived wake-coupled candidate is superseded and should not
be rerun under a new filename.

## Returning diagnostic stage

Run one diagnostic per clean boot and jailbreak state. A clean bypass state is
additionally required once a stage actually exercises the bypass. The intended
order is:

1. bounded loader-only USB and file validation (**passed**);
2. reversible syscore alias construction (**passed**);
3. alias read-through with translation-cache handling;
4. high-firmware wake-shellcode staging without arming;
5. ktext cave and resume-redirect preflight;
6. AP/VMCB strike integration;
7. reversible HV-handler passthrough;
8. full coupled wake-time Linux takeover only after all prior steps pass.

Each returning diagnostic must report restoration of every object it actually
changed. Gate, IST, cave, or hypervisor-byte restoration is required only for
a stage that touches those objects. The final candidate is different: success
continues to Linux and therefore cannot produce a GameOS userland PASS message.

## After a failure

- Save the complete log and payload hash.
- Record the last marker and console behavior.
- Fully reboot. Do not assume a failed handler or page-table experiment left a
  reusable state.
- Change one boundary for the next run.
- Never interpret silence after a marker as proof that the next operation ran.

Use [the run report template](../templates/run-report.md) for every console
test.
