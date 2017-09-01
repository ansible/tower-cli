Instance
========

Description
-----------

This resource is used for managing instance resources in Tower. Note since instances are read-only in Tower,
only ``get`` and ``list`` methods are available for this resource.

Fields Table
------------
.. <table goes here>

+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|name              |type   |help_text                    |read_only |unique |filterable |required |
+==================+=======+=============================+==========+=======+===========+=========+
|uuid              |String |The uuid field.              |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|hostname          |String |The hostname field.          |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|version           |String |The version field.           |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|capacity          |int    |The capacity field.          |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|consumed_capacity |int    |The consumed_capacity field. |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.instance.Resource
   :members: get, list
