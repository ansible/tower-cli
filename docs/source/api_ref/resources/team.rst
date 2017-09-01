Team
====

Description
-----------

This resource is used for managing teams and their users in Tower.

Fields Table
------------
.. <table goes here>

+-------------+----------------------+------------------------+----------+-------+-----------+---------+
|name         |type                  |help_text               |read_only |unique |filterable |required |
+=============+======================+========================+==========+=======+===========+=========+
|name         |String                |The name field.         |False     |True   |True       |True     |
+-------------+----------------------+------------------------+----------+-------+-----------+---------+
|organization |Resource organization |The organization field. |False     |False  |True       |True     |
+-------------+----------------------+------------------------+----------+-------+-----------+---------+
|description  |String                |The description field.  |False     |False  |True       |False    |
+-------------+----------------------+------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.team.Resource
   :members: copy, create, delete, get, list, modify, associate, disassociate
