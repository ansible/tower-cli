## Example Commands

Examples here are intended to give concrete examples of how the CLI
can be used in an automated way. It can also help with testing or the defining of
feature requests.

Expect the setup script to take up to 2 minutes to run. Most of this is due to the project source control downloading the examples
from github to the tower server.

### Setup

You should have a testing version of tower running and configured in the CLI
in order to run any scripts or commands here. With your specific data, that
can done by the following commands:

```bash
$ tower-cli config host tower.example.com
$ tower-cli config username leeroyjenkins
$ tower-cli config password myPassw0rd
```

### Create Fake Data

You may want to reference the
[fake data creator](/docs/examples/fake_data_creator.sh) for
examples on how to do things.

If you want to run the script, which auto-populates your Tower server
with a small set of fake data, run the following:

```bash
# Populate the server with fake data and run test jobs
$ cd docs/examples/
$ source fake_data_creator.sh
```

### Cleaning Up

The teardown script removes all of the objects that the CLI can easily
remove. This is not a perfect cleanup, but it performs well enough to get the system
ready to run the fake data creator script again.

```bash
# Delete the data that was created (with some exceptions)
$ source fake_data_teardown.sh
```

### Warnings

It is strongly suggested that you only run these scripts on testing versions
of an Ansible Tower host.

### Module Use Example

This bash script example borrows fake data elements from the [tower populator script](https://github.com/jsmartin/tower_populator). The tower_populator script provides an example of how to use the tower-cli python modules.
 