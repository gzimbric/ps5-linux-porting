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

**Result:** Rejected for page-table construction.

A bounded official-loader-derived diagnostic preflighted 2,534 logical 16 KiB
source pages, installed and verified 10,136 leaf PTEs, restored and verified
10,158 journaled writes, verified every target absent, then released 22
temporary table-page mappings. It returned normally and the UI remained
responsive.

**Remaining boundary:** The test verified the page tables and physical backing
but deliberately did not read through the new syscore virtual aliases. Alias
read-through with explicit translation-cache handling is the next returning
diagnostic; `prepare_resume` remains premature until it passes.
