|Build Status| |Coverage Status| |Version| |Downloads| |License|
|Supported Python Versions|

Welcome to tower-cli
====================

**tower-cli** is a legacy command line tool for Ansible Tower.

It is also what the Ansible `tower_*` modules use under the hood. Such as:

https://docs.ansible.com/ansible/latest/modules/tower_organization_module.html

These modules are now vendored as part of the AWX collection at:

https://galaxy.ansible.com/awx/awx

Supporting correct operation of the modules is the maintenance aim of this
package.

Anyone developing new tooling around AWX or Ansible Tower via a Unix command
line is suggested to use the new CLI.

https://github.com/ansible/awx/tree/devel/awxkit/awxkit/cli/docs

 .. |Build Status| image:: https://img.shields.io/travis/com/ansible/tower-cli.svg
    :target: https://travis-ci.com/ansible/tower-cli
 .. |Coverage Status| image:: https://img.shields.io/coveralls/ansible/tower-cli.svg
    :target: https://coveralls.io/r/ansible/tower-cli
 .. |Version| image:: https://img.shields.io/pypi/v/ansible-tower-cli.svg
    :target: https://pypi.python.org/pypi/ansible-tower-cli/
 .. |Downloads| image:: https://img.shields.io/pypi/dm/ansible-tower-cli.svg
    :target: https://pypi.python.org/pypi/ansible-tower-cli/
 .. |License| image:: https://img.shields.io/pypi/l/ansible-tower-cli.svg
    :target: https://pypi.python.org/pypi/ansible-tower-cli/
 .. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/ansible-tower-cli.svg
    :target: https://pypi.python.org/pypi/ansible-tower-cli/
