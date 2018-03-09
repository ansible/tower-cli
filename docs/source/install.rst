.. _installation:

Installation
============

Install from Package Managers
-----------------------------

Tower CLI is available as a package on
`PyPI <https://pypi.python.org/pypi/ansible-tower-cli>`__.

The preferred way to install is through pip:

.. code:: bash

    $ pip install ansible-tower-cli

Build from Source
-----------------

ansible-tower-cli may also be consumed and built directly from source.

.. code:: bash

    $ git clone https://github.com/ansible/tower-cli.git

Then, inside ``tower_cli`` directory, run

.. code:: bash

   $ make install

and follow the instructions.

If you are not familiar with ansible-tower-cli's dependency tree, we suggested building source in a fresh
`virtual environment <http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/>`__
to prevent any dependency conflict.
