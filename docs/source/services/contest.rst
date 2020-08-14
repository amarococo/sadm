Contest services
================

These contest services are the infrastructure for visualizing, scheduling and
running matches and tournaments between the champions. They are one of the most
important parts of the final infrastructure and should be prioritized more than
non-core services.

Concours
--------

Concours is the main contest website available at ``http://concours/``. It
allows people to upload champions and maps, schedule champion compilations, and
schedule maps. Staff users can also use it to schedule tournaments.

Concours is usually installed on the ``web`` machine, running as
``concours.service``. The on-disk champion and match data is stored in
``/var/prologin/concours_shared``. Users are automatically synchronized
from UDB with ``udbsync_django@concours``.

.. note::

    Concours is a *contest* service. It won't be available to users until the
    contest gets enabled in the Ansible inventory.
    See :ref:`enable_contest_services`.

API
^^^

Concours has a REST API available at ``http://concours/api``. It can be used by
contestants to script their interaction with the website.

Masternode
----------

Masternode is the scheduler node of a distributed task queue that runs on all
the user machines. Its goal is to retrieve pending tasks to compile champions
and run matches from the Concours website, find an available node to run the
task and send the required task data to the "Workernodes". Once the task is
completed, the Workernode sends back the result to Masternode, which saves it
in the database.

Masternode has to be setup on the same machine as Concours, as it requires
access to ``/var/prologin/concours_shared`` to retrieve and save the champion
data. It runs as ``masternode.service`` on ``web``.

You can check that Masternode is properly working by going to the master
status page on http://concours/status. It will tell you whether Masternode is
accessible, and list the Workernodes that are currently attached to it.

Workernode
----------

Workernode is the service that runs on all the user machines. It uses `isolate
<https://github.com/ioi/isolate>`_ and `camisole
<https://camisole.prologin.org/>` as isolation backends, to make sure that the
contestants' code is run safely without annoying the machine users.

Workernode runs as ``workernode.service``. Workers that cannot be reached from
the Masternode are automatically dropped from the pool. It is possible to
configure the number of "slots" allocated to each worker to throttle
parallelism in the ansible configuration, as well as the time, memory and other
resource constraints.

Year-specific customizations
----------------------------

Each year we create a new multiplayer game to be used in the final. We usually
need to add customizations for the game of the year, either aesthetic (custom
CSS for the theme of the game) or practical (map validation scripts,
game configuration, ...).

Configuration
^^^^^^^^^^^^^

**TODO**: Document how to set the number of players, whether to use maps, etc.

Theme
^^^^^

**TODO**: Document how to deploy and set the static path of the game theme.

Replay
^^^^^^

**TODO**: Document how to deploy the Javascript replayer script.

Map preview
^^^^^^^^^^^

**TODO**: Document how to deploy the Javascript map previewing script.

Map validity checks
^^^^^^^^^^^^^^^^^^^

**TODO**: Document how to deploy the map checking script to ensure uploaded
maps are valid. This might become obsolete if this issue is solved:
https://github.com/prologin/stechec2/issues/136


Running tournaments
-------------------

**TODO**
