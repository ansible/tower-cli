Release History
===============

3.3.0 (2018-04-25)
------------------

 - Added send and receive commands to export and import resources
 - Added support for import and export role memberships as well
 - Added login command for token-based auth (AWX feature)
 - Added options for workflow nodes and schedules (AWX feature)
 - Added support for server-side copying (AWX feature)
 - Added resource for activity stream
 - Added abstract resource for job events
 - Bug fixes for label creation, workflow monitor, global config, role list

3.2.1 (2017-12-19)
------------------

- Added support for using settings from environment vars in normal CLI use
- Made many-to-many relations easier to manage with a new field type
- Installed new CLI entry point, awx-cli
- Allowed setup and testing to proceed without root privileges
- Added project and inventory update resources to enable more functionality
- Fixed bug when copying resources that use the variables field type
- Fixed bug that caused debug messages to hang with long line lengths
- Fixed bug with side-by-side install of v1 and v2
- Fixed bug where --all-pages was ignored for roles
- Allowed use of --format=id with multiple results
- Added cleaner handling of Unicode

3.2.0 (2017-10-04)
------------------

*General:*

- Officially support using tower_cli as a python library.
- Major documentation updates. From 3.2.0 docs are hosted on http://tower-cli.readthedocs.io.
- Added project_update and inventory_update resources to allow canceling and deleting.

*Updates from Tower 3.2:*

- Migrated to API V2. All API calls will start with `/api/v2` instead of `/api/v1`.
- Made inventory_source an external resource and remove the old relationship to its associated group. Remove launching inventory updates from group resource.
- Added credential_type resource and significantly modified credential resource to reveal user-defined credentials feature of Tower 3.2.
- Added job template extra credential (dis)association to reveal extra_credential field of 3.2 job templates.
- Removed all source-specific inventory source fields and replaced them with a `credential` field.
- Updated inventory resource fields to reveal smart inventory and insights integration features of Tower 3.2.
- Added `list_fact` and `insights` commands to host resource to reveal smart inventory and insights integration features of Tower 3.2.
- Added `instance` and `instance_group` resources to reveal instance/instance group feature of Tower 3.2.
- Enabled (dis)associating instance groups to(from) organization, job_template and inventory resources to reveal instance/instance group feature of Tower 3.2.
- Added support for Tower 3.2 SCM inventory sources.
- Updated job_template resource fields to reveal changes in Tower 3.2, including `--diff` mode feature.
- Updated job resource launch command to reveal changes in Tower 3.2, including `--diff` mode feature.
- Updated ad_hoc resource fields to reveal changes in Tower 3.2, including `--diff` mode feature. Specifically, changed name of `--become` of `launch` command into `--become-enabled`.

*Deprecated features:*

- Removed permission resource.
- Disabled launching a job using the jobs endpoint.
- Removed scan jobs in favor of new job fact cache.
- Removed Rackspace options.
- Remove outdated association function for project’s organization.

*Reflected from 3.1.8:*

- Include method of installing with alias tower-cli-v2
- Fix bug of incomplete role membership lookup, preventing granting of roles.
- Combine click parameters from multiple base classes in metaclass.
- Fix unicode bug in human display format.
- Add new page_size parameter to list view.
- Add scm_update_cache_timeout field to project resource.
- Begin process to deprecate python 2.6.

3.1.7 (2017-08-07)
------------------

- Follow up 3.1.6 by duplicating exceptions.py to support `import tower_cli.utils.exceptions` syntax.

3.1.6 (2017-07-18)
------------------

- Fix a usage compatibility issue for Ansible Tower modules.

3.1.5 (2017-07-12)
------------------

- Major code base file structure refactor. Now all click-related logics are moved to `tower_cli/cli/` directory,
  and `exceptions.py` as well as `compat.py` are moved out of utils directory into base directory.
- Categorize help text options for resource action commands (like `update`) to increase readability.
- Behavior change of workflow schema command. Now schema will both create new nodes and delete existing nodes when
  needed to make the resulting workflow topology exactly the same as described in schema file.
- Add command `job_template callback` to enable conducting provisioning callback via Tower CLI.
- Add new format option to just echo id.
- Expand some resource fields, including hipchat rooms for notification template and allow_simultaneous for job
  templates.
- Lookup related inventory sources with "starts with" logic if its name is not fully qualified.
- Fixed a python 3.5 compatibility issue that causes job monitor traceback.
- Minor typo and help text updates.

3.1.4 (2017-06-07)
------------------

- Support resource copy subcommand.
- Support auth-token-based authentication for Tower CLI requests.
- Support managing workflow roles, labels and notifications via Tower CLI.
- Several fixes on RPM spec file.
- Name change from 'foreman' to 'satellite6' in credential kind choices.
- Fixed a bug where creating job templates with --extra-vars did not work after
  3.1.0 upgrade.
- Fixed traceback when launching job with --use-job-endpoint.
- Enhanced json library usage to prevent traceback when using earlier python 2.6
  versions.
- Prevent throwing unnecessary warning when reading from global configuration file.

3.1.3 (2017-03-22)
------------------

- Fixed a bug where extra_vars were dropped in some commands.

3.1.2 (2017-03-21)
------------------

- Fixed a bug where global flags are not added to some commands.

3.1.1 (2017-03-13)
------------------

- Fixed a bug which blocks named resources from using runtime configure settings.
- Fixed a bug in 3.1.0 which sometimes causes traceback when `pk` value is given.

3.1.0 (2017-03-09)
------------------

- Improved job monitoring functionality to enable standard out streaming, which
  displays real-time job output on command line.
- Added workflow, workflow_job and node endpoints to manipulate workflow graph
  and manage workflow job resources. Reflecting workflows feature of Tower 3.1.
- Added settings command to manage Tower settings via Tower CLI. Reflecting
  Configure Tower in Tower (CTiT) feature of Tower 3.1.
- Included timeout option to certain unified job template resources. Reflecting
  job timeout feature of Tower 3.1.
- Added unicode support to extra_vars and variable types.
- Several minor bug fixes to improve user experience.

3.0.3 (2017-02-07)
------------------

- Expose custom inventory script resource to the user
- Include tests and docs in the release tarball
- Added job template skip_tags prompting support
- Added job template callback support

3.0.2 (2016-12-08)
------------------

- Enable configuring tower-cli via environment variables

3.0.1 (2016-09-22)
------------------

- Added custom SSL certificate support

3.0.0 (2016-08-05)
------------------

- Added text indicator for resource change
- Allow hosts, inventory, and groups to use variables from the command line
  and denote a file by starting with "@"
- Added resource role for tower3.0 and permission for previous tower versions
- Added notification templates
- Added labels
- Added description display option
- Added deprecation warnings
- Help text upgrades
- Give indication of "changed" apart from color
- New credential fields to support openstack-v2, networking and azure
- New options for inventory source/group. Add implicit resource inventory
  script.
- credential updates (no longer require user/team)
- Added support for system auditors
- projects (do not post to organizations/N/projects)
- prompt-for JT fields + job launch options (allow blank inventory too)
- Update the POST protocol for associate and disassociate actions
- New job launch option for backwards compatibility
- New tower-cli option to display tower-cli version
- Enhanced debug log format (support multi-line debug log)

2.3.2 (2016-07-21)
------------------

- Add RPM specfile and Makefile
- Tower compatibility fixes
- Allow scan JTs as an option for "job_type"
- Add ability to create group as subgroup of another group
- Add YAML output format against JSON and humanized output formats
- Add SSL corner case error handling and suggestion
- Allow resource disassociation with "null"

2.3.1 (2015-12-10)
------------------

- Fixed bug affecting force-on-exists and fail_on_found options
- Changed extra_vars behavior to be more compliant by re-parsing vars,
  even when only one source exists
- Fixed group modify bug, avoid sending unwanted fields in modify requests

2.3.0 (2015-10-20)
------------------

-  Fixed an issue where the settings file could be world readable
-  Added the ability to associate a project with an organization
-  Added setting "verify\_ssl" to disallow insecure connections
-  Added support for additional cloud credentials
-  Exposed additional options for a cloud inventory source
-  Combined " launch-time extra\_vars" with " job\_template extra\_vars"
   for older Tower versions
-  Changed the extra\_vars parameters to align with Ansible parameter
   handling
-  Added the ability to run ad hoc commands
-  Included more detail when displaying job information
-  Added an example bash script to demonstrate tower-cli usage

2.1.1 (2015-01-27)
------------------

-  Added tests for Python versions 2.6 through 3.4
-  Added shields for github README
-  Added job\_tags on job launches
-  Added option for project local path

2.1.0 (2015-01-21)
------------------

-  Added the ability to customize the set of fields used as options for
   a resource
-  Expanded monitoring capability to include projects and inventory
   sources
-  Added support for new job\_template job launch endpoint

2.0.2 (2014-10-02)
------------------

-  Added ability to set local scope for config file
-  Expanded credential resource to allow options for cloud credentials

2.0.1 (2014-07-18)
------------------

-  Updated README and error text

2.0.0 (2014-07-15)
------------------

-  Pluggable resource architecture built around click
