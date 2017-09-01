Label
=====

Description
-----------

This resource is used for managing label resources in Tower.

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

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.label.Resource
   :members: copy, create, get, list, modify
