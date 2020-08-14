Web services
=============

These web services are usually installed on the ``web`` machine. They are
important services like documentations, wikis, bug tracking systems etc. that
make the contest experience better.

Homepage
--------

Homepage is a landing page for all contestants, available at
``http://homepage``. It is a simple page that shows a list of links to the
available services.

Homepage is a Django application that allows the staff to easily add new links
by going to the admin panel here: http://homepage/admin

This service runs as ``homepage.service``. Users are automatically synchronized
from UDB with ``udbsync_django@homepage``.

Docs
----

Documentation of the finals (Stechec2 usage, game API, FAQ, ...) can be hosted
on ``http://docs/``. After the initial setup, this page is just an empty page
containing instructions on how to upload content here.

For more flexibility, so that the staff working on the game rules can easily
make changes to the documentation, the deployment of this documentation is
manual. Building and deploying the documentation should look like this::

    cd prologin20XX/docs
    make html
    rsync --info=progress2 -r _build/html/* root@web:/var/prologin/docs

It is recommanded to add this line as a ``make deploy`` rule in the
documentation Makefile.

DevDocs
-------

The language documentations are available at ``http://devdocs/``. It is a
self-hosted instance of `DevDocs <https://devdocs.io/>`_ that allows people to
easily browse the documentation of the supported languages without having
access to the internet.

It is possible for each user to enable or disable the documentation of their
languages of choice, so that when they search for a keyword they only see the
relevant parts of the documentation.

This service runs as ``devdocs.service``.

Wiki
-----

A Wiki service is available at ``http://wiki``. It is a self-hosted
instance of `django-wiki <https://github.com/django-wiki/django-wiki>`_ that
everyone can edit with any information they want.

**TODO**: add documentation on how to create the initial pages as staff.

This service runs as ``wiki.service``. Users are automatically synchronized
from UDB with ``udbsync_django@wiki``.

Paste
-----

A pastebin service is available at ``http://paste``. It is a self-hosted
instance of `dpaste <https://github.com/bartTC/dpaste>`_, where everyone can
paste anything with syntax highlighting.

This service runs as ``paste.service``. Users are automatically synchronized
from UDB with ``udbsync_django@paste``.

Bug tracker
-----------

**TODO**: We ditched Redmine and we are working on a good replacement based on
Django. This section should be updated once it's ready.
