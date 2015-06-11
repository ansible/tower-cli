[![Build Status](https://img.shields.io/travis/ansible/tower-cli.svg)](https://travis-ci.org/ansible/tower-cli)
[![Coverage Status](https://img.shields.io/coveralls/ansible/tower-cli.svg)](https://coveralls.io/r/ansible/tower-cli)
[![Version](https://img.shields.io/pypi/v/ansible-tower-cli.svg)](https://pypi.python.org/pypi/ansible-tower-cli/)
[![Downloads](https://img.shields.io/pypi/dm/ansible-tower-cli.svg)](https://pypi.python.org/pypi/ansible-tower-cli/)
[![License](https://img.shields.io/pypi/l/ansible-tower-cli.svg)](https://pypi.python.org/pypi/ansible-tower-cli/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/ansible-tower-cli.svg)](https://pypi.python.org/pypi/ansible-tower-cli/)


## Welcome to tower-cli

**tower-cli** is a command line tool for Ansible Tower. It allows Tower
commands to be easily run from the Unix command-line.  It can also be used
as a client library for other python apps, or as a reference for others 
developing API interactions with Tower's REST API.


### About Tower

[Ansible Tower][1] is a GUI and REST interface for Ansible that supercharges
it by adding RBAC, centralized logging, autoscaling/provisioning callbacks,
graphical inventory editing, and more.

Tower is free to use for up to 30 days or 10 nodes. Beyond this, [a license
is required][2].

  [1]: http://ansible.com/tower
  [2]: http://ansible.com/ansible-pricing


### Capabilities

This command line tool sends commands to the Tower API. It is capable of
retrieving, creating, modifying, and deleting most objects within Tower.

A few potential uses include:

  * Launching playbook runs (for instance, from Jenkins, TeamCity, Bamboo, etc)
  * Checking on job statuses
  * Rapidly creating objects like organizations, users, teams, and more

### Installation

Tower CLI is available as a package on [PyPI][3].

  [3]: https://pypi.python.org/pypi/ansible-tower-cli

The preferred way to install is through pip:

```bash
$ pip install ansible-tower-cli
```

The main branch of this project may also be consumed directly from source.

### Configuration

Configuration can be set in several places.  The `tower-cli` itself can edit it's own configuration, or
users can directly edit the configuration file.

#### Set configuration with tower-cli config.

The preferred way to set configuration is with the `tower-cli config` command.
The syntax is:

```bash
$ tower-cli config key value
```

By issuing `tower-cli config` with no arguments, you can see a full list
of configuration options and where they are set.

You will generally need to set at least three configuration options:
`host`, `username`, and `password`; these correspond to the location of
your Ansible Tower instance and your credentials to authenticate to Tower.

```bash
$ tower-cli config host tower.example.com
$ tower-cli config username leeroyjenkins
$ tower-cli config password myPassw0rd
```

#### Write to the config files directly.

The configuration file can also be edited directly.  A configuration file is a simple file with keys and values, separated by `:` or `=`:

```yaml
host: tower.example.com
username: admin
password: p4ssw0rd
```

The locations searched for the configuration file are given below.

#### File Locations

The order of precedence for configuration file locations is as follows, from least to
greatest:

  * internal defaults
  * `/etc/awx/tower_cli.cfg` (written using `tower-cli config --global`)
  * `~/.tower_cli.cfg` (written using `tower-cli config`)
  * run-time paramaters


### Usage

CLI invocation generally follows this format:

```bash
$ tower-cli {resource} {action} ...
```

The "resource" is a type of object within Tower (a noun), such as `user`,
`organization`, `job_template`, etc.; resource names are always singular in
Tower CLI (so: it's `tower-cli user`, never `tower-cli users`).

The "action" is the thing you want to do (a verb). Most Tower CLI resources
have the following actions: `get`, `list`, `create`, `modify`, and `delete`,
and have options corresponding to fields on the object in Tower.

Some examples:

```bash
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
                        --last-name="Van Rossum" --email=guido@python.org

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

# Launch a job.
$ tower-cli job launch --job-template=144

# Monitor a job.
$ tower-cli job monitor 95
```

When in doubt, help is available!

```bash
$ tower-cli # help
$ tower-cli user --help # resource specific help
$ tower-cli user create --help # command specific help
```

### License

While Tower is commercially licensed software, _tower-cli_ is an open source project,
and we encorage contributions.  Specfically, this CLI project is licensed
under the Apache 2.0 license.  Pull requests and tickets filed in GitHub are welcome.

(C) 2015, Michael DeHaan, and others, Ansible, Inc.
