Misc services
=============

These services are usually installed on the ``misc`` machine. They are
generally relatively unimportant services that do not prevent the contestants
from participating in the finals when not present (game servers, music voting
system, ...). Performance and reliability are generally not a priority for
them, so we put them in this machine.

``/sgoinfre``
-------------

``/sgoinfre`` is a shared read/write NFS mount between all the contestants. The
NFS server is on misc, and all the managed user machines mount it
automatically when available through the ``sgoinfre.mount`` unit.

Radio
-----

Sometimes, when the DJ is sleeping, we allow the contestants to vote for the
music that gets played in the music room. We use `djraio
<https://bitbucket/Zopieux/djraio>`_, which is able to pull music from YouTube
and Spotify. It acts as a proxy so that contestants can search for their music
without internet access. This service is available at ``http://radio/``.

**TODO:** the setup of this service isn't automated yet. To install it, follow
README instructions here: https://bitbucket/Zopieux/djraio

IRC
---

An IRC server is available at ``irc://prologin:6667/``. It's an UnrealIRCd
server running as ``unrealircd.service``. When connecting to the server,
contestants are automatically added to three channels:

- **#prologin**: A free-for-all discussion channel.
- **#announce**: A channel where only the staff can talk, to send announcements
  to contestants.
- **#issues**: A channel streaming status updates on issues created in the bug
  tracker.

Everyone can create new channels, there are no restrictions.

Oper privileges
~~~~~~~~~~~~~~~

Staff users can get oper privileges on the channels by typing the command::

    /oper ircgod <operpassword>

where ``<operpassword>`` is the ``irc_oper_password`` defined in the Ansible
inventory.

This will make you automatically join the fourth default chan:

- **#staff**: A channel that only the staff can join, to coordinate together.

IRC issues bot
~~~~~~~~~~~~~~

**TODO**: A bot is supposed to stream the status updates of issues in the
**#issues** channel, but we don't have that anymore since we migrated away from
redmine. This section requires updating once we have that back.

Motus bot
~~~~~~~~~

An Eggdrop IRC bot that automatically joins the **#motus** channel to play
an IRC variant of the game of `Motus
<https://fr.wikipedia.org/wiki/Motus_(jeu_t%C3%A9l%C3%A9vis%C3%A9)>`_. To start
a game, simply say in the channel::

    !motus

For the full documentation of the bot commands, check out the `Motus bot
homepage <https://scripts.eggdrop.fr/details-Motus-s2.html>`_.

Teeworlds Server
----------------

A Teeworlds game server named "Prologin" runs as ``teeworlds-server.service``.
It automatically enables everyone on the LAN to play.

World of Warcraft Server
------------------------

It is possible to setup a World of Warcraft Server, however the setup is a bit
complex and not really automated. Instructions for the setup are available
here: https://github.com/seirl/prologin-sadm-wow

This setup is based on the open-source `CMaNGOS <https://cmangos.net/>`_ server
implementation.

The repository also contains:

- a ``udbsync_mangos`` service that synchronises the World of Warcraft accounts
  from UDB (and automatically adds the staff as Game Masters).
- a ``wow`` wrapper script that symlinks the WoW data files in the user homes
  to allow them to keep their own configuration between runs without storing
  the entire game in their home.
