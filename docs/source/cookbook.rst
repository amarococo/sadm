Cookbook
========

All the things you might need to do as an organizer or a root are documented
here.

Install a package for the contestants
-------------------------------------

The recommended way to add a package for the contestants is to add it in the
list of packages, so that it will be also installed in future editions.
Simply edit ``ansible/roles/rfs_packages/tasks/main.yml`` and add the wanted
packages where appropriate, then redeploy::

    ansible-playbook playbook-rfs-container.yml

However, sometimes you might not want to add a package in a permanent fashion,
and just want to install something in a quick and dirty way on all the RFS
exports. In that case, use an Ansible ad-hoc command like this::

    ansible rfs_container -m shell -a "pacman -S mypackage"


.. _enable_contest_services:

Switching in and out of contest mode
------------------------------------

Contest mode is the set of switches to block internet access to the users and
give them access to the contest ressources.

Switching to contest mode is completely automated in Ansible. Initially, the
inventory should contain this default configuration, which disables contest
mode::

    contest_enabled: false
    contest_started: false

**Switching to contest mode** can be done in two steps:

1. Edit your inventory and enable these two values::

    contest_enabled: true
    contest_started: true

2. Run the following ansible command::

    ansible-playbook playbook-all-sadm.yml --tags contest_mode

**Once the contest is over**, you will want to go back to a configuration where
everyone can access the internet, but you do not want to remove the game
packages, because you will need them to run tournament matches. You can go to a
configuration that is out of contest mode, but where the contest resources
are no longer considered "secret" and are installed on the machines:

1. Change your inventory values to this::

    contest_enabled: false
    contest_started: true

2. Run the ansible command again::

    ansible-playbook playbook-all-sadm.yml --tags contest_mode

Customize the wallpaper
~~~~~~~~~~~~~~~~~~~~~~~

To customize the desktop wallpaper, edit your inventory to add a custom
wallpaper URL like this::

    wallpaper_override_url: "https://prologin.org/static/archives/2009/finale/xdm/prologin2k9_1280x1024.jpg"

Then, run the following command::

    ansible-playbook playbook-rfs-container.yml --tags wallpaper

This will install the new wallpaper at ``/opt/prologin/wallpaper.png``.

The following DE are setup to use this file:

* i3
* awesome
* Plasma (aka. KDE)
* XFCE

Gnome-shell is still to be done.

Customize the lightdm theme
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**TODO**

Sending announcements
---------------------

To send pop-up announcements on all the user's machines, use an Ansible ad-hoc
command like this::

    ansible user -m shell -a "/usr/bin/xrun /usr/bin/zenity --info --text='Allez manger !' --icon-name face-cool"

``xrun`` is a binary we install on all the user machines that knows how to
find the currently running X server and sets all the required environment
variables to run a GUI program on the remote machine.

User related operations
-----------------------

Most of the operations are made very simple with the use of ``udb``. If you are
an organizer, you can access ``udb`` in read only mode. If you are a root, you
obviously have write access too.

``udb`` displays the information (including passwords) of every contestant to
organizers. Organizers can't see the information of other organizers or roots.

All services should be using ``udb`` for authentication. Synchronization might
take up to 5 minutes (usually only one minute) if anything is changed.

Giving back his password to a contestant
    First of all, make sure to ask the contestant for his badge, which he
    should always have on him. Use the name from the badge to look up the user
    in the ``udb``. The password should be visible there.

Adding an organizer
    **Root only**. Go to ``udb`` and add a user with type ``orga``.

Machine registration
--------------------

``mdb`` contains the information of all machines on the contest LANs. If a
machine is not in ``mdb``, it is considered an alien and won't be able to
access the network.

All of these operations are **root only**. Organizers can't access the ``mdb``
administration interface.

Adding a user machine to the network
    In the ``mdb`` configuration, authorize self registration by adding a
    VolatileSetting ``allow_self_registration`` to true. Netboot the user
    machine - it should ask for registration details. After the details have
    been entered, the machine should reboot to the user environment. Disable
    ``allow_self_registration`` when you're done.

Adding a machine we don't manage to the user network
    Some organizers may want to use their laptop. Ask them for their MAC
    address and the hostname they want.
    Finally, insert a ``mdb`` machine record with machine type ``orga`` using
    the IP address you manually allocated (if you set the last allocation to
    100, you should assign the IP .100). Wait a minute for the DHCP
    configuration to be synced, and connect the laptop to the network.

Network FS related operations
-----------------------------

Two kind of network file systems are used during the finals, the first one is
the Root File System: RFS, the second is the Home File System: HFS.  The current
setup is that a server is both a RFS and a HFS node.

The RFS is a read-only NFS mounted as a rootnfs in Linux. It is replicated over
multiple servers to ensure minimum latency over the network.

The HFS is a read-write,
exclusive, user-specific export of their home. In other words, each user has
it's own personal space that can only be mounted once at a time. The HFS exports
are sharded over multiple servers.

Resetting the hfs
~~~~~~~~~~~~~~~~~

If you need to delete every ``/home`` created by the hfs, simply delete all nbd
files in ``/export/hfs/`` on all HFS servers and delete entries in the
``user_location`` table of the hfs' database::

  # For each hfs instance
  rm /export/hfs/*.nbd

  echo 'delete from user_location;' | su - postgres -c 'psql hfs'

Remove a RAID 1
~~~~~~~~~~~~~~~

The first step is to deactivate and remove the volume group::

  vgchange -a n data
  vgremove data

Then you have to actually deconstruct the RAID array and zero the superblock
of each device::

  mdadm --stop /dev/md0
  mdadm --remove /dev/md0
  mdadm --zero-superblock /dev/sda2
  mdadm --zero-superblock /dev/sdb2

If you want to erase the remaining ext4 filesystem on thoses devices, you can
use fdisk.
