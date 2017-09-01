Inventory Script
================

Description
-----------

This resource is used for managing inventory script resources in Tower.

Fields Table
------------
.. <table goes here>

+-------------+----------------------+----------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|name         |type                  |help_text                                                                               |read_only |unique |filterable |required |
+=============+======================+========================================================================================+==========+=======+===========+=========+
|name         |String                |The name field.                                                                         |False     |True   |True       |True     |
+-------------+----------------------+----------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|description  |String                |The description field.                                                                  |False     |False  |True       |False    |
+-------------+----------------------+----------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|script       |variables             |Script code to fetch inventory, prefix with "@" to use contents of file for this field. |False     |False  |True       |True     |
+-------------+----------------------+----------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|organization |Resource organization |The organization field.                                                                 |False     |False  |True       |True     |
+-------------+----------------------+----------------------------------------------------------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.inventory_script.Resource
   :members: copy, create, delete, get, list, modify
