# Security and hardware safety

This project documents experimental low-level code. A wrong address, page
table change, VMEXIT redirect, or CPU barrier can panic or hang a console.

Do not treat a firmware-adjacent value as interchangeable. Validate live bytes
and page properties before a write. Prefer a reversible diagnostic with exact
readback and restoration before an irreversible takeover attempt.

Do not report Sony secrets, console keys, decrypted firmware, or private user
data in a public issue. A bug in this repository's own tooling can be reported
through GitHub's private vulnerability reporting if available.
