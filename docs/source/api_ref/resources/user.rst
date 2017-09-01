User
====

Description
-----------

This resource is used for managing users in Tower.

Fields Table
------------
.. <table goes here>

+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|name              |type   |help_text                    |read_only |unique |filterable |required |
+==================+=======+=============================+==========+=======+===========+=========+
|username          |String |The username field.          |False     |True   |True       |True     |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|password          |String |The password field.          |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|email             |String |The email field.             |False     |True   |True       |True     |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|first_name        |String |The first_name field.        |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|last_name         |String |The last_name field.         |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|is_superuser      |bool   |The is_superuser field.      |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+
|is_system_auditor |bool   |The is_system_auditor field. |False     |False  |True       |False    |
+------------------+-------+-----------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.user.Resource
   :members: copy, create, delete, get, list, modify
