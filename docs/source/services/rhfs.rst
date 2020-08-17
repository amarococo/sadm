RHFS services
=============

RFS
---

**TODO**

Forwarding of authorized_keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On a rhfs, the service ``udbsync_rootssh`` (aka. ``udbsync_clients.rootssh``)
writes the ssh public keys of roots to ``/root/.ssh/authorized_keys``. The unit
``rootssh.path`` watches this file, and on change starts the service
``rootssh-copy`` that updates the ``authorized_keys`` in the
``/exports/nfsroot_ro``.

HFS
---

**TODO**
