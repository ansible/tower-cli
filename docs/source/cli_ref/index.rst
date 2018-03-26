.. _cli_ref:

CLI Reference
=============

CLI invocation generally follows this format:

.. code:: bash

    $ tower-cli {resource} {action} ...

The "resource" is a type of object within Tower (a noun), such as
``user``, ``organization``, ``job_template``, etc.; resource names are
always singular in Tower CLI (so it is ``tower-cli user``, never
``tower-cli users``).

The "action" is the thing you want to do (a verb). Most Tower CLI
resources have the following actions--\ ``get``, ``list``, ``create``,
``modify``, and ``delete``--and have options corresponding to fields on
the object in Tower.

Some examples:

.. code:: bash

    # List all users.
    $ tower-cli user list

    # List all non-superusers
    $ tower-cli user list --is-superuser=false

    # Get the user with the ID of 42.
    $ tower-cli user get 42

    # Get the user with the given username.
    $ tower-cli user get --username=guido

    # Create a new user.
    $ tower-cli user create --username=guido --first-name=Guido \
                            --last-name="Van Rossum" --email=guido@python.org \
                            --password=password1234

    # Modify an existing user.
    # This would modify the first name of the user with the ID of "42" to "Guido".
    $ tower-cli user modify 42 --first-name=Guido

    # Modify an existing user, lookup by username.
    # This would use "username" as the lookup, and modify the first name.
    # Which fields are used as lookups vary by resource, but are generally
    # the resource's name.
    $ tower-cli user modify --username=guido --first-name=Guido

    # Delete a user.
    $ tower-cli user delete 42

    # List all jobs
    $ tower-cli job list
    
    # List specific page of job list
    $ tower-cli job list --page=1

    # Launch a job.
    $ tower-cli job launch --job-template=144

    # Monitor a job.
    $ tower-cli job monitor 95
    
    # Filter job list for currently running jobs
    $ tower-cli job list --status=running

    # Export all objects
    $ tower-cli receive --all

    # Export all credentials
    $ tower-cli receive --credential all

    # Export a credential named "My Credential"
    $ tower-cli receive --credential "My Credential"

    # Import from a JSON file named assets.json
    $ tower-cli send assets.json

    # Import anything except an organization defined in a JSON file named assets.json
    $ tower-cli send --prevent organization assets.json

    # Copy all assets from one instance to another
    $ tower-cli receive --tower-host tower1.example.com --all | tower-cli send --tower-host tower2.example.com



When in doubt, help is available!

.. code:: bash

    $ tower-cli --help # help
    $ tower-cli user --help # resource specific help
    $ tower-cli user create --help # command specific help

In specific, ``tower-cli --help`` lists all available resources in the current version of Tower CLI:

.. code:: bash

    $ tower-cli --help
    Usage: tower-cli [OPTIONS] COMMAND [ARGS]...

    Options:
      --version  Display tower-cli version.
      --help     Show this message and exit.

    Commands:
      ad_hoc                 Launch commands based on playbook given at...
      config                 Read or write tower-cli configuration.
      credential             Manage credentials within Ansible Tower.
      credential_type        Manage credential types within Ansible Tower.
      empty                  Empties assets from Tower.
      group                  Manage groups belonging to an inventory.
      host                   Manage hosts belonging to a group within an...
      instance               Check instances within Ansible Tower.
      instance_group         Check instance groups within Ansible Tower.
      inventory              Manage inventory within Ansible Tower.
      inventory_script       Manage inventory scripts within Ansible...
      inventory_source       Manage inventory sources within Ansible...
      job                    Launch or monitor jobs.
      job_template           Manage job templates.
      label                  Manage labels within Ansible Tower.
      node                   Manage nodes inside of a workflow job...
      notification_template  Manage notification templates within Ansible...
      organization           Manage organizations within Ansible Tower.
      project                Manage projects within Ansible Tower.
      receive                Export assets from Tower.
      role                   Add and remove users/teams from roles.
      schedule               Manage schedules within Ansible Tower.
      send                   Import assets into Tower.
      setting                Manage settings within Ansible Tower.
      team                   Manage teams within Ansible Tower.
      user                   Manage users within Ansible Tower.
      version                Display version information.
      workflow               Manage workflow job templates.
      workflow_job           Launch or monitor workflow jobs.

and ``tower-cli {resource} --help`` lists all available actions:

.. code:: bash

    $ tower-cli user --help
    Usage: tower-cli user [OPTIONS] COMMAND [ARGS]...

      Manage users within Ansible Tower.

    Options:
      --help  Show this message and exit.

    Commands:
      copy    Copy a user.
      create  Create a user.
      delete  Remove the given user.
      get     Return one and exactly one user.
      list    Return a list of users.
      modify  Modify an already existing user.

and ``tower-cli {resource} {action} --help`` shows details of the usage of this action:

.. code:: bash

    $ tower-cli user create --help
    Usage: tower-cli user create [OPTIONS]

      Create a user.

      Fields in the resource's --identity tuple are used for a lookup; if a
      match is found, then no-op (unless --force-on-exists is set) but do not
      fail (unless --fail-on-found is set).

    Field Options:
      --username TEXT              [REQUIRED] The username field.
      --password TEXT              The password field.
      --email TEXT                 [REQUIRED] The email field.
      --first-name TEXT            The first_name field.
      --last-name TEXT             The last_name field.
      --is-superuser BOOLEAN       The is_superuser field.
      --is-system-auditor BOOLEAN  The is_system_auditor field.

    Local Options:
      --fail-on-found    If used, return an error if a matching record already
                         exists.  [default: False]
      --force-on-exists  If used, if a match is found on unique fields, other
                         fields will be updated to the provided values. If False,
                         a match causes the request to be a no-op.  [default:
                         False]

    Global Options:
      --certificate TEXT              Path to a custom certificate file that will
                                      be used throughout the command. Overwritten
                                      by --insecure flag if set.
      --insecure                      Turn off insecure connection warnings. Set
                                      config verify_ssl to make this permanent.
      --description-on                Show description in human-formatted output.
      -v, --verbose                   Show information about requests being made.
      -f, --format [human|json|yaml|id]
                                      Output format. The "human" format is
                                      intended for humans reading output on the
                                      CLI; the "json" and "yaml" formats provide
                                      more data, and "id" echos the object id
                                      only.
      -p, --tower-password TEXT       Password to use to authenticate to Ansible
                                      Tower. This will take precedence over a
                                      password provided to `tower config`, if any.
      -u, --tower-username TEXT       Username to use to authenticate to Ansible
                                      Tower. This will take precedence over a
                                      username provided to `tower config`, if any.
      -h, --tower-host TEXT           The location of the Ansible Tower host.
                                      HTTPS is assumed as the protocol unless
                                      "http://" is explicitly provided. This will
                                      take precedence over a host provided to
                                      `tower config`, if any.
      --use-token                     Turn on Tower's token-based authentication.
                                      No longer supported in Tower 3.3 and above

    Other Options:
      --help  Show this message and exit.

There are generally 3 categories of options for each action to take: field options, local options and global
options. Field options can be seen as wrappers around actual resource fields exposed by Tower REST API. They
are generally used to create and modify resources and filter when searching for specific resources; local options
are action-specific options, they provide fine-grained modification of the behavior of a resource action. for
example, ``--fail-on-found`` option of a ``create`` action will fail the command if a matching record already
exists in Tower backend; global options are used to set runtime configuration settings, functioning the same way
as context manager ``tower_cli.conf.Settings.runtime_values`` in :ref:`api-ref-conf`.

.. toctree::
   :maxdepth: 0
   :caption: Usage Guides

   usage/CONFIG_CMD_OPTIONS.rst
   usage/VERSIONING.rst
   usage/NOTIFICATION_TEMPLATE_MANAGEMENT.rst
   usage/ROLE_MANAGEMENT.rst
   usage/SURVEYS.rst
   usage/WORKFLOWS.rst

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/README.rst

