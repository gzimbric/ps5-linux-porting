# Debugging the final handoff

The final handoff crosses several protection and address-space boundaries at
once. Logging from userland naturally stops, so each boundary needs an
observable side effect that does not depend on Linux already working.

## Boundary A: live handler write

Prove that the expected handler bytes were read, the relative jump was
encoded against physical addresses correctly, the patch read back exactly,
and instruction visibility was handled before issuing VMMCALL.

## Boundary B: transition cave entry

First use a passthrough cave that replays the displaced instructions and
returns to the stock path. This is more informative than loading CR3 on the
first attempt because it separates redirect correctness from address-space
transition correctness.

## Boundary C: identity CR3

Once passthrough returns reliably, make the smallest possible transition-cave
test. The code after `mov cr3` must use only identity-valid addresses and must
not depend on a stack or data pointer from the old virtual mapping.

## Boundary D: staged shellcode entry

Verify that the entry point is position independent, that any embedded
addresses are physical or identity-valid, and that the staging copy includes
all referenced sections. A raw binary may not preserve assumptions made by a
normal linked image.

## Boundary E: all-core barrier

Confirm the CPU identifier source, expected CPU count, stack allocation, and
atomic storage location under the identity map. A wrong count looks exactly
like a permanent freeze.

## Boundary F: Linux entry

Only after the prior boundaries are proven should the investigation move to
the boot parameters, e820 map, ACPI pointer, VRAM configuration, IOMMU state,
and `startup_64` calling convention.

## Evidence rule

A marker before an instruction proves only that execution reached the marker.
A returned passthrough proves the complete round trip. Prefer round-trip tests
where the hardware allows them.
