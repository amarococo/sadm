Infrastructure overview
=======================

This section gives a brief overview of our infrastructure.

Documentation maintainers
-------------------------

- Alexandre Macabies (2013-2019)
- Antoine Pietri (2013-2020)
- Marin Hannache (2013, 2014)
- Nicolas Hureau (2013)
- Paul Hervot (2014, 2015)
- Pierre Bourdon (2013, 2014)
- Pierre-Marie de Rodat (2013)
- Rémi Audebert (2014-2019)
- Sylvain Laurent (2013)

Requirements
------------

- Host 100 contest participants + 20 organizers on diskless computers connected
  to a strangely wired network (2 rooms with low bandwidth between the two).

- Run several internal services:

  - DHCP + DNS
  - Machine DataBase (MDB)
  - User DataBase (UDB)
  - Home File Server (HFS)
  - NTPd

- Run several external services (all of these are described later):

  - File storage
  - Homepage server
  - Wiki
  - Contest website
  - Bug tracking software (Redmine)
  - Documentation pages
  - IRC server
  - Pastebin
  - Matches cluster

Network infrastructure
----------------------

We basically have a single local network, containing every user machine and all
servers, on the range 192.168.0.0/23. The gateway (named ``gw``) is
192.168.1.254.

This local network is further divided in three subnetworks:

- 192.168.0.0/24 is for users (staff and contestants)
- 192.168.1.0/24 is reserved for servers
- 192.168.250.0/24 is the *alien* network, reserved for machines not in the MDB
  that are pending registration.

.. _mdb_overview:

Machine database
----------------

The Machine DataBase (MDB) is one of the most important parts of the
architecture. Its goal is to track the state of all the machines on the network
and provide information about the machines to anyone who needs it. It is
running on hostname ``mdb`` and exports a web interface for administration
(accessible to all roots).

A Python client is available for scripts that need to query it, as well as a
bare-bones HTTP interface for use in PXE scripts.

It stores the following information for each machine:

- Main hostname
- Alias hostnames (for machines hosting multiple services, or for services that
  have several DNS aliases, eg. ``docs`` and ``doc``)
- IP
- MAC
- Nearest root file server
- Nearest home file server
- Machine type (user, orga, cluster, service)
- Room id (pasteur, alt, cluster, other)

It is the main data source for DHCP, DNS, monitoring and other stuff.

.. _mdb_pxe:

When a machine boots, an IPXE script will lookup the machine info from the MDB
to get the hostname and the nearest NFS root. If it is not present, it will ask
for information interactively and register the machine in the MDB.

.. _udb_overview:

User database
-------------

The User DataBase (UDB) stores the user information. As with MDB, it provides a
simple Python client library as well as a web interface (accessible to all
organizers, not only roots). It is running on hostname ``udb``.

It stores the following information for every user:

- Login
- First name
- Last name
- Current machine name
- Password (unencrypted so organizers can give it back to people who lose it)
- Type (contestant, organizer, root)
- SSH key (mostly useful for roots)

As with the MDB, the UDB is used as the main data source for several services:
every service accepting logins from users synchronizes the user data from the
UDB (contest website, bug tracker, ...). A PAM script is also used to handle
login on user machines.

File storage
------------

3 classes of file storage, all using NFS over TCP (to handle network congestion
gracefully):

- Root filesystem for the user machines: 99% reads, writes only done by roots.
- Home directories filesystem: 50% reads, 50% writes, needs low latency
- Shared directory for users junk: best effort, does not need to be fast, if
  people complain, tell them off.

Root filesystem is manually replicated to several file servers after any change
by a sysadmin. Each machine using the root filesystem will interrogate the MDB
:ref:`at boot time <mdb_pxe>` to know what file server to connect to. These
file servers are named ``rfs-1``, ``rfs-2``, etc. One of these file servers
(usually ``rfs-1``) is aliased to ``rfs``. It is the one roots should connect
to in order to write to the exported filesystem. The other rfs servers have the
exported filesystem mounted as read-only, except when syncing.

Home directories are sharded to several file servers, typically two per
physical room. These file servers are named ``hfs-1``, ``hfs-2``, etc. When a
PAM session is opened on a machine, a script contacts the :ref:`HFS` to request
that this user's home direct be ready for serving over the network. This can
involve :ref:`a migration <home_migration>`, but eventually the script mounts
the home directory and the user is logged-in.

The user shared directory is just one shared NFS mountpoint for everyone. It
does not have any hard performance requirement. If it really is too slow, it
can be sharded as well (users will see two shared mount points and will have to
choose which one to use). This file server is called ``shfs``.

Other small services
--------------------

Here is a list of all the other small services we provide that don't really
warrant a long explanation:

- Homepage: runs on ``homepage``, provides the default web page displayed to
  contestants in their browser
- Wiki: runs on ``wiki``, UDB aware wiki for contestants
- Contest website: runs on ``contest``, contestants upload their code and
  launch matches there
- Bug tracker: ``bugs``, UDB aware Redmine
- Documentations: ``docs``, language and libraries docs, also rules, API and
  Stechec docs.
- IRC server: ``irc``, small UnrealIRCd without services, not UDB aware
- Paste: ``paste``, random pastebin service
