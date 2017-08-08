Quick Start
===========

This chapter walks you through the general process of setting up and using Tower CLI. It starts with CLI usage
and ends with API usage. For details, please see API and CLI references in subsequent chapters.

It is assumed you have a Tower backend available to talk to and Tower CLI installed. Please see 'Installation'
chapter for instructions on installing Tower CLI.

First of all, make sure you know the name of the Tower backend, like ``tower.example.com``, as well as the
username/password set of a user in that Tower backend, like ``user/pass``. These are connection information
necessary for Tower CLI to communicate to Tower. With these prerequisites, run

.. code:: bash

    $ tower-cli config host tower.example.com
    $ tower-cli config username user
    $ tower-cli config password pass

The first Tower CLI command, ``tower-cli config``. writes the connection informations to a configuration file
(``~/.tower-cli.cfg`` in this case), and subsequent commands and API calls will read this file, extract connection
information and talk to Tower as the specified user. See details of Tower CLI configuration in API reference and
``tower-cli config --help``.

Then, use Tower CLI to actually control your Tower backend. The CRUD operations against almost every Tower resource
can be done using Tower CLI. Suppose we want to see the available job templates to choose for running:

.. code:: bash

   $ tower-cli job_template list

A command-line-formatted table would show up, giving general summary of (maybe part of) the available job templates.
Note the actual HTTP(S) response is in JSON format, you can choose to see the JSON response itself instead using
``--format`` flag.

.. code:: bash

   $ tower-cli job_template list --format json

Other than normal resource CRUD operations, Tower CLI can be used to launch and monitor executable resources like
job templates and projects. Suppose we have had the ID of the job template we want to execute from the previous
``list`` call, we can launch the job template by:

.. code:: bash

   $ tower-cli job launch -J <ID of the job template> --monitor

This command will POST to Tower backend to launch the job template to be executed, and monitor the triggered job
run by dumping job stdout in real-time, just as what Tower UI does.

The best CLI help you can get is from ``--help`` option. Each Tower CLI command is guaranteed to have a ``--help``
option instructing the command hierarchy and detailed usage like command format the meaning of each available
command option. Use ``--help`` whenever you have questions about a Tower CLI command.

Under the hood, Tower CLI is composed of an API engine and a wrapper layer around it to make it a CLI. Using API
of Tower CLI gives you finer-grained control and makes it easy to integrate Tower CLI into your python scripts.

The usage of Tower CLI's API is two-phased: get resource and call its API. First you get the type of resource
you want to interact with.

.. code:: python

  import tower_cli

  res = tower_cli.get_resource('job_template')

Due to legacy reasons, we use a non-traditional way of importing resource class, ``tower_cli.get_resource``.
Alternatively, you can use the old way by using import alias:

.. code:: python

  import tower_cli.resources.job_template import Resource as JobTemplate

  res = JobTemplate()

Then, interaction with Tower would be as easy as straight-forward resource public method calls, like

.. code:: python

  jt_list = res.list()
  tower_cli.get_resource('job').launch(job_template=1, monitor=True)

More API usage can be found in API reference.
