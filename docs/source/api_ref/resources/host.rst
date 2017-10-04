Host
====

Description
-----------

This resource is used for managing host resources in Tower. It can also associate/disassociate a group
to/from a host.

Fields Table
------------
.. <table goes here>

+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+
|name               |type               |help_text                                 |read_only |unique |filterable |required |
+===================+===================+==========================================+==========+=======+===========+=========+
|name               |String             |The name field.                           |False     |True   |True       |True     |
+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+
|description        |String             |The description field.                    |False     |False  |True       |False    |
+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+
|inventory          |Resource inventory |The inventory field.                      |False     |False  |True       |True     |
+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+
|enabled            |bool               |The enabled field.                        |False     |False  |True       |False    |
+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+
|variables          |variables          |Host variables, use "@" to get from file. |False     |False  |True       |False    |
+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+
|insights_system_id |String             |The insights_system_id field.             |False     |False  |True       |False    |
+-------------------+-------------------+------------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.host.Resource
   :members: copy, create, delete, get, list, modify, associate, disassociate, insights, list_facts
