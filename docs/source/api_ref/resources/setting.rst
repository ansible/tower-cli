Tower Configuration
===================

Description
-----------

This resource is used for managing tower configurations in Tower.

Fields Table
------------
.. <table goes here>

+------+----------+-----------------+----------+-------+-----------+---------+
|name  |type      |help_text        |read_only |unique |filterable |required |
+======+==========+=================+==========+=======+===========+=========+
|value |variables |The value field. |False     |False  |True       |True     |
+------+----------+-----------------+----------+-------+-----------+---------+

.. <table goes here>

API Specification
-----------------
.. autoclass:: tower_cli.resources.setting.Resource
   :members: copy, get, list, modify
