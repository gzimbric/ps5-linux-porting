# Firmware manifests

Each JSON manifest records what has and has not been observed on hardware.
Read each Boolean as the exact proposition named by its key. A key ending in
`present_in_successful_path` records only that the component was present in a
successful containing run, not that it was separately isolated. The adjacent
`notes` fields record the observation boundary and unresolved alternatives.

Run `python3 tools/validate_manifests.py` after editing a manifest.
