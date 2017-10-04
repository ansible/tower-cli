Project
=======

Description
-----------

This resource is used for managing and executing projects via Tower. Note project updates are triggered
via ``update`` method.

Fields Table
------------
.. <table goes here>

+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|name                     |type                  |help_text                                                |read_only |unique |filterable |required |
+=========================+======================+=========================================================+==========+=======+===========+=========+
|name                     |String                |The name field.                                          |False     |True   |True       |True     |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|description              |String                |The description field.                                   |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|organization             |Resource organization |The organization field.                                  |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_type                 |mapped_choice         |The scm_type field.                                      |False     |False  |True       |True     |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_url                  |String                |The scm_url field.                                       |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|local_path               |String                |For manual projects, the server playbook directory name. |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_branch               |String                |The scm_branch field.                                    |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_credential           |Resource credential   |The scm_credential field.                                |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_clean                |bool                  |The scm_clean field.                                     |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_delete_on_update     |bool                  |The scm_delete_on_update field.                          |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_update_on_launch     |bool                  |The scm_update_on_launch field.                          |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|scm_update_cache_timeout |int                   |The scm_update_cache_timeout field.                      |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+
|job_timeout              |int                   |The timeout field (in seconds).                          |False     |False  |True       |False    |
+-------------------------+----------------------+---------------------------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.project.Resource
   :members: copy, create, delete, get, list, modify, monitor, status, stdout, update, wait
