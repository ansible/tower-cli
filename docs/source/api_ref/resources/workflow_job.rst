Workflow Job
============

Description
-----------

This resource is used for managing workflow jobs and launching workflow job templates via Tower.

Fields Table
------------
.. <table goes here>

+----------------------+------------------+---------------------------------+----------+-------+-----------+---------+
|name                  |type              |help_text                        |read_only |unique |filterable |required |
+======================+==================+=================================+==========+=======+===========+=========+
|workflow_job_template |Resource workflow |The workflow_job_template field. |False     |False  |True       |True     |
+----------------------+------------------+---------------------------------+----------+-------+-----------+---------+
|extra_vars            |variables         |The extra_vars field.            |False     |False  |True       |False    |
+----------------------+------------------+---------------------------------+----------+-------+-----------+---------+
|created               |String            |The created field.               |False     |False  |True       |False    |
+----------------------+------------------+---------------------------------+----------+-------+-----------+---------+
|status                |String            |The status field.                |False     |False  |True       |False    |
+----------------------+------------------+---------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.workflow_job.Resource
   :members: cancel, delete, get, launch, list, monitor, relaunch, status, wait
