#!/usr/bin/env bash
set -euo pipefail

kernel_version=${1:-7.1.7}
output=${2:-/tmp/ps5-initrd-1160.img}
firmware_dir=/usr/lib/firmware/amdgpu
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
amdgpu_config="$script_dir/../config/ps5-amdgpu.conf"
mkinitcpio_config=/etc/mkinitcpio.conf
expected_mkinitcpio_config=6329d81d796228ef0a2c3ee3b16be551f4403dcb129defbab91aa4279f40bc77
expected_output_size=54376639
expected_output_sha256=c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f
firmware_names=(ce me mec pfp rlc sdma sdma1)

expected_packages=(
  "linux-ps5 7.1.7-1"
  "linux-firmware-amdgpu 20260810-2"
  "mkinitcpio 41.1-1"
  "mkinitcpio-busybox 1.36.1-1"
  "zstd 1.5.7-3"
)

if (( EUID != 0 )); then
  printf 'Run this script as root.\n' >&2
  exit 1
fi

if [[ "$kernel_version" != 7.1.7 ]]; then
  printf 'This recipe is pinned to kernel 7.1.7, not %s\n' \
    "$kernel_version" >&2
  exit 1
fi

for command in awk chmod chown cmp grep install ln lsinitcpio mkinitcpio pacman \
  readlink sha256sum sort stat zstd; do
  if ! command -v "$command" >/dev/null; then
    printf 'Missing required command: %s\n' "$command" >&2
    exit 1
  fi
done

actual_mkinitcpio_config=$(sha256sum "$mkinitcpio_config" | awk '{print $1}')
if [[ "$actual_mkinitcpio_config" != "$expected_mkinitcpio_config" ]]; then
  printf 'mkinitcpio config mismatch: expected %s, found %s\n' \
    "$expected_mkinitcpio_config" "$actual_mkinitcpio_config" >&2
  exit 1
fi

if [[ -e "$output" ]]; then
  printf 'Refusing to overwrite %s\n' "$output" >&2
  exit 1
fi

if [[ ! -d "/usr/lib/modules/$kernel_version" ]]; then
  printf 'Missing kernel module tree: /usr/lib/modules/%s\n' \
    "$kernel_version" >&2
  exit 1
fi

for expected in "${expected_packages[@]}"; do
  package=${expected%% *}
  installed=$(pacman -Q "$package" 2>/dev/null || true)
  if [[ "$installed" != "$expected" ]]; then
    printf 'Package mismatch: expected %s, found %s\n' \
      "$expected" "${installed:-not installed}" >&2
    exit 1
  fi
done

if ! grep -Eq \
  '^[[:space:]]*MODULES=\([[:space:]]*amdgpu[[:space:]]*\)[[:space:]]*$' \
  "$mkinitcpio_config"; then
  printf 'Expected MODULES=(amdgpu) in %s\n' "$mkinitcpio_config" >&2
  exit 1
fi

if ! grep -Eq \
  '^[[:space:]]*HOOKS=\([[:space:]]*base[[:space:]]+udev[[:space:]]+modconf[[:space:]]+kms[[:space:]]+keyboard[[:space:]]+block[[:space:]]+filesystems[[:space:]]+fsck[[:space:]]*\)[[:space:]]*$' \
  "$mkinitcpio_config"; then
  printf 'Unexpected HOOKS in %s; refusing an unverified build\n' \
    "$mkinitcpio_config" >&2
  exit 1
fi

if [[ ! -f "$amdgpu_config" ]]; then
  printf 'Missing repository config: %s\n' "$amdgpu_config" >&2
  exit 1
fi

# Finish all checks before creating or replacing system files.
for name in "${firmware_names[@]}"; do
  compressed="$firmware_dir/cyan_skillfish2_${name}.bin.zst"
  uncompressed=${compressed%.zst}

  if [[ ! -f "$compressed" ]]; then
    printf 'Missing firmware package file: %s\n' "$compressed" >&2
    exit 1
  fi

  if [[ -e "$uncompressed" ]]; then
    if ! zstd -q -d -c -- "$compressed" | cmp -s - "$uncompressed"; then
      printf 'Existing firmware does not match %s: %s\n' \
        "$compressed" "$uncompressed" >&2
      exit 1
    fi
  fi
done

mec2="$firmware_dir/cyan_skillfish2_mec2.bin"
if [[ -e "$mec2" || -L "$mec2" ]]; then
  if [[ ! -L "$mec2" || "$(readlink "$mec2")" != cyan_skillfish2_mec.bin ]]; then
    printf 'Refusing to replace unexpected firmware entry: %s\n' "$mec2" >&2
    exit 1
  fi
fi

installed_config=/etc/modprobe.d/ps5-amdgpu.conf
if [[ -e "$installed_config" ]]; then
  if ! cmp -s "$amdgpu_config" "$installed_config"; then
    printf 'Refusing to replace different config: %s\n' \
      "$installed_config" >&2
    exit 1
  fi
fi

for name in "${firmware_names[@]}"; do
  compressed="$firmware_dir/cyan_skillfish2_${name}.bin.zst"
  uncompressed=${compressed%.zst}
  if [[ ! -e "$uncompressed" ]]; then
    zstd -q -d -k -- "$compressed" -o "$uncompressed"
  fi
  chown root:root "$uncompressed"
  chmod 0644 "$uncompressed"
done

if [[ ! -L "$mec2" ]]; then
  ln -s cyan_skillfish2_mec.bin "$mec2"
fi

if [[ ! -e "$installed_config" ]]; then
  install -D -m 0644 "$amdgpu_config" "$installed_config"
fi
chown root:root "$installed_config"
chmod 0644 "$installed_config"

mkinitcpio -g "$output" -k "$kernel_version"

printf '\nBuilt initramfs:\n'
stat -c '%n %s bytes' "$output"
sha256sum "$output"

actual_output_size=$(stat -c '%s' "$output")
actual_output_sha256=$(sha256sum "$output" | awk '{print $1}')
if [[ "$actual_output_size" != "$expected_output_size" ||
      "$actual_output_sha256" != "$expected_output_sha256" ]]; then
  printf 'Build does not match the Run 15 initramfs identity.\n' >&2
  printf 'Expected: %s bytes, %s\n' \
    "$expected_output_size" "$expected_output_sha256" >&2
  exit 2
fi

printf '\nEmbedded Cyan Skillfish firmware:\n'
lsinitcpio "$output" | grep 'usr/lib/firmware/amdgpu/cyan_skillfish2_' | sort

printf '\nEmbedded PS5 amdgpu configuration:\n'
lsinitcpio "$output" | grep 'etc/modprobe.d/ps5-amdgpu.conf'
