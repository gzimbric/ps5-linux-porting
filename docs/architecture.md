# Architecture

## Upstream boot path

The low-firmware `ps5-linux-loader` already provides the Linux-facing half of
the job: load a bzImage and initrd, build boot parameters and an e820 map,
configure the platform, and enter the kernel at `startup_64`.

The high-firmware problem is reaching that boot path with all CPUs outside the
hypervisor and with a usable physical address space.

## 11.60 two-stage design

The current 11.60 design separates the bypass from the Linux takeover.

### Stage 1: establish and verify the bypass

1. Prepare a resume hook using the hardware-validated 11.60 Byepervisor path.
2. Enter rest mode manually and wake normally.
3. Discover the live GameOS VMCBs at runtime.
4. Disable nested paging on exactly 16 target VMCBs.
5. Verify all 16 writes and restore the kernel hook.
6. Leave a small status record for the Linux payload.

The accepted success shape is:

```text
error=0 self=1 targets=16 written=16 verified=16
```

### Stage 2: take over all CPUs

1. Refuse to continue unless the Stage 1 status is exact.
2. Load the bzImage and initrd from USB.
3. Validate the executable kernel-text cave and VMMCALL handler identity.
4. Build an identity page table and stage the Linux boot shellcode.
5. Redirect only the VMMCALL-specific VMEXIT handler to a nearby transition
   cave.
6. Use the kernel SMP rendezvous path to issue a balanced VMMCALL on all CPUs.
7. In the transition cave, load the identity CR3 and jump to the staged
   hypervisor shellcode.
8. Give each CPU a distinct stack, wait until all CPUs have arrived, park the
   secondary CPUs, and let CPU 0 enter Linux.

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
