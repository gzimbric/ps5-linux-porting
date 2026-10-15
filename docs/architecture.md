# Architecture

## Upstream boot path

The low-firmware `ps5-linux-loader` already provides the Linux-facing half of
the job: load a bzImage and initrd, build boot parameters and an e820 map,
configure the platform, and enter the kernel at `startup_64`.

The high-firmware problem is reaching that boot path with all CPUs outside the
hypervisor and with a usable physical address space.

## 11.60 reconstruction design

The pLinux-derived wake wrapper is a superseded experiment. It coupled work
into one wake context by redirecting the MP-startup hook into a new staging
wrapper, but it replaced the original memory contract and component boundary.
Sonic's known-working 13.60 ELF instead keeps the AP/VMCB strike and the kernel
Linux wake shellcode as distinct components inside one outer payload. The
11.60 reconstruction follows that official-loader shape. See
[Sonic 13.60 binary reference](sonic-13.60-reference.md).

### Validated prefix

On 2026-10-15, the official-loader-derived Stage 0, Stage 1A, Stage 1B, and
Stage 2A diagnostics passed on a regular 11.60 console. Stage 0 read both Linux images
without page-table writes. Stage 1A preflighted the source and destination
ranges, installed and verified the official-style syscore alias PTEs, then
reversed and verified every journaled write.

Stage 1B wired a 16 KiB data canary and three page-table allocations, installed
four NX leaves in a new syscore subtree, mirrored that exact PML4 entry into the
current pmap, and matched every byte through the target virtual address. All
four leaf Accessed bits were observed before both roots were restored and
verified. This proves current-context CPU traversal of the shared subtree; it
does not prove PID-1-context access, TLB shootdown, executable mapping, or
post-rollback translation eviction.

Stage 2A then used the official `prepare_resume` contract to publish the exact
240-byte inert wake blob RX at `0xffff800000000000` in PID 1. It verified the
`0x98` argument block, the four contiguous leaf PTEs, and exact blob bytes, then
held every backing page. It did not execute the mapping or link any hook, HV,
rest-mode, or Linux-loading path. GameOS remained responsive during the hold;
the deliberately retained mappings still require a cold reboot for cleanup.

### Intended final component split

1. Before rest, userland loads the Linux inputs and installs their kernel
   aliases using the now data-read-through-validated official-loader mapping
   layout; executable wake-shellcode staging is now validated as a separate
   boundary.
2. A separately installed kernel wake shellcode owns Linux staging, the live
   HV-exit patch, the identity map, the all-core rendezvous, and Linux entry.
3. The root-0 AP payload owns only dynamic VMCB discovery and NPT disable on
   exactly 16 GameOS VMCBs.
4. The S3/GP resume redirect preserves the original startup flow and enters the
   kernel wake shellcode; it is not a replacement staging wrapper.

The final successful path will not return to GameOS userland. Until then, each
diagnostic must be bounded, independently audited, and prove restoration.

## Why timing is part of the port

The bypass is not merely a prerequisite bit that can always be consumed later.
Resume code runs while CPU, hypervisor, page-table, and retained-memory state
are in a narrow, known relationship. The original loader exploits that window
by continuing directly from bypass completion into the Linux handoff. Delaying
the takeover until a separate payload can change those assumptions even when
the bypass counters still look valid.

This ordering is visible both in the upstream source and in the supplied 13.60
comparison ELF: the resume entry patches and stages the HV/Linux path, then
invokes the all-core rendezvous from that same execution context.

The ordering alone is not enough. The known-working binary also preserves the
official loader's pre-suspend page aliases and `prepare_resume` shellcode, while
the superseded 11.60 wrapper replaced both. The next port must reproduce that
memory contract and division of responsibilities, not merely run all steps
during the same rest/wake cycle.

## Why the VMMCALL-specific handler matters

An earlier experiment patched the general return path after `VMRUN`. Any
unrelated timer, MSR, RDTSC, or other VM exit could then divert one CPU into
the Linux shellcode before the remaining CPUs reached the rendezvous. The
first CPU waited forever at the 16-core barrier, which matched the white frozen
home screen.

The 11.60 path now targets the VMMCALL-specific handler at physical address
`0x62847551`. The balanced kernel wrapper is at ktext offset `0xC88100`.

## Address domains

Keep these values visibly separate:

- kernel text offset;
- runtime kernel virtual address;
- kernel direct-map virtual address;
- hypervisor physical address;
- identity-mapped physical address after the CR3 switch.

The transition begins in a slid hypervisor mapping. A relative jump to a cave
in that same mapping remains valid before the CR3 switch. An absolute physical
jump does not become valid until after the identity CR3 is active.

## CPU invariants

- Do not let one application processor leave virtualization while GameOS
  continues on its peers.
- The setup and teardown callbacks for the SMP rendezvous must be valid under
  the active CFI policy.
- The VMMCALL wrapper must leave the stack balanced.
- Every CPU needs a separate downward-growing stack.
- The Linux barrier count must match the hardware topology used by the loader.
- Only one bootstrap CPU may proceed into platform setup and `startup_64`.
