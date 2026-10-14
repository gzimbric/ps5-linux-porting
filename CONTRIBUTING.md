# Contributing

Contributions should improve the evidence, not just add another guessed value.

For a firmware result, include:

1. console model and firmware;
2. exact upstream commit and local source commit;
3. payload hash if a binary was tested privately;
4. prerequisites and prior payload state;
5. last confirmed log marker;
6. whether the console returned, froze, rebooted, or panicked;
7. every write performed and whether it was restored;
8. the narrow conclusion supported by the result.

Do not attach proprietary dumps, keys, decrypted firmware, raw private logs,
disk images, or prebuilt crash payloads. Use `templates/run-report.md` and run
`make check` before opening a pull request.
