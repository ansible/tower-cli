Organization
============

Description
-----------

This resource is used for managing organization resources in Tower. It can also perform some
associations/disassociations.

Fields Table
------------
.. <table goes here>

+------------+-------+-----------------------+----------+-------+-----------+---------+
|name        |type   |help_text              |read_only |unique |filterable |required |
+============+=======+=======================+==========+=======+===========+=========+
|name        |String |The name field.        |False     |True   |True       |True     |
+------------+-------+-----------------------+----------+-------+-----------+---------+
|description |String |The description field. |False     |False  |True       |False    |
+------------+-------+-----------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.organization.Resource
   :members: copy, create, delete, get, list, modify, associate, disassociate, associate_admin, disassociate_admin, associate_ig, disassociate_ig
