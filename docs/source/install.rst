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

If you are not familar with ansible-tower-cli's dependency tree, we suggested building source in a fresh
`virtual environment <http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/>`__
to prevent any dependency conflict.

Install the Right Version
-------------------------

REST API of Ansible Tower is versioned, and each API version is supported by a subset,
rather than all, of ansible-tower-cli versions. Make sure you are pairing
your Tower backend with a right version of ansible-tower-cli, specifically:

- If you are using Tower 3.2.0 and beyond, API v2 is available, you should use ansible-tower-cli
  3.2.0 and beyond.
- If you are using a Tower version lower than 3.2.0, only API v1 is available,
  you should use ansible-tower-cli versions lower than 3.2.0.
