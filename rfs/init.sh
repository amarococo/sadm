#!/bin/bash

set -e

if [ x"$ROOTFS" == "x" ]; then
  echo "ROOTFS not specified... aborting"
  exit 1
fi
if [ x"$SUBNET" == "x" ]; then
  echo "SUBNET not specified... aborting"
  exit 1
fi
if [ x"$PACKAGES" == "x" ]; then
  echo "PACKAGES not specified... aborting"
  exit 1
fi

mkdir -p "$ROOTFS"

# Install the tools needed to install and serve the rfs
pacman -Sy --needed --noconfirm arch-install-scripts nfs-utils openssh dnsutils

# Install the base system (in rfs)
pacstrap -d "$ROOTFS" base $PACKAGES

# Copy some tools we will use in chroot
cp -rv initcpio $ROOTFS/lib/    # initramfs hook
cp -rv .. "$ROOTFS/sadm"        # sadm (we'll need some of it's services)
cp rfs.sh "$ROOTFS/"            # the script executed by chroot below

# Chroot to continue work
arch-chroot "$ROOTFS" bash /rfs.sh

# Give the new system a nameserver (the gateway)
sed -e 's:^#nameserver.*:domain prolo\nnameserver 192.168.1.254:g' -i /export/nfsroot/etc/resolv.conf

# Load nbd driver at startup
echo nbd > /export/nfsroot/etc/modules-load.d/nbd.conf

# Clean the rfs by removing our installation tools
rm -f "$ROOTFS/rfs.sh"
rm -rf "$ROOTFS/sadm"

# Enable and start the services need to serve the rfs
for svc in {sshd,nfsd,udbsync_passwd_nfsroot,rpc-{idmapd,gssd,mountd,statd}}.service; do
  systemctl enable "$svc"
  systemctl start  "$svc"
done

# And finally export the rfs via nfs
echo "$ROOTFS $SUBNET(ro,no_root_squash,subtree_check,async)" > /etc/exports.d/rootfs.exports
exportfs -arv
echo "--------------"
echo "WARNING: Do not forget to copy the initrd and the kernel ($ROOTFS/boot/initramfs-linux.img and $ROOTFS/boot/vmlinuz-linux) to the directory specified in ./etc/prologin/netboot.yml (likely /srv/tftp/) and name them respectively 'initrd' and 'kernel'"
echo "--------------"
