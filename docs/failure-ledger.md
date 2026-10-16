# Failure ledger

This ledger records discarded designs as well as successful diagnostics. Its
purpose is to prevent the same crash from being rediscovered under a new file
name.

## Single-core application-processor handoff

**Idea:** Send one AP into the Linux shellcode and leave the bootstrap CPU and
remaining APs in GameOS.

**Result:** Rejected.

**Reason:** The Linux shellcode expects a coordinated machine takeover. One
core leaving virtualization while the rest remain active can deadlock at the
barrier or corrupt shared machine state.

## General post-VMRUN patch

**Idea:** Patch the common return point after the hypervisor's main `VMRUN`.

**Observed behavior:** White frozen home screen.

**Reason:** The location runs for many kinds of VM exits. An unrelated exit can
send one CPU into the Linux barrier before the SMP rendezvous moves the other
15 CPUs.

**Replacement:** Patch only the VMMCALL-specific handler.

## Data cave used as executable code

**Idea:** Place the kernel redirect trampoline in the known data cave.

**Result:** Rejected.

**Reason:** Writable data is not automatically executable. A ktext-relative
address does not change the underlying page permissions.

**Replacement:** Use a dump-backed ktext NOP cave and validate its live PDE and
contents before every run.

## Direct-map execution assumption

**Idea:** Execute the same bytes through the kernel direct map.

**Result:** Rejected on 11.60.

**Reason:** The relevant execute-only behavior and aliases did not provide the
needed executable view. The dedicated ktext mapping is the validated path.

## Automatic rest and wake sequence

**Idea:** Let an earlier combined test automate both the rest request and the
wake/testing sequence.

**Observed behavior:** Repeated crashes and ambiguous state.

**Replacement:** Split preparation, rest, operator wake, status, and Linux
diagnostics into explicit observable stages.

This result rejected an opaque automated sequence; it did not prove that Linux
takeover should be delayed until a second userland payload. The current
official-loader reconstruction preserves a coupled final wake path but brings
its inputs and component boundaries up through returning diagnostics first.

## Split post-wake Linux takeover

**Idea:** Complete and verify Byepervisor during wake, return to GameOS
userland, then launch a separate Linux payload.

**Observed behavior:** The split flow proved the exact 16-of-16 strike and many
reversible diagnostics. The full attempt reached `Linux images staged
successfully` and then became silent.

**Current assessment:** Valuable as a diagnostic architecture, but not yet a
valid final boot architecture. It diverges from the original loader's coupled
wake-time handoff and may lose assumptions about CPU, hypervisor, page-table,
or retained-memory state.

**Replacement under test:** Reconstruct the official/Sonic component split:
preinstall the Linux aliases, keep the AP payload limited to VMCB/NPT work, and
perform Linux staging and handoff in a separate kernel wake shellcode. The
reversible alias-construction stage has now passed on 11.60.

## HDMI Device Link

**Idea:** Treat HDMI wake behavior as the cause of the takeover crash.

**Result:** Not the root cause.

Disabling HDMI Device Link removes an external wake variable and matches
upstream guidance, but the final takeover still failed afterward.

## Stock all-core VMMCALL

**Question:** Is the SMP callback, stack discipline, or ordinary VMMCALL path
itself broken?

**Result:** Pass.

The balanced VMMCALL wrapper ran on all cores through the stock handler and
returned. This removes the ordinary rendezvous and VMMCALL path from the
leading suspect list.

## Full staging followed by silence

**Observed behavior:** The loader validated the bypass and handler, copied the
bzImage and initrd, and reported `Linux images staged successfully`. No later
marker appeared and the console stopped responding.

**Conclusion:** The input image and large file copies are no longer the first
failure. The next boundary to isolate is the reversible handler redirect. A
full Linux attempt gives too little information until that diagnostic passes.

## Assumption that Sonic-style aliases were not viable on 11.60

**Question:** Does the official loader's per-page syscore alias contract fail
on firmware 11.60 before the wake path is involved?

**Result:** Rejected for page-table construction and bounded data read-through.

A bounded official-loader-derived diagnostic preflighted 2,534 logical 16 KiB
source pages, installed and verified 10,136 leaf PTEs, restored and verified
10,158 journaled writes, verified every target absent, then released 22
temporary table-page mappings. It returned normally and the UI remained
responsive.

The follow-up test wired a 16 KiB data canary and all table backing, mirrored
the exact syscore subtree into the current pmap, matched the full canary through
the target virtual address, observed all four hardware Accessed bits, and
restored both roots. It deliberately did not test PID-1 execution, TLB
shootdown, executable mappings, or wake-shellcode staging.

**Remaining boundary:** Stage executable wake-shellcode pages without arming
the resume hook, rest mode, or HV path, and verify the installation can be
fully reversed.

## Direct resume-chain execution from the PID-1 alias

**Question:** Can the validated 11.60 #DB/S3 carrier return directly to the
240-byte inert page mapped only at `0xffff800000000000` in PID 1?

**Result:** Rejected on hardware.

Stage 2B-3 used the exact `startup_mp` resume boundary without fetching the
alias. It passed after one Rest Mode cycle, verified the expected resume RIP and
absence of foreign CPU frames, restored the stock #DB gate, cleared DR7,
restored all 16 IST6 entries and four carrier-cave pages, rolled back the alias,
and returned to responsive GameOS.

After a cold reboot and fresh exploit, audited Stage 2B-4
(`b997f822684c99f1156d45149be3401d76046812cd2270da7d9ac9ee30d099f1`)
added one direct `RET` target at the PID-1 alias. It armed normally and entered
Rest Mode, but wake stopped with a continuously pulsing blue light and no PASS
marker. No HV or Linux path was linked.

**Conclusion:** The direct alias fetch is the isolated failed boundary. Do not
retry it. The next diagnostic must match the supplied Sonic 13.60 carrier more
closely: copy the staged entry into executable kernel text under the validated
supervisor carrier, then transfer control to that copy.

That replacement architecture was subsequently integrated and reached
authenticated Linux userspace. The failed direct-alias design remains retired.

## Treating Linux DRM state as visible HDMI proof

**Idea:** Consider `amdgpu` binding, a connected DRM connector, EDID readback,
or a successful modeset return sufficient evidence that display output works.

**Result:** Rejected on hardware.

Runs 10, 12, and 14 reached authenticated Linux userspace. Run 12 reported the
connector connected and completed a direct 1080p60, 8-bpc, full-RGB modeset,
yet the physical monitor reported no signal throughout; Run 14 again reported
connected DRM state while the monitor remained at no signal. Linux boot and
visible HDMI therefore remain separate pass criteria.

**Resolution:** The missing precondition was Sonic's pre-Linux MP3 command and
display-table sequence, not the Linux graphics stack. Run 15 enabled it and
produced physical output with the same kernel, initrd, and command line.

## Enabling the complete Sonic display preamble at once

**Idea:** Enable VBIOS copy, transmitter setup, MP3 initialization, MP3
commands 21/22, and no table calls in one `PRE=5`, `OP=0` run.

**Observed behavior:** Run 11 remained in a blue-pulsing state and never
exposed SSH.

**Replacement:** Retain the same Linux carrier and bisect the preamble while
keeping `OP=0`. Run 12 established PRE2 as an authenticated pass.

## PRE3 with wake-time MP3 buffer clearing

**Idea:** Add both a 10,252-byte runtime clear of the retained MP3 work area
and `mp3_initialize(0)` to the passing PRE2 boundary.

**Observed behavior:** The exact Run 13 ELF failed twice. Both attempts reached
a steady white light without HDMI and kept TCP port 22 down for more than three
minutes.

**Follow-up:** Run 14 suppressed only that clear, retained the direct
`mp3_initialize(0)` call, and reached authenticated Linux userspace. The
console reached a white light while the monitor remained at no signal.

**Conclusion:** The mapped 11.60 initializer works in the wake context. Within
the controlled Run 12/13/14 sequence, the Run 13 regression is isolated to the
redundant 10,252-byte clear and its retained-alias writes. The complete page was
already zeroed before suspend, Sonic relies on pre-zeroed static storage, and
Sonic performs no equivalent runtime clear. Exact-11.60 production must omit
the clear. Do not skip MP3 initialization or promote Run 13 to a working boot;
advance next to command 21 only.
