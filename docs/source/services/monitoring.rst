Monitoring services
===================

Monitoring is the art of knowning when something fails, and getting as much
information as possible to solve the issue.

We use `prometheus <http://prometheus.io/>`_ as our metrics monitoring backend
and `grafana <https://grafana.com/>`_ for the dashboards. We use `elasticsearch
<https://www.elastic.co/products/elasticsearch>`_ to store logs and `kibana
<https://www.elastic.co/products/kibana>`_ to search through them.

We use a separate machine for monitoring (called, surprisingly,
``monitoring``), as we want to isolate it from the core services, because we
don't want the monitoring workload to impact other services, and vice versa.

Prometheus
----------

Prometheus is a monitoring system that stores a backlog of metrics as time
series in its database. Prometheus runs on the ``monitoring`` machine as
``prometheus.service``.

All the machines in the infrastructure have a
``prometheus-node-exporter.service`` service running on them, which
periodically exports system information to Prometheus.

Most SADM services come with built-in monitoring and will be monitored as
soon as prometheus is started.

The following endpoints are available for Prometheus to fetch metrics:

- ``http://udb/metrics``
- ``http://mdb/metrics``
- ``http://concours/metrics``
- ``http://masternode:9021``
- ``http://presencesync:9030``
- hfs: each hfs exports its metrics on ``http://hfsx:9030``
- workernode: each workernode exports its metrics on ``http://MACHINE:9020``.

**TODO**: add more information on how to use alerting.

Grafana
-------

Grafana is a web service available at ``http://grafana/`` that allows you to
visualize the information stored in Prometheus.

To access it, the username is ``admin`` and the password is the value of
``grafana_admin_password`` in your Ansible inventory. It is also possible to
allow guest user access, so that contestants will also be able to see the state
of the infrastructure.

Some built-in dashboards are automatically added to Grafana during the
installation, and show the current state of the machines and main services.

Monitoring screen how-to
~~~~~~~~~~~~~~~~~~~~~~~~

We like to have a giant monitoring screen showing sexy graphs to the roots
because it's cool.

Start multiple ``chromium --app http://grafana/`` to open a monitoring web
view.

We look at both the ``System`` and ``Masternode`` dashboards from grafana.

Disable the screen saver and DPMS using on the monitoring display using::

  $ xset -dpms
  $ xset s off

Icinga
------

Icinga aggregates the logs of all the machines in the infrastructure, and
stores it in an ElasticSearch database. It allows you to quickly search for
failures in the logs of the entire setup, including the diskless machines.

These logs are exported through the
``journalbeat.service`` service that is installed on all the machines and
extracts the logs from the systemd journal.

**TODO**: add more information on how to use Icinga

Icinga runs on ``monitoring`` as ``icinga.service``.
