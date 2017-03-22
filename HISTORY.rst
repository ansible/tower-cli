Release History
===============

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
