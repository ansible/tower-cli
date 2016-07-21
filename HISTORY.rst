Release History
===============

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
