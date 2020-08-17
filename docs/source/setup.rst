Setup instructions
==================

If you are like the typical Prologin organizer, you're probably reading this
documentation one day before the start of the event, worried about your ability
to make everything work before the contest starts. Fear not! This section of
the documentation explains everything you need to do to set up the
infrastructure for the finals, assuming all the machines are already physically
present. Just follow the guide!

Note: This section is for the actual hardware setup of the final. To setup a
development environment in containers, see :ref:`container_setup`.

Step 0: hardware and network setup
----------------------------------

Before installing servers, we need to make sure all the machines are connected
to the network properly. Here are the major points you need to be careful
about:

* Make sure to balance the number of machines connected per switch: the least
  machines connected to a switch, the better performance you'll get.
* Inter-switch connections is not very important: we tried to make most things
  local to a switch (RFS + HFS should each be local, the rest is mainly HTTP
  connections to services).
* Have a very limited trust on the hardware that is given to you, and if
  possible reset them to a factory default.

For each pair of switches, you will need one RHFS server (connected to the 2
switches via 2 separate NICs, and hosting the RFS + HFS for the machines on
these 2 switches). Please be careful out the disk space: assume that each RHFS
has about 100GB usable for HFS storage. That means at most 50 contestants (2GB
quota) or 20 organizers (5GB quota) per RHFS. With contestants that should not
be a problem, but try to balance organizers machines as much as possible.

You also need one gateway/router machine, which will have 3 different IP
addresses for the 3 logical subnets used during the finals:

:Users and services: 192.168.0.0/23
:Alien (unknown): 192.168.250.0/24
:Upstream: Based on the IP used by the bocal internet gateway.

Contestants and organizers must be on the same subnet in order for UDP
broadcasting to work between them. This is required for most video games played
during the finals: server browsers work by sending UDP broadcast announcements.

Having services and users on the same logical network avoids all the traffic
from users to services going through the gateway. Since this includes all RHFS
traffic, we need to make sure this is local to the switch and not being routed
via the gateway. However, for clarity reasons, we allocate IP addresses in the
users and services subnet like this:

:Users: 192.168.0.0 - 192.168.0.253
:Services and organizers machines: 192.168.1.0 - 192.168.1.253

Step 1: writing the Ansible inventory
-------------------------------------

The Ansible inventory is configuration that is specific to the current SADM
deployment. There are two inventories in the ``ansible`` directory:

- an ``inventory`` directory, the default inventory, which is used for local
  testing purposes
- a ``inv_final`` directory, which contains the deployment for the finals, that
  we update each year.

**TODO**: document step-by-step how to write the inventory once we actually
have to do it on a physical infra, which hasn't happened yet. Include secrets
rotations, addition of MAC addresses, etc.

Step 2: setting up the gateway
------------------------------

The very first step is to install an Arch Linux system for ``gw``.  We have
scripts to make this task fast and easy.

.. _basic_fs_setup:

Basic system: file system setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    The installation process is partially automated with scripts. You are
    strongly advised to read them and make sure you understand what they are
    doing.

Let's start with the hardware setup. You can skip this section if you are
doing a containerized install or if you already have a file system ready.

For ``gw`` and other critical systems such as ``web``, we setup a `RAID1
(mirroring) <https://en.wikipedia.org/wiki/Standard_RAID_levels#RAID_1>`__ over
two discs. Because the RAID will be the size of the smallest disc, they have to
be of the same capacity. We use regular 500GBytes SATA, which is usually more
than enough. It is a good idea to choose two different disks (brand, age,
batch) to reduce the chance to have them failing at the same time.

On top of the RAID1, our standard setup uses `LVM
<https://wiki.archlinux.org/index.php/LVM>`_ to create and manage the system
partition. For bootloading the system we use the good old BIOS and ``syslinux``.

All this setup is automated by our bootstrap scripts, but to run them you will
need a bootstrap Linux distribution. The easiest solution is to boot on the
Arch Linux's install medium
`<https://wiki.archlinux.org/index.php/Installation_guide#Boot_the_live_environment>`_.

Once the bootstrap system is started, you can start the install using::

  bash <(curl https://raw.githubusercontent.com/prologin/sadm/master/install_scripts/bootstrap_from_install_medium.sh)

This script checks out sadm, then does the RAID1 setup, installs Arch Linux and
configures it for RAID1 boot. So far nothing is specific to sadm and you could
almost use this script to install yourself an Arch Linux.

When the script finishes the system is configured and bootable, you can restart
the machine::

  reboot

The machine should reboot and display the login tty. To test this step:

- The system must boot
- Systemd should start without any ``[FAILED]`` item.
- Log into the machine as ``root`` with the password you configured.
- Check that the hostname is ``gw.prolo`` by invoking ``hostnamectl``::

     Static hostname: gw.prolo
           Icon name: computer-container
             Chassis: container
          Machine ID: 603218907b0f49a696e6363323cb1833
             Boot ID: 65c57ca80edc464bb83295ccc4014ef6
      Virtualization: systemd-nspawn
    Operating System: Arch Linux
              Kernel: Linux 4.6.2-1-ARCH
        Architecture: x86-64

- Check that the timezone is ``Europe/Paris`` and `NTP
  <https://wiki.archlinux.org/index.php/Time#Time_synchronization>`_ is enabled
  using ``timedatectl``::

          Local time: Fri 2016-06-24 08:53:03 CEST
      Universal time: Fri 2016-06-24 06:53:03 UTC
            RTC time: n/a
           Time zone: Europe/Paris (CEST, +0200)
     Network time on: yes
    NTP synchronized: yes
     RTC in local TZ: no

- Check the NTP server used::

    systemctl status systemd-timesyncd
    Sep 25 13:49:28 halfr-thinkpad-e545 systemd-timesyncd[13554]: Synchronized to time server 212.47.239.163:123 (0.arch.pool.ntp.org).

- Check that the locale is ``en_US.UTF8`` with the ``UTF8`` charset using
  ``localectl``::

    System Locale: LANG=en_US.UTF-8
        VC Keymap: n/a
       X11 Layout: n/a

- You should get an IP from DHCP if you are on a network that has such a setup,
  else you can add a static IP using a ``systemd-network`` ``.network``
  configuration file.

SADM deployment
~~~~~~~~~~~~~~~

Now, we can install the Prologin-specific services on ``gw`` using Ansible.
Either from a machine that is on the same network as ``gw`` or on ``gw``
itself, retrieve the SADM repository and deploy the gateway playbook::

    cd ansible
    export ANSIBLE_INVENTORY=inv_final
    source ./activate_mitogen.sh  # Tool that speeds-up Ansible
    ansible-playbook playbook-gw.yml

Gateway network configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``gw`` has multiple static IPs used in our local network:

- 192.168.1.254/23 used to communicate with both the services and the users
- 192.168.250.254/24 used to communicate with aliens (aka. machines not in mdb)

It also has IP to communicate with the outside world:

- 10.?.?.?/8 static IP given by the bocal to communicate with the bocal gateway
- 163.5.??.??/16 WAN IP given by the CRI

The network interface(s) are configured using ``systemd-networkd``. Our
configuration files are stored in ``etc/systemd/network/``.

For this step, we use the following systemd services:

- From systemd: ``systemd-networkd.service``: does the network configuration, interface
  renaming, IP setting, DHCP getting, gateway configuring, you get the idea.
  This service is enabled by the Arch Linux bootstrap script.
- From sadm: ``nic-configuration@.service``: network interface configuration,
  this service should be enabled for each of the interface on the system.

For more information, see the `systemd-networkd documentation
<http://www.freedesktop.org/software/systemd/man/systemd-networkd.html>`_.

At this point you should reboot and test your network configuration:

- Your network interfaces should be up (``ip link show`` shoud show ``state
  UP`` for all interfaces but ``lo``).
- The IP addresses (``ip address show``) are correctly set to their respective
  interfaces.
- Default route (``ip route show``) should be the CRI's gateway.

Then, you can also check that the :ref:`core_services` are individually running
properly, as they will be required for the rest of the setup.

Step 3: file storage
--------------------

.. sidebar:: rhfs naming scheme

    A rhfs has two NICs and is connected to two switches, there is therefore
    two ``hfs-server`` running on one rhfs machine, each with a different id.
    The hostname of the rhfs that hosts hfs ``0`` and hfs ``1`` will be:
    ``rhfs01``.

A RHFS, for "root/home file server", has the following specifications:

- It is connected to two switches, handling two separates L2 segments. As such,
  the machine on a L2 segment is only 1 switch away from it RHFS. This is a
  good thing as it reduces the network latency, reduces the risk if one the
  switches in the room fails and simplyfies debugging network issues.
  It also mean that a RHFS will be physically near the machines it handles,
  pretty useful for debugging, although you will mostly work using SSH.
- Two NICs configured using DHCP, each of them connected to a different switch.
- Two disks in RAID1 setup, same as gw.

To bootstrap a rhfs, ``rhfs01`` for example, follow this procedure:

#. Boot the machine using PXE and register it into ``mdb`` as ``rhfs01``.
#. Reboot the machine and boot an Arch Linux install medium.
#. Follow the same first setup step as for ``gw``: see :ref:`basic_fs_setup`.

Do that for all the RHFS, then go to the next step.

RHFS Inventory setup
~~~~~~~~~~~~~~~~~~~~

**TODO**: explain how to write the RHFS parts of the inventory

Installing the RHFS
~~~~~~~~~~~~~~~~~~~

Like before, once the base system is set up and the inventory has been written,
we can install it very simply::

    ansible-playbook playbook-rhfs.yml

After setting up the RHFS systems, we also need to setup the inside of the RFS
system, by deploying ansible in the container which mounts
``/export/nfsroot``::

    ansible-playbook playbook-rfs-container.yml

Registering the switches
~~~~~~~~~~~~~~~~~~~~~~~~

To be able to register the machines easily, we can register all the switches in
MDB. By using the LLDP protocol, when registering the machines, they will be
able to see which switch they are linked to and automatically guess the
matching RHFS server.

On each rhfs, run the following command::

  networkctl lldp

You should see an LLDP table like this::

  LINK    CHASSIS ID         SYSTEM NAME   CAPS        PORT ID           PORT DESCRIPTION
  rhfs0   68:b5:99:9f:45:40  sw-kb-past-2  ..b........ 12                12
  rhfs1   c0:91:34:c3:02:00  sw-kb-pas-3   ..b........ 22                22

This means the "rhfs0" interface of rhfs01 is linked to a switch named
sw-kb-past-2 with a Chassis ID of 68:b5:99:9f:45:40.

After running this on all the rhfs, you should be able to
establish a mapping like this::

  rhfs0 -> sw-kb-past-2 (68:b5:99:9f:45:40)
  rhfs1 -> sw-kb-pas-3 (c0:91:34:c3:02:00)
  rhfs2 -> sw-kb-pas-4 (00:16:b9:c5:25:60)
  rhfs3 -> sw-pas-5 (00:16:b9:c5:84:e0)
  rhfs4 -> sw-kb-pas-6 (00:14:38:67:f7:e0)
  rhfs5 -> sw-kb-pas-7 (00:1b:3f:5b:8c:a0)

You can register all those switches [in MDB](http://mdb/mdb/switch/). Click on
"add switch", with the name of the switch like ``sw-kb-past-2``, the chassis ID
like ``68:b5:99:9f:45:40``, and put the number of the interface in the RFS and
HFS field (i.e if it's on the interface ``rhfs0``, put 0 in both fields).

Step 4: booting the user machines
---------------------------------

All the components required to boot user machines should now properly be
installed. Execute this on all the machines:

#. Boot a user machine
#. Choose "Register with LLDP"
#. Follow the instructions to register the machine and reboot.

Test procedure that everything is working well on the machine:

#. Boot a user machine
#. Login manager should appear
#. Log using a test account (create one if needed), a hfs should be created
   with the skeleton in it.
#. The desktop launches, the user can edit files and start programs
#. Close the session
#. Boot a user machine using an other hfs
#. Log using the same test account, the hfs should be be migrated.
#. The same desktop launches with modifications.

Step 5: Install the service machines
------------------------------------

We now need to setup all the service machines (monitoring, web, misc). For each
of these servers:

#. Boot the machine using PXE and register it into ``mdb`` as a service with
   the correct hostname.
#. Reboot the machine and boot an Arch Linux install medium.
#. Follow the same first setup step as for ``gw``: see :ref:`basic_fs_setup`.

Once all of them are running on the network and pinging properly, they can be
deployed::

    ansible-playbook playbook-monitoring.yml
    ansible-playbook playbook-web.yml
    ansible-playbook playbook-misc.yml


Note: Testing on qemu/libvirt
-----------------------------

Here are some notes:

- Do not use the spice graphical console for setting up servers, use the serial
  line. For syslinux it is ``serial 0`` at the top of ``syslinux.cfg`` and for
  Linux ``console=ttyS0`` on the cmd line of the kernel in ``syslinux.cfg``.
- For best performance use the VirtIO devices (disk, NIC), this should already
  be configured if you used ``virt-install`` to create the machine.
- For user machines, use the QXL driver for best performance with SPICE.
