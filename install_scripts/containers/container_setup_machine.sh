#!/bin/bash

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <machine_name>"
  exit 1
fi

CONTAINER_NAME="my$1"
CONTAINER_HOSTNAME="$1"

cd $(dirname -- $0)
source ./container_common.sh

this_script_must_be_run_as_root

function stage_setup_container {
    echo "[-] Create $CONTAINER_ROOT"
    if $USE_BTRFS; then
        if [ -d $CONTAINER_ROOT ]; then
            container_remove_btrfs_root
        fi
        btrfs subvolume snapshot $ARCH_LINUX_BASE_ROOT $CONTAINER_ROOT
    else
        rsync --partial --info=progress2 -ha $ARCH_LINUX_BASE_ROOT/ $CONTAINER_ROOT
    fi

    echo "[-] Remove pacstrapped /etc/machine-id"
    rm -f "$CONTAINER_ROOT"/etc/machine-id

    echo "[-] Configure hostname"
    echo "$CONTAINER_HOSTNAME" > "$CONTAINER_ROOT"/etc/hostname

    echo "[-] Create $CONTAINER_NAME.nspawn configuration file"
    mkdir -p /etc/systemd/nspawn
    cat >/etc/systemd/nspawn/$CONTAINER_NAME.nspawn <<EOF
[Network]
Zone=$NETWORK_ZONE

[Files]
# Allows cp-ing from container to container
PrivateUsersChown=false
BindReadOnly=${SADM_ROOT_DIR}:/root/sadm
EOF

    if [ "$CONTAINER_HOSTNAME" == "gw" ]; then
        echo "[-] Bootstrap gateway static IP"
	# This will be overwritten by ansible and just serves to bootstrap the
	# gateway IP for the first time.
        cat >"$CONTAINER_ROOT"/etc/systemd/network/10-gw.network <<EOF
[Match]
Name=host0

[Network]
DHCP=no
Gateway=10.0.0.1
Address=10.0.0.254/24
EOF
        cat >"$CONTAINER_ROOT"/etc/resolv.conf <<EOF
nameserver 8.8.8.8
EOF
    fi
}

function stage_setup_ssh {
    echo_status "Setup SSH keys"

    mkdir -p "$CONTAINER_ROOT"/root/.ssh
    cat "$SSH_PUB_KEY" > "$CONTAINER_ROOT"/root/.ssh/authorized_keys
    cat "$SSH_PUB_KEY" > "$CONTAINER_ROOT"/root/.ssh/authorized_keys2
    chown -R root:root "$CONTAINER_ROOT"/root/.ssh
    chmod 700 "$CONTAINER_ROOT"/root/.ssh
    chmod 600 "$CONTAINER_ROOT"/root/.ssh/*
}

function stage_write_inventory_mac {
    echo_status "Write ethernet MAC in the ansible container inventory"

    host_var_dir="$ANSIBLE_INVENTORY/host_vars/$CONTAINER_HOSTNAME"
    mkdir -p "$host_var_dir"
    CONTAINER_MAC=$(
        systemd-run -M $CONTAINER_NAME --quiet --pipe "$@" \
            /bin/cat /sys/class/net/host0/address
    )
    echo "mac: \"$CONTAINER_MAC\"" > "$host_var_dir/mac.yml"
    chown --reference="$host_var_dir" "$host_var_dir/mac.yml"
}

run container_stop
run stage_setup_container
run stage_setup_ssh
run container_start
run stage_write_inventory_mac
