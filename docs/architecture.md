# Architecture

## Upstream boot path

The low-firmware `ps5-linux-loader` already provides the Linux-facing half of
the job: load a bzImage and initrd, build boot parameters and an e820 map,
configure the platform, and enter the kernel at `startup_64`.

The high-firmware problem is reaching that boot path with all CPUs outside the
hypervisor and with a usable physical address space.

## 11.60 wake-coupled design

The earlier 11.60 design separated the bypass from Linux takeover and resumed
GameOS userland between them. That produced useful diagnostics, but it differs
from the original loader. The current candidate lets the payload request rest
after preflight and keeps the operator-controlled wake, while coupling the
machine-state transition inside the wake path.

### Before rest mode

1. Load and validate the bzImage and initrd from USB.
2. Allocate the identity-map, Linux boot, wrapper, parameter, and retained-copy
   regions needed after S3.
3. Record page-granular physical copy lists so wake code does not depend on
   ordinary user mappings or file I/O.
4. Stage a position-independent wrapper in a validated executable kernel-text
   cave.
5. Hook the S3 hypervisor startup call, count down, and request rest mode.

### In the wake kernel context

1. Preserve the hook ABI and call the original hypervisor startup routine.
2. Discover the live GameOS VMCBs at runtime.
3. Disable nested paging on exactly 16 target VMCBs and verify every write.
4. Require `error=0 self=1 targets=16 written=16 verified=16`.
5. Restore the kernel resume gate and IST state.
6. Rebuild the identity page table and clone the live hypervisor high PML4
   entries required while the redirect executes.
7. Refresh the staged Linux shellcode, bzImage, initrd, and parameter blocks
   from the retained physical copies.
8. Validate and patch only the VMMCALL-specific VMEXIT handler.
9. Use the kernel SMP rendezvous path to issue the balanced VMMCALL on all CPUs.
10. Assign each arrival a compact stack slot, wait for the full barrier,
    atomically elect one bootstrap CPU, and park every other CPU.

A successful path does not return to GameOS userland. Returning is a failure
path and must leave a diagnosable status without pretending that Linux booted.

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
