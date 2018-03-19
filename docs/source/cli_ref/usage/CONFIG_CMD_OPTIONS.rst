.. _cli_ref:

Config Command Options
======================

key-value options available for ``tower-cli config <key> <value>`` command
--------------------------------------------------------------------------

+-------+-------------------+--------------------------------------------------+
| *Key* | *Value            | *Description*                                    |
|       | Type/Default*     |                                                  |
+=======+===================+==================================================+
| ``col | Boolean/'true'    | Whether to use colored output for highlighting   |
| or``  |                   | or not.                                          |
+-------+-------------------+--------------------------------------------------+
| ``for | String with       | Output format. The "human" format is intended    |
| mat`` | options ('human', | for humans reading output on the CLI; the "json" |
|       | 'json',           | and "yaml" formats provide more data.            |
|       | 'yaml')/'human'   |                                                  |
+-------+-------------------+--------------------------------------------------+
| ``hos | String/'127.0.0.1 | The location of the Ansible Tower host. HTTPS is |
| t``   | '                 | assumed as the protocol unless "http://" is      |
|       |                   | explicitly provided.                             |
+-------+-------------------+--------------------------------------------------+
| ``pas | String/''         | Password to use to authenticate to Ansible       |
| sword |                   | Tower.                                           |
| ``    |                   |                                                  |
+-------+-------------------+--------------------------------------------------+
| ``use | String/''         | Username to use to authenticate to Ansible       |
| rname |                   | Tower.                                           |
| ``    |                   |                                                  |
+-------+-------------------+--------------------------------------------------+
| ``ver | Boolean/'true'    | Whether to force verified SSL connections.       |
| ify_s |                   |                                                  |
| sl``  |                   |                                                  |
+-------+-------------------+--------------------------------------------------+
| ``ver | Boolean/'false'   | Whether to show information about requests being |
| bose` |                   | made.                                            |
| `     |                   |                                                  |
+-------+-------------------+--------------------------------------------------+
| ``des | Boolean/'false'   | Whether to show description in human-formatted   |
| cript |                   | output.                                          |
| ion_o |                   |                                                  |
| n``   |                   |                                                  |
+-------+-------------------+--------------------------------------------------+
| ``cer | String/''         | Path to a custom certificate file that will be   |
| tific |                   | used throughout the command. Ignored if          |
| ate`` |                   | ``--insecure`` flag if set in command or         |
|       |                   | ``verify_ssl`` is set to false                   |
+-------+-------------------+--------------------------------------------------+
| ``use | Boolean/'false'   | Whether to use token-based authentication.       |
| _toke |                   |                                                  |
| n``   |                   |                                                  |
+-------+-------------------+--------------------------------------------------+

Environment Variables
---------------------

All of the above options can also be set using environment variables.
The default behavior is to allow environment variables to override your
tower-cli.cfg settings, but they will not override config values that
are passed in on the command line at runtime. Below is a table of the
available environment variables.

Variable Mapping
~~~~~~~~~~~~~~~~

+---------------------------+--------------------+
| *Environment Variable*    | *Tower Config Key* |
+===========================+====================+
| ``TOWER_COLOR``           | ``color``          | 
+---------------------------+--------------------+
| ``TOWER_FORMAT``          | ``format``         |
+---------------------------+--------------------+ 
| ``TOWER_HOST``            | ``host``           |
+---------------------------+--------------------+ 
| ``TOWER_PASSWORD``        | ``password``       |
+---------------------------+--------------------+ 
| ``TOWER_USERNAME``        | ``username``       |
+---------------------------+--------------------+ 
| ``TOWER_VERIFY_SSL``      | ``verify_ssl``     |
+---------------------------+--------------------+ 
| ``TOWER_VERBOSE``         | ``verbose``        |
+---------------------------+--------------------+ 
| ``TOWER_DESCRIPTION_ON``  | ``description_on`` |
+---------------------------+--------------------+
| ``TOWER_CERTIFICATE``     | ``certificate``    | 
+---------------------------+--------------------+
| ``TOWER_USE_TOKEN``       | ``use_token``      |
+---------------------------+--------------------+

Notes
-----

-  Under the hood we use the SSL functionality of requests, however the
   current requests version has checkings on a deprecated SSL
   certificate field ``commonName`` (deprecated by RFC 2818). In order
   to prevent any related usage issues, please make sure to add
   ``subjectAltName`` field to your own certificate in use. We will
   update help docs as soon as changes are made on the requests side.
