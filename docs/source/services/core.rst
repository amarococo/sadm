.. _core_services:

Core services
=============

These services are the backbone of the infrastructure and are installed very
early during the setup, as most other services depend on them. They are
generally installed on the ``gw`` machine; they could run elsewhere but we
don't have a lot of free machines and the core is easier to set up at one
single place.

The services installed here are a bit tricky. As this is the core of the
architecture, everything kind of depends on each other:

.. image:: ../core-deps.png

This is worked around by bootstrapping the infra in a number of ways, most
importantly by keeping an initial list of the first core services in
``gw:/etc/hosts`` to access them while the DNS setup is not available.

mdb
~~~

MDB is the machine database described in the infrastructure overview (see
:ref:`mdb_overview`), available at ``http://mdb/``. Root admins can login there
to edit information about the machines.

To check that MDB is working, you can call the RPC endpoint ``/call/query``::

  curl http://mdb/call/query
  # Should return a JSON dict containing the machines registered in MDB


mdbsync
~~~~~~~

``mdbsync`` is a web server used for applications that need to react on ``mdb``
updates. The DHCP and DNS config generation scripts use it to automatically
update the configuration when ``mdb`` changes.

To check if ``mdbsync`` is working, try to register for updates::

  python -c 'import prologin.mdbsync.client; prologin.mdbsync.client.connect().poll_updates(print)'
  # Should print {} {} and wait for updates

mdbdns
~~~~~~

``mdbdns`` gets updates from ``mdbsync`` and regenerates the DNS configuration.

You can check that ``mdbdns`` is working by checking that the DNS configuration
correctly contains the machines registered in MDB::

  host mdb.prolo 127.0.0.1
  # Should return 192.168.1.254

mdbdhcp
~~~~~~~

``mdbdhcp`` works just like ``mdbdns``, but for DHCP.

The DHCP server also provides an Arch Linux install medium in PXE to install
all the servers. (See https://www.archlinux.org/releng/netboot/)

netboot
~~~~~~~

Netboot is a small HTTP service used to handle interactions with the PXE boot
script: machine registration and chaining on the appropriate kernel files. It
runs as ``netboot.service``.

TFTP
~~~~

The TFTP server is used by the PXE clients to fetch the first stage of the boot
chain: the iPXE binary (more on that in the next section). It is a simple
``tftp-hpa`` daemon.

The TFTP server serves files from ``/srv/tftp``.

iPXE bootrom
~~~~~~~~~~~~

The iPXE bootrom is an integral part of the boot chain for user machines. It is
loaded by the machine BIOS via PXE and is responsible for booting the Linux
kernel using the nearest RFS. It also handles registering the machine in the
MDB if needed.

We need a special version of iPXE supporting the LLDP protocol to speed up
machine registration. We have a pre-built version of the PXE image in our Arch
Linux repository. The package ``ipxe-sadm-git`` installs the PXE image as
``/srv/tftp/prologin.kpxe``.

udb
~~~

UDB is the user database described in the infrastructure overview (see
:ref:`udb_overview`), available at ``http://udb/``. Root admins can login there
to edit information about the users.

You can then import all contestants information to ``udb`` using the
``batchimport`` command::

  cd /opt/prologin/udb
  python manage.py batchimport --file=/root/finalistes.txt

The password sheet data can then be generated with this command, then printed
by someone else::

  python manage.py pwdsheetdata --type=user > /root/user_pwdsheet_data

Then do the same for organizers::

  python manage.py batchimport --logins --type=orga --pwdlen=10 \
      --file=/root/orgas.txt
  python manage.py pwdsheetdata --type=orga > /root/orga_pwdsheet_data

Then for roots::

  python manage.py batchimport --logins --type=root --pwdlen=10 \
      --file=/root/roots.txt
  python manage.py pwdsheetdata --type=root > /root/root_pwdsheet_data

udbsync
~~~~~~~

``usbsync`` is a server that pushes updates of the user list.

presencesync
~~~~~~~~~~~~

``presencesync`` manages the list of logged users. It authorizes user logins
and maintain the list of logged users using pings from the ``presenced`` daemon
running in the NFS exported systems.

presencesync_sso
~~~~~~~~~~~~~~~~

This listens to both ``presencesync`` and ``mdb`` updates and maintains a double
mapping ``ip addr → machine hostname → logged-in username``. This provides a way
of knowing which user is logged on what machine by its IP address. This is used
by nginx SSO to translate request IPs to logged-in username.

``presencesync_sso`` exposes an HTTP endpoint at http://sso/.

All services that support SSO already have the proper stubs in their respective
nginx config. See the comments in ``etc/nginx/sso/{handler,protect}`` for how
to use these stubs in new HTTP endpoints.

Debugging SSO
*************

Typical symptoms of an incorrect SSO setup are:

* you're not automatically logged-in on SSO-enabled websites such as http://udb
  or http://concours
* nginx logs show entries mentioning ``__sso_auth`` or something about not being
  able to connect to some ``sso`` upstream

Your best chance at debugging this is to check the reply headers in your browser
inspection tool.

* if there is not any of the headers described below, it means your service
  is not SSO-enabled, ie. doesn't contain the stubs mentioned above. Fix that.
* ``X-SSO-Backend-Status`` should be ``working``, otherwise it means nginx
  cannot reach the SSO endpoint; in that case check that ``presencesync_sso``
  works and http://sso is reachable.
* ``X-SSO-Status`` should be ``authenticated`` and ``X-SSO-User`` should be
  filled-in; if the website is not in a logged-in state, it means SSO is working
  but the website does not understand, or doesn't correctly handle the SSO
  headers. Maybe it is configured to get the user from a different header eg.
  ``Remote-User``? Fix the website.
* if ``X-SSO-Status`` is ``missing header``, it means nginx is not sending the
  real IP address making the request; are you missing ``include sso/handler``?
* if ``X-SSO-Status`` is ``unknown IP``, it means ``presencesync_sso`` couldn't
  resolve the machine hostname from its IP; check the IP exists in http://mdb
  and that ``presencesync_sso`` is receiving ``mdb`` updates.
* if ``X-SSO-Status`` is ``logged-out machine``, it means ``presencesync_sso``
  believes no one is logged-in the machine from which you do the requests; check
  that ``presencesync`` knows about the session (eg. using http://map/) and that
  ``presencesync_sso`` is receiving ``presencesync`` updates.

firewall
~~~~~~~~

A firewall of iptables rules is automatically installed on ``gw``. It handles
allowing and disallowing network access, and masquerading the network traffic.

A ``presencesync_firewall.service`` service automatically updates this firewall
to allow internet access to staff and disallow it to contestants during the
contest.

conntrack
~~~~~~~~~

``conntrack.service`` does the necessary logging to comply with the fact that
we are responsible for what the users are doing when using our gateway to the
internet.

hfsdb
~~~~~

**TODO**

udbsync_rootssh
~~~~~~~~~~~~~~~

**TODO**

udbsync_django
~~~~~~~~~~~~~~

**TODO**
