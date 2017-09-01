Workflow Node
=============

Description
-----------

This resource is used for managing workflow job template nodes in Tower. It can also used for building workflow
topology by associating/disassociating nodes.

Fields Table
------------
.. <table goes here>

+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|name                  |type                |help_text                        |read_only |unique |filterable |required |
+======================+====================+=================================+==========+=======+===========+=========+
|workflow_job_template |Resource workflow   |The workflow_job_template field. |False     |False  |True       |True     |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|unified_job_template  |String              |The unified_job_template field.  |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|inventory             |Resource inventory  |The inventory field.             |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|credential            |Resource credential |The credential field.            |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|job_type              |String              |The job_type field.              |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|job_tags              |String              |The job_tags field.              |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|skip_tags             |String              |The skip_tags field.             |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+
|limit                 |String              |The limit field.                 |False     |False  |True       |False    |
+----------------------+--------------------+---------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.node.Resource
   :members: copy, create, delete, get, list, modify, associate_always_node, disassociate_always_node, associate_failure_node, disassociate_failure_node, associate_success_node, disassociate_success_node
