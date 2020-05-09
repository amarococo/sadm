#!/bin/bash

set -e

cd /var/lib/machines

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <machine_name>"
fi

machine="my$1"
machine_hostname="$1"

rsync --partial --info=progress2 -ha arch_linux_base/ "$machine"
rm -f "$machine"/etc/machine-id

mkdir -p "$machine"/root/.ssh
cat $HOME/.ssh/id_*.pub | tee "$machine"/root/.ssh/authorized_keys "$machine"/root/.ssh/authorized_keys2
chown -R root:root "$machine"/root/.ssh
chmod 700 "$machine"/root/.ssh
chmod 600 "$machine"/root/.ssh/*
echo "$machine_hostname" > "$machine"/etc/hostname

cat >/etc/systemd/nspawn/"$machine".nspawn <<NSPAWN
[Network]
Zone=prolo

[Files]
# Allows cp-ing from container to container
PrivateUsersChown=false

# Allow use of cgroupv1 from inside the container
Bind=/sys/fs/cgroup

[Exec]
# Required for docker
Capability=all
SystemCallFilter=add_key keyctl
NSPAWN

mkdir -p /etc/systemd/system/systemd-nspawn@"$machine".service.d/
cat >/etc/systemd/system/systemd-nspawn@"$machine".service.d/override.conf <<NSPAWN
Environment=SYSTEMD_NSPAWN_USE_CGNS=0
NSPAWN

machinectl start "$machine"
