Inventory
=========

Description
-----------

This resource is used for managing inventory resources in Tower.

Fields Table
------------
.. <table goes here>

+-------------+----------------------+-----------------------------------------------+----------+-------+-----------+---------+
|name         |type                  |help_text                                      |read_only |unique |filterable |required |
+=============+======================+===============================================+==========+=======+===========+=========+
|name         |String                |The name field.                                |False     |True   |True       |True     |
+-------------+----------------------+-----------------------------------------------+----------+-------+-----------+---------+
|description  |String                |The description field.                         |False     |False  |True       |False    |
+-------------+----------------------+-----------------------------------------------+----------+-------+-----------+---------+
|organization |Resource organization |The organization field.                        |False     |False  |True       |True     |
+-------------+----------------------+-----------------------------------------------+----------+-------+-----------+---------+
|variables    |variables             |Inventory variables, use "@" to get from file. |False     |False  |True       |False    |
+-------------+----------------------+-----------------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.inventory.Resource
   :members: copy, create, delete, get, list, modify
