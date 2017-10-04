Credential
==========

Description
-----------

This resource is used for managing credential resources in Tower.

Fields Table
------------
.. <table goes here>

+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|name            |type                     |help_text                  |read_only |unique |filterable |required |
+================+=========================+===========================+==========+=======+===========+=========+
|name            |String                   |The name field.            |False     |True   |True       |True     |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|description     |String                   |The description field.     |False     |False  |True       |False    |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|user            |Resource user            |The user field.            |False     |False  |True       |False    |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|team            |Resource team            |The team field.            |False     |False  |True       |False    |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|organization    |Resource organization    |The organization field.    |False     |False  |True       |False    |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|credential_type |Resource credential_type |The credential_type field. |False     |False  |True       |True     |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+
|inputs          |structured_input         |The inputs field.          |False     |False  |True       |False    |
+----------------+-------------------------+---------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.credential.Resource
   :members: copy, create, delete, get, list, modify
