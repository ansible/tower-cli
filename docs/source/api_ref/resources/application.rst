Application
===========

Description
-----------

This resource is used for managing application resources in Tower.

Fields Table
------------
.. <table goes here>

+-------------------------+--------------------------------------------------------------------+------------------------------------+----------+-------+-----------+---------+
|name                     |type                                                                |help_text                           |read_only |unique |filterable |required |
+=========================+====================================================================+====================================+==========+=======+===========+=========+
|name                     |String                                                              |The name field.                     |False     |True   |True       |True     |
+-------------------------+--------------------------------------------------------------------+------------------------------------+----------+-------+-----------+---------+
|client_type              |Choices: public, confidential                                       |The client_type field.              |False     |False  |True       |True     |
+-------------------------+--------------------------------------------------------------------+------------------------------------+----------+-------+-----------+---------+
|organization             |Resource organization                                               |The organization field.             |False     |False  |True       |True     |
+-------------------------+--------------------------------------------------------------------+------------------------------------+----------+-------+-----------+---------+
|authorization_grant_type |Choices: authorization-code, implicit, password, client-credentials |The authorization_grant_type field. |False     |False  |True       |True     |
+-------------------------+--------------------------------------------------------------------+------------------------------------+----------+-------+-----------+---------+
|skip_authorization       |BOOL                                                                |The skip_authorization field.       |False     |False  |True       |False    |
+-------------------------+--------------------------------------------------------------------+------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.application.Resource
   :members: copy, create, delete, get, list, modify
