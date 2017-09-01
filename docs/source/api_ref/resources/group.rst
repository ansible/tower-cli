Group
=====

Description
-----------

This resource is used for managing group resources in Tower. It can also associate/disassociate one group
to/from another group.

Fields Table
------------
.. <table goes here>

+------------+-------------------+-------------------------------------------+----------+-------+-----------+---------+
|name        |type               |help_text                                  |read_only |unique |filterable |required |
+============+===================+===========================================+==========+=======+===========+=========+
|name        |String             |The name field.                            |False     |True   |True       |True     |
+------------+-------------------+-------------------------------------------+----------+-------+-----------+---------+
|description |String             |The description field.                     |False     |False  |True       |False    |
+------------+-------------------+-------------------------------------------+----------+-------+-----------+---------+
|inventory   |Resource inventory |The inventory field.                       |False     |False  |True       |True     |
+------------+-------------------+-------------------------------------------+----------+-------+-----------+---------+
|variables   |variables          |Group variables, use "@" to get from file. |False     |False  |True       |False    |
+------------+-------------------+-------------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.group.Resource
   :members: copy, create, delete, get, modify, associate, disassociate, list
