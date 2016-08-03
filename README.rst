|Build Status| |Coverage Status| |Version| |Downloads| |License|
|Supported Python Versions|

Welcome to tower-cli
====================

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
retrieving, creating, modifying, and deleting most objects within Tower.

A few potential uses include:

-  Launching playbook runs (for instance, from Jenkins, TeamCity,
   Bamboo, etc)
-  Checking on job statuses
-  Rapidly creating objects like organizations, users, teams, and more

Installation
------------

Tower CLI is available as a package on
`PyPI <https://pypi.python.org/pypi/ansible-tower-cli>`__.

The preferred way to install is through pip:

.. code:: bash

    $ pip install ansible-tower-cli

The main branch of this project may also be consumed directly from
source.

Configuration
-------------

Configuration can be set in several places: ``tower-cli`` can edit its
own configuration, or users can directly edit the configuration file.

Set configuration with tower-cli config.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The preferred way to set configuration is with the ``tower-cli config``
command. The syntax is:

.. code:: bash

    $ tower-cli config key value

By issuing ``tower-cli config`` with no arguments, you can see a full
list of configuration options and where they are set.

In most cases, you must set at least three configuration
options--\ ``host``, ``username``, and ``password``--which correspond to
the location of your Ansible Tower instance and your credentials to
authenticate to Tower.

.. code:: bash

    $ tower-cli config host tower.example.com
    $ tower-cli config username leeroyjenkins
    $ tower-cli config password myPassw0rd

Write to the config files directly.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The configuration file can also be edited directly. A configuration file
is a simple file with keys and values, separated by a colon (``:``) or by
the equality sign (``=``):

.. code:: yaml

    host: tower.example.com
    username: admin
    password: p4ssw0rd

The locations searched for the configuration file are given below.

File Locations
~~~~~~~~~~~~~~

The order of precedence for configuration file locations is as follows,
from least to greatest:

-  internal defaults
-  ``/etc/tower/tower_cli.cfg`` (written using
   ``tower-cli config --global``)
-  ``~/.tower_cli.cfg`` (written using ``tower-cli config``)
-  run-time paramaters

Usage
-----

CLI invocation generally follows this format:

.. code:: bash

    $ tower-cli {resource} {action} ...

The "resource" is a type of object within Tower (a noun), such as
``user``, ``organization``, ``job_template``, etc.; resource names are
always singular in Tower CLI (so it is ``tower-cli user``, never
``tower-cli users``).

The "action" is the thing you want to do (a verb). Most Tower CLI
resources have the following actions--\ ``get``, ``list``, ``create``,
``modify``, and ``delete``--and have options corresponding to fields on
the object in Tower.

Some examples:

.. code:: bash

    # List all users.
    $ tower-cli user list

    # List all non-superusers
    $ tower-cli user list --is-superuser=false

    # Get the user with the ID of 42.
    $ tower-cli user get 42

    # Get the user with the given username.
    $ tower-cli user get --username=guido

    # Create a new user.
    $ tower-cli user create --username=guido --first-name=Guido \
                            --last-name="Van Rossum" --email=guido@python.org \
                            --password=password1234

    # Modify an existing user.
    # This would modify the first name of the user with the ID of "42" to "Guido".
    $ tower-cli user modify 42 --first-name=Guido

    # Modify an existing user, lookup by username.
    # This would use "username" as the lookup, and modify the first name.
    # Which fields are used as lookups vary by resource, but are generally
    # the resource's name.
    $ tower-cli user modify --username=guido --first-name=Guido

    # Delete a user.
    $ tower-cli user delete 42

    # Launch a job.
    $ tower-cli job launch --job-template=144

    # Monitor a job.
    $ tower-cli job monitor 95

When in doubt, help is available!

.. code:: bash

    $ tower-cli # help
    $ tower-cli user --help # resource specific help
    $ tower-cli user create --help # command specific help

Specify extra variables.
~~~~~~~~~~~~~~~~~~~~~~~~

There are a number of ways to pass extra variables to the Tower server
when launching a job:

-  Pass data in a file using the flag ``--extra-vars="@filename.yml"``
-  Include yaml data at runtime with the flag
   ``--extra-vars="var: value"``
-  A command-line editor automatically pops up when the job template is
   marked to prompt on launch
-  If the job template has extra variables, these are not over-ridden

These methods can also be combined. For instance, if you give the flag
multiple times on the command line, specifying a file in addition to
manually giving extra variables, these two sources are combined and sent
to the Tower server.

.. code:: bash

    # Launch a job with extra variables from filename.yml, and also a=5
    $ tower-cli job launch --job-template=1 --extra-vars="a=5 b=3" \
                                            --extra-vars="@filename.yml"

    # Create a job template with that same set of extra variables
    $ tower-cli job_template create --name=test_job_template --project=1 \
                                    --inventory=1 --playbook=helloworld.yml \
                                    --machine-credential=1 --extra-vars="a=5 b=3" \
                                    --extra-vars="@filename.yml"

You may not combine multiple sources when modifying a job template.
Whitespace can be used in strings like
``--extra-vars="a='white space'"``, and list-valued parameters can be
sent as JSON or YAML, but not key=value pairs. For instance,
``--extra-vars="a: [1, 2, 3, 4, 5]"`` sends the parameter "a" with that
list as its value.

SSL warnings
~~~~~~~~~~~~

By default tower-cli will raise an error if the SSL certificate of the
Tower server cannot be verified. To allow unverified SSL connections,
set the config variable ``verify_ssl`` to true. To allow it for a single
command, add the --insecure flag.

.. code:: bash

    # Disable insecure connection warnings permanently
    $ tower-cli config verify_ssl false

    # Disable insecure connection warnings for just this command
    $ tower-cli job_template list --insecure

Bash script example
~~~~~~~~~~~~~~~~~~~

If you want an example for a particular case that this README does not
cover, the development distribution of tower-cli includes a script that
populates the Tower server with fake data using tower-cli commands.
These attempt to cover most of the available features and can be found
in the folder `/docs/examples/ <https://github.com/ansible/tower-cli/tree/master/docs/examples>`__.

License
-------

While Tower is commercially licensed software, *tower-cli* is an open
source project, and contributions are highly encouraged. Specifically,
this CLI project is licensed under the Apache 2.0 license. Pull requests
and tickets filed in GitHub are welcome.

\(C) 2016, Ansible Tower by Red Hat 

.. |Build Status| image:: https://img.shields.io/travis/ansible/tower-cli.svg
   :target: https://travis-ci.org/ansible/tower-cli
.. |Coverage Status| image:: https://img.shields.io/coveralls/ansible/tower-cli.svg
   :target: https://coveralls.io/r/ansible/tower-cli
.. |Version| image:: https://img.shields.io/pypi/v/ansible-tower-cli.svg
   :target: https://pypi.python.org/pypi/ansible-tower-cli/
.. |Downloads| image:: https://img.shields.io/pypi/dm/ansible-tower-cli.svg
   :target: https://pypi.python.org/pypi/ansible-tower-cli/
.. |License| image:: https://img.shields.io/pypi/l/ansible-tower-cli.svg
   :target: https://pypi.python.org/pypi/ansible-tower-cli/
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/ansible-tower-cli.svg
   :target: https://pypi.python.org/pypi/ansible-tower-cli/
