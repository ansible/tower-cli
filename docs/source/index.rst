Ansible Tower CLI
=================

**tower-cli** is a command line tool for Ansible Tower. It allows Tower
commands to be easily run from the Unix command line. It can also be
used as a client library for other python apps, or as a reference for
others developing API interactions with Tower's REST API.

About Tower
-----------

`Ansible Tower <https://www.ansible.com/tower>`__ is a GUI and REST interface
for Ansible that supercharges it by adding RBAC, centralized logging,
autoscaling/provisioning callbacks, graphical inventory editing, and
more.

Tower is free to use for up to 30 days or 10 nodes. Beyond this, `a
license is required <https://www.ansible.com/pricing>`__.

Capabilities
------------

This command line tool sends commands to the Tower API. It is capable of
retrieving, creating, modifying, and deleting most resources within Tower.

A few potential uses include:

-  Launching playbook runs (for instance, from Jenkins, TeamCity,
   Bamboo, etc)
-  Checking on job statuses
-  Rapidly creating objects like organizations, users, teams, and more

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   install.rst
   quickstart.rst
   cli_ref/index.rst
   api_ref/index.rst
   CONTRIBUTING.rst
   HISTORY.rst
