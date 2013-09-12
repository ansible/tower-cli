awx-cli
=======

This is a command line tool for AnsibleWorks AWX.  

About AWX
=========

AWX is a GUI and REST interface for Ansible that supercharges it by adding RBAC,
centralized logging, autoscaling/provisioning callbacks, graphical inventory
editing, and more.

See http://ansibleworks.com/ansibleworks-awx for more details.  

AWX is free to use for up to 10 nodes, and you can purchase a license for more at http://store.ansibleworks.com.

Capabilities
============

You can use this command line tool to send commands to the AWX API.

For instance, you might use this tool with Jenkins, cron, or in-house software to trigger remote execution of Ansible playbook runs.

This tool is designed to be pluggable and will be expanded over time.

Installation
============

Packages will be coming soon.

From a git checkout:
  
    make install
    awx-cli --help

Usage
=====

All commands take a username, password, and server parameter.  These values
can also be set in a ~/.awx_cli.cfg file as follows, which is recommended for
batch usage.  If the ~/.awx_cli.cfg is not found, the config file will also
be looked for in /etc/awx/awx_cli.cfg.

    [general]
    username=admin
    password=password
    server=http://127.0.0.1

CLI invocation looks like this:

    # list subcommands
    awx-cli --help
    
    # run a command (no config file)
    awx-cli version --username admin --password password --server http://172.16.177.238
  
    # run a command (config file)
    awx-cli version

Here is an example of launching a job template to run an ansible playbook. The system will prompt for any parameters
set to 'ASK' in AWX, so be sure all of this information is filled in if you are using this
from a system like Jenkins or cron.  All we need to specify is the template ID.

    awx-cli joblaunch --template 5

License
=======

While AWX is commercial software, awx-cli is an open source project and we want
to encourage contributions to it.  Specfically, this CLI project is licensed under the
Apache2 license.  You may do what you like with it, but we definitely welcome
pull requests!

Michael DeHaan
(C) 2013, AnsibleWorks, Inc.


