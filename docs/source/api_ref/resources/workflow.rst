Workflow Job Template
=====================

Description
-----------

This resource is used for managing workflow job template resources in Tower. It is also responsible for
associating/disassociating labels and notification templates to/from an existing job template. There is
yet another 2 custom commands, ``survey``, used for getting survey specification of a workflow job template,
and ``schema``, used for build workflow topology via YAML/JSON content.

Workflow Schema
---------------

Workflow ``schema`` is a handy API to bulk-create or bulk-update a workflow node network. The schema is a JSON-
or YAML-formatted string defining the hierarchy structure that connects the nodes. Names, as well as other valid
parameters for node creation, are acceptable inside of the node's entry inside the schema definition.

Links must be declared as a list under a key that starts with "success", "failure", or "always". The following is
an example of a valid YAML-formatted schema definition.

::

  """
  - job_template: Hello world
    failure:
    - inventory_source: AWS servers (AWS servers - 42)
    success:
    - project: Ansible Examples
      always:
      - job_template: Echo variable
        success:
        - job_template: Scan localhost
  """

The workflow schema feature populates the workflow node network based on the hierarchy structure. Before creating
each node, it attempts to find an existing node with the specified properties in that location in the tree, and
will not create a new node if it exists. Also, if an existing node has no correspondence in the schema, the entire
sub-tree based on that node will be deleted.

Thus, after running the schema command, the resulting workflow node network topology will always be exactly the
same as what is specified in the given schema file. To continue with the previous example, subsequent invocations
of:

::

  wfjt.schema('workflow1', '<schema spec>')

should not change the network of ``workflow1``, since schema detail is unchanged. However

::

  wfjt.schema('workflow1', '<new schema spec>')

will modify node network topology of ``workflow1`` to exactly the same as what is specified in the new schema spec.

Fields Table
------------
.. <table goes here>

+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|name               |type                  |help_text                                                                                                                                                  |read_only |unique |filterable |required |
+===================+======================+===========================================================================================================================================================+==========+=======+===========+=========+
|name               |String                |The name field.                                                                                                                                            |False     |True   |True       |True     |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|description        |String                |The description field.                                                                                                                                     |False     |False  |True       |False    |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|extra_vars         |variables             |Extra variables used by Ansible in YAML or key=value format. Use @ to get YAML from a file. Use the option multiple times to add multiple extra variables. |False     |False  |True       |False    |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|organization       |Resource organization |The organization field.                                                                                                                                    |False     |False  |True       |False    |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|survey_enabled     |bool                  |Prompt user for job type on launch.                                                                                                                        |False     |False  |True       |False    |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|allow_simultaneous |bool                  |The allow_simultaneous field.                                                                                                                              |False     |False  |True       |False    |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+
|survey_spec        |variables             |On write commands, perform extra POST to the survey_spec endpoint.                                                                                         |False     |False  |True       |False    |
+-------------------+----------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.workflow.Resource
   :members: copy, create, delete, get, list, modify, survey, associate_label, associate_notification_template, disassociate_notification_template, associate_label, disassociate_label, schema
