tower-cli
=======

This is a command line tool for Ansible Tower.  

About Tower
=========

Tower is a GUI and REST interface for Ansible that supercharges it by adding RBAC,
centralized logging, autoscaling/provisioning callbacks, graphical inventory
editing, and more.

See http://ansible.com/tower for more details.  

Tower is free to use for up to 10 nodes, and you can purchase a license for more at http://ansible.com/ansible-pricing.

Capabilities
============

You can use this command line tool to send commands to the Tower API.

For instance, you might use this tool with Jenkins, cron, or in-house software to trigger remote execution of Ansible playbook runs.

This tool is designed to be pluggable and will be expanded over time.

Installation
============

Packages will be coming soon.

From a git checkout:
  
    make install
    tower-cli --help

Usage
=====

All commands take a username, password, and server parameter.  These values
can also be set in a ~/.tower_cli.cfg file as follows, which is recommended for
batch usage.  If the ~/.tower_cli.cfg is not found, the config file will also
be looked for in /etc/awx/tower_cli.cfg.

    [general]
    username=admin
    password=password
    server=http://127.0.0.1

CLI invocation looks like this:

    # list subcommands
    tower-cli --help
    
    # run a command (no config file)
    tower-cli version --username admin --password password --server http://172.16.177.238
  
    # run a command (config file)
    tower-cli version

Here is an example of launching a job template to run an ansible playbook. The system will prompt for any parameters
set to 'ASK' in Tower, so be sure all of this information is filled in if you are using this
from a system like Jenkins or cron.  All we need to specify is the template ID.

    tower-cli joblaunch --template 5

License
=======

While Tower is commercial software, tower-cli is an open source project and we want
to encourage contributions to it.  Specfically, this CLI project is licensed under the
Apache2 license.  You may do what you like with it, but we definitely welcome
pull requests!

Michael DeHaan
(C) 2014, Ansible, Inc.


