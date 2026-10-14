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

## Bypass stage

1. Run the reviewed 11.60 Byepervisor prepare payload.
2. Confirm that the preparation marker and hook readback are valid.
3. Enter rest mode manually.
4. Wait until the rest transition completes, then wake once.
5. Run the matching status payload.
6. Require `err=0`, `self=1`, `tgt=16`, `wr=16`, and `ver=16`.
7. Require confirmation that the resume hook was restored.

Do not continue if any count is different. Reboot before another attempt.

## Linux diagnostic stage

Run one diagnostic per clean bypass state. The intended order is:

1. loader-only USB and file validation;
2. ktext cave preflight;
3. hook-only self-test;
4. resume redirect self-test;
5. all-core no-op rendezvous;
6. all-core stock VMMCALL;
7. reversible HV-handler passthrough;
8. final takeover only after all prior steps pass.

Each returning diagnostic must report restoration of the gate, IST, cave, and
any hypervisor bytes it changed.

## After a failure

- Save the complete log and payload hash.
- Record the last marker and console behavior.
- Fully reboot. Do not assume a failed handler or page-table experiment left a
  reusable state.
- Change one boundary for the next run.
- Never interpret silence after a marker as proof that the next operation ran.

Use [the run report template](../templates/run-report.md) for every console
test.
