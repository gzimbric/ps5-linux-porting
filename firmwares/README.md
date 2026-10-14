# Firmware manifests

Each JSON manifest records what has and has not been observed on hardware.
`true` means a dedicated test passed. `false` means it failed or was not
observed. The adjacent `notes` fields provide the distinction.

Run `python3 tools/validate_manifests.py` after editing a manifest.
