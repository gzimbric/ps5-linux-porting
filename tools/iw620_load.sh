#!/usr/bin/env bash
# Load the IW620 Wi-Fi driver once on the Run 16 Ubuntu image (firmware 11.60).
# Usage: sudo ./iw620_load.sh [directory with mlan.ko, moal.ko and the firmware]
# Set IW620_ALLOW_UNTESTED=1 to load files that differ from the Run 17 build.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
dir=${1:-$script_dir}
kernel_version=7.1.7
firmware=nxp/pcieuartiw620_combo_v1.bin
options="fw_name=$firmware pcie_int_mode=1 drv_mode=1 cfg80211_wext=4 sta_name=mlan ext_scan=1 auto_fw_reload=0 wifi_reset_config=0 sched_scan=0 ps_mode=2 auto_ds=2 amsdu_disable=1 drvdbg=0x7"

check_file() {
  local file=$1 expected=$2 actual
  if [[ ! -f "$dir/$file" ]]; then
    printf 'Missing file: %s\n' "$dir/$file" >&2
    exit 1
  fi
  actual=$(sha256sum "$dir/$file" | awk '{print $1}')
  if [[ "$actual" != "$expected" ]]; then
    printf '%s does not match the Run 17 build: %s\n' "$file" "$actual" >&2
    if [[ "${IW620_ALLOW_UNTESTED:-0}" != 1 ]]; then
      exit 1
    fi
  fi
}

if (( EUID != 0 )); then
  printf 'Run this script as root.\n' >&2
  exit 1
fi

if [[ "$(uname -r)" != "$kernel_version" ]]; then
  printf 'Expected kernel %s, found %s\n' "$kernel_version" "$(uname -r)" >&2
  exit 1
fi

check_file mlan.ko e6f8e649974767f26d9bd8c60b3b49e1203d5282700493864b7e6fd7be482b23
check_file moal.ko 3e00f26af4d71d6f459a56a1b99c435dcacb09d3ead28e0e722898a68a6347ed
check_file pcieuartiw620_combo_v1.bin eafef24af118f96f84a652e17aeed555ec4ac719b9fac11ff98a2de7e2b4b369

if [[ "$(modinfo -F vermagic "$dir/moal.ko")" != "$(modinfo -F vermagic cfg80211)" ]]; then
  printf 'moal.ko was not built for this kernel.\n' >&2
  exit 1
fi

install -D -m 0644 "$dir/pcieuartiw620_combo_v1.bin" "/lib/firmware/$firmware"
modprobe cfg80211
if ! lsmod | grep -q '^mlan '; then
  insmod "$dir/mlan.ko"
fi
# shellcheck disable=SC2086
insmod "$dir/moal.ko" $options
sleep 3
dmesg | grep -E 'wlan:|WLAN|IW620|Register NXP|Firmware|Timeout|already running|FW download' \
  | tail -n 25
printf 'Interface: %s\n' "$(ls /sys/bus/pci/devices/0000:40:00.7/net/ 2>/dev/null || echo none)"
