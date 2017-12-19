Job
===

Description
-----------

This resource is used for managing jobs and launching job templates via Tower. Note for historical purposes,
launching a job template is linked to job, rather than job template.

Fields Table
------------
.. <table goes here>

+----------------+----------------------+---------------------------+----------+-------+-----------+---------+
|name            |type                  |help_text                  |read_only |unique |filterable |required |
+================+======================+===========================+==========+=======+===========+=========+
|job_template    |Resource job_template |The job_template field.    |False     |False  |True       |False    |
+----------------+----------------------+---------------------------+----------+-------+-----------+---------+
|job_explanation |String                |The job_explanation field. |True      |False  |True       |False    |
+----------------+----------------------+---------------------------+----------+-------+-----------+---------+
|created         |String                |The created field.         |False     |False  |True       |False    |
+----------------+----------------------+---------------------------+----------+-------+-----------+---------+
|status          |String                |The status field.          |False     |False  |True       |False    |
+----------------+----------------------+---------------------------+----------+-------+-----------+---------+
|elapsed         |String                |The elapsed field.         |False     |False  |True       |False    |
+----------------+----------------------+---------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.job.Resource
   :members: cancel, delete, get, launch, list, monitor, relaunch, status, stdout, wait
