#!/bin/bash

CONTAINER_NAME=arch_linux_base
CONTAINER_HOSTNAME=dummy

cd $(dirname -- $0)
source ./container_common.sh

this_script_must_be_run_as_root

function container_setup_host {
  echo_status "Configure host for SADM containers"

  echo "[-] Disable DHCP server for our network zone"
  cat >/etc/systemd/network/80-container-vz-prolo.network <<EOF
[Match]
Name=vz-$NETWORK_ZONE
Driver=bridge

[Network]
# Default to using a /24 prefix, giving up to 253 addresses per virtual network.
Address=10.0.0.1/24
LinkLocalAddressing=yes
IPForward=yes
IPMasquerade=yes
LLDP=yes
EmitLLDP=customer-bridge
EOF

  echo "[-] Restart systemd-networkd"
  systemctl restart systemd-networkd

  echo "[-] Load the nbd kernel module"
  modprobe nbd
}

function container_bootstrap_arch_linux {
  echo_status "Preparing an Arch Linux install"

  if $USE_BTRFS; then
    if [ -d $ARCH_LINUX_BASE_ROOT ]; then
      container_remove_btrfs_root
    fi
    btrfs subvolume create $ARCH_LINUX_BASE_ROOT
  else
    mkdir -p $ARCH_LINUX_BASE_ROOT
  fi

  ../bootstrap_arch_linux.sh $ARCH_LINUX_BASE_ROOT fake_hostname <(echo $ROOT_PASSWORD)
}

container_setup_host

container_bootstrap_arch_linux
