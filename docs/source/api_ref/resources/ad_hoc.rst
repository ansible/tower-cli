Ad Hoc Commands
===============

Description
-----------

This resource is used for managing and executing ad hoc commands via Tower. While the rest CRUD operations follow
the common usage pattern, an ad hoc command resource cannot be created via the normal way of calling ``create``,
but only be created on-the-fly via ``launch``.

Fields Table
------------
.. <table goes here>

+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|name            |type                |help_text                  |read_only |unique |filterable |required |
+================+====================+===========================+==========+=======+===========+=========+
|job_explanation |String              |The job_explanation field. |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|created         |String              |The created field.         |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|status          |String              |The status field.          |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|elapsed         |String              |The elapsed field.         |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|job_type        |Choices: run,check  |The job_type field.        |False     |False  |True       |True     |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|inventory       |Resource inventory  |The inventory field.       |False     |False  |True       |True     |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|limit           |String              |The limit field.           |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|credential      |Resource credential |The credential field.      |False     |False  |True       |True     |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|module_name     |String              |The module_name field.     |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|module_args     |String              |The module_args field.     |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|forks           |int                 |The forks field.           |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|verbosity       |mapped_choice       |The verbosity field.       |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|become_enabled  |bool                |The become_enabled field.  |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+
|diff_mode       |bool                |The diff_mode field.       |False     |False  |True       |False    |
+----------------+--------------------+---------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.ad_hoc.Resource
   :members: cancel, delete, get, launch, list, monitor, relaunch, status, wait
