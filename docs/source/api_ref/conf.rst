.. _api-ref-conf:

Configuration
=============

In Tower CLI, there are a number of configuration settings available to users. These settings are mostly used to
set up connection details to Tower backend, like hostname of Tower backend and user name/password used for
authentication; some are also used for other purposes, like toggle on/off colored stdout. Here is a list of all
available Tower CLI settings:

+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Key**          | **Value Type / Value Default**                        | **Description**                                                                                                                                            |
+==================+=======================================================+============================================================================================================================================================+
| ``color``        | Boolean/'true'                                        | Whether to use colored output for highlighting or not.                                                                                                     |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``format``        | String with options ('human', 'json', 'yaml')/'human' | Output format. The "human" format is intended for humans reading output on the CLI; the "json" and "yaml" formats provide more data. [CLI use only]        |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``host``          | String/'127.0.0.1'                                    | The location of the Ansible Tower host. HTTPS is assumed as the protocol unless "http://" is explicitly provided.                                          |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``password``      | String/''                                             | Password to use to authenticate to Ansible Tower.                                                                                                          |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``username``      | String/''                                             | Username to use to authenticate to Ansible Tower.                                                                                                          |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``verify_ssl``    | Boolean/'true'                                        | Whether to force verified SSL connections.                                                                                                                 |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``verbose``       | Boolean/'false'                                       | Whether to show information about requests being made.                                                                                                     |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``description_on``| Boolean/'false'                                       | Whether to show description in human-formatted output. [CLI use only]                                                                                      |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``certificate``   | String/''                                             | Path to a custom certificate file that will be used throughout the command. Ignored if `--insecure` flag if set in command or `verify_ssl` is set to false |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
|``use_token``     | Boolean/'false'                                       | Whether to use token-based authentication.  No longer supported in Tower 3.3 and above                                                                     |
+------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Note:** Some settings are marked as 'CLI use only', this means although users are free to set values to those
settings, those settings only affect CLI but not API usage.

.. autoclass:: tower_cli.conf.Settings
   :members: runtime_values
