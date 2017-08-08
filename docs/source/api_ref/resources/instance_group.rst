Instance Group
==============

Description
-----------

This resource is used for managing instance group resources in Tower. Note since instance groups are read-only
in Tower, only ``get`` and ``list`` methods are available for this resource.

Fields Table
------------
.. <table goes here>

+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|name              |type   |help_text                    |read_only |unique |filterable |required |
+==================+=======+=============================+==========+=======+===========+=========+
|name              |String |The name field.              |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|capacity          |int    |The capacity field.          |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|consumed_capacity |int    |The consumed_capacity field. |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.instance_group.Resource
   :members: get, list
