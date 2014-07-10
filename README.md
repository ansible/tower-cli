## Welcome to tower-cli

**tower-cli** is a command line tool for Ansible Tower. It allows Tower
commands to be easily run from the Unix command-line.


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

  * System-based job launches (for instance, from Jenkins, cron, etc.)
  * Use in callbacks from Ansible playbooks
  * Custom syncronization of inventory


### Installation

Tower CLI is available as a package on [PyPI][3].

  [3]: https://pypi.python.org/pypi/ansible-tower-cli

The preferred way to install is through pip:

```bash
$ pip install ansible-tower-cli
```


### Configuration

Configuration can be set in several places, and either through a command
sent to `tower-cli` or through direct editing of the configuration file.

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


#### Write to the config files directly.

A configuration file is a simple file with keys and values, separated by
`:` or `=`:

```yaml
host: tower.example.com
username: admin
password: p4ssw0rd
```


#### Order of Precedence

The order of precedence for configuration is as follows, from least to
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

### License

While Tower is commercial software, _tower-cli_ is an open source project,
and we encorage contributions.  Specfically, this CLI project is licensed
under the Apache license.

Michael DeHaan
(C) 2014, Ansible, Inc.
