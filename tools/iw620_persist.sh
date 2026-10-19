#!/usr/bin/env bash
# Configure the IW620 Wi-Fi driver to load at boot on the Run 16 Ubuntu image
# (firmware 11.60). Run it after iw620_load.sh worked and a network connected.
# Usage: sudo ./iw620_persist.sh [directory with mlan.ko, moal.ko and the firmware]
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
dir=${1:-$script_dir}
kernel_version=7.1.7
module_dir=/lib/modules/$kernel_version/updates/ps5-iw620
blacklist=/etc/modprobe.d/ps5-iw620-noautoload.conf
saved_blacklist=/etc/ps5-iw620-noautoload.conf.orig

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

check_file mlan.ko e6f8e649974767f26d9bd8c60b3b49e1203d5282700493864b7e6fd7be482b23
check_file moal.ko 3e00f26af4d71d6f459a56a1b99c435dcacb09d3ead28e0e722898a68a6347ed
check_file pcieuartiw620_combo_v1.bin eafef24af118f96f84a652e17aeed555ec4ac719b9fac11ff98a2de7e2b4b369

install -D -m 0644 "$dir/pcieuartiw620_combo_v1.bin" \
  /lib/firmware/nxp/pcieuartiw620_combo_v1.bin
install -D -m 0644 "$dir/mlan.ko" "$module_dir/mlan.ko"
install -D -m 0644 "$dir/moal.ko" "$module_dir/moal.ko"
depmod -a "$kernel_version"

cat > /etc/modprobe.d/ps5-iw620.conf <<'EOF'
softdep moal pre: cfg80211 mlan
options moal fw_name=nxp/pcieuartiw620_combo_v1.bin pcie_int_mode=1 drv_mode=1 cfg80211_wext=4 sta_name=mlan ext_scan=1 auto_fw_reload=0 wifi_reset_config=0 sched_scan=0 ps_mode=2 auto_ds=2 amsdu_disable=1 drvdbg=0x7
EOF

# The image's initramfs hook copies the blacklist file, so keep the file and
# replace its contents.
if [[ -f "$blacklist" && ! -e "$saved_blacklist" ]]; then
  cp "$blacklist" "$saved_blacklist"
fi
printf '# moal/mlan autoload enabled\n' > "$blacklist"
printf 'moal\n' > /etc/modules-load.d/ps5-iw620.conf

if [[ "$(modinfo -k "$kernel_version" -F filename moal)" != "$module_dir/moal.ko" ]]; then
  printf 'depmod did not pick up %s\n' "$module_dir" >&2
  exit 1
fi
printf 'Configured moal to load at boot. Reboot to confirm it.\n'
