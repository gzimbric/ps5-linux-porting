#!/usr/bin/env python3
"""Read-only verification of the USB boot files used for Ubuntu Run 16."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


READ_SIZE = 1024 * 1024


@dataclass(frozen=True)
class FileIdentity:
    size: int
    sha256: str


RUN16_BOOT_FILES: Mapping[str, FileIdentity] = {
    "bzImage": FileIdentity(
        12_702_720,
        "11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde",
    ),
    "initrd.img": FileIdentity(
        54_376_639,
        "2eef0352879e091083450b799c75514a450f4110cbc747f640962fdde2dc06c8",
    ),
    "cmdline.txt": FileIdentity(
        121,
        "6b3c09112fe049d3cbeada65fb3c82bb0f5fcaddce6c0709051df3d9f5a79f6d",
    ),
    "vram.txt": FileIdentity(
        11,
        "bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0",
    ),
    "kexec.sh": FileIdentity(
        136,
        "0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52",
    ),
}

RUN16_ROOT_INITRD = FileIdentity(
    50_803_483,
    "996bc02a64404bc84d06c8df0c4143b66932d8af8549f39c82c71677fdec58c9",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(READ_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected: FileIdentity) -> list[str]:
    errors: list[str] = []
    try:
        stat = path.stat()
    except OSError as exc:
        return [f"{path}: cannot read file metadata: {exc}"]

    if not path.is_file():
        return [f"{path}: not a regular file"]
    if stat.st_size != expected.size:
        errors.append(
            f"{path}: size {stat.st_size}, expected {expected.size}"
        )
    try:
        digest = sha256_file(path)
    except OSError as exc:
        errors.append(f"{path}: cannot read file contents: {exc}")
    else:
        if digest != expected.sha256:
            errors.append(
                f"{path}: SHA-256 {digest}, expected {expected.sha256}"
            )
    return errors


def verify_boot_directory(
    efi_root: Path,
    expected_files: Mapping[str, FileIdentity] = RUN16_BOOT_FILES,
) -> list[str]:
    if not efi_root.is_dir():
        return [f"{efi_root}: EFI root is not a directory"]
    errors: list[str] = []
    for name, expected in expected_files.items():
        errors.extend(verify_file(efi_root / name, expected))
    return errors


def verify_initrd_relationship(
    root_initrd: Path,
    efi_initrd: Path,
    expected_root: FileIdentity = RUN16_ROOT_INITRD,
    expected_efi: FileIdentity = RUN16_BOOT_FILES["initrd.img"],
) -> list[str]:
    errors = verify_file(root_initrd, expected_root)
    errors.extend(verify_file(efi_initrd, expected_efi))
    if errors:
        return errors

    try:
        with (
            root_initrd.open("rb") as root_stream,
            efi_initrd.open("rb") as efi_stream,
        ):
            offset = 0
            while root_chunk := root_stream.read(READ_SIZE):
                efi_chunk = efi_stream.read(len(root_chunk))
                if efi_chunk != root_chunk:
                    errors.append(
                        f"{efi_initrd}: content differs from {root_initrd} "
                        f"at or after byte {offset}"
                    )
                    return errors
                offset += len(root_chunk)

            padding_size = expected_efi.size - expected_root.size
            padding_read = 0
            while padding_read < padding_size:
                chunk = efi_stream.read(min(READ_SIZE, padding_size - padding_read))
                if not chunk:
                    errors.append(f"{efi_initrd}: zero-padding tail ended early")
                    return errors
                if any(chunk):
                    errors.append(f"{efi_initrd}: padding tail contains nonzero data")
                    return errors
                padding_read += len(chunk)
            if efi_stream.read(1):
                errors.append(f"{efi_initrd}: data follows the expected padding tail")
    except OSError as exc:
        errors.append(f"could not compare initramfs copies: {exc}")
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read and verify the mounted EFI files from the successful "
            "firmware 11.60 Ubuntu Run 16 USB. No files are modified."
        )
    )
    parser.add_argument(
        "efi_root",
        type=Path,
        help="mounted FAT/EFI partition containing bzImage and initrd.img",
    )
    parser.add_argument(
        "--root-initrd",
        type=Path,
        help=(
            "optional unpadded /boot/initrd.img-7.1.7 from the mounted Linux "
            "root; also verifies the EFI prefix and zero-padding tail"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    errors = verify_boot_directory(args.efi_root)
    if args.root_initrd is not None:
        errors.extend(
            verify_initrd_relationship(
                args.root_initrd,
                args.efi_root / "initrd.img",
            )
        )

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS Ubuntu Run 16 boot-file identities match")
    if args.root_initrd is not None:
        print(
            "PASS EFI initrd is the exact root initramfs followed by zero padding"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
