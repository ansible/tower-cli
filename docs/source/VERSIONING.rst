Versioning of tower-cli
=======================

Tower-CLI is a command-line interface and python library to interact with
Ansible Tower and AWX. Only versions of tower-cli can successfully
interact with only a certain subset of versions of Ansible Tower or AWX,
and this document is meant to outline the policy.

API Versions
------------

Ansible Tower and AWX communicate with clients through a particular API
version, so that each version forms a stable API for Ansible Tower.
Each version of tower-cli also has a corresponding API version.

Supported Versions with Ansible Tower
-------------------------------------

The following table summarizes the policy of supported versions.

=============  =============  ====================
   tower-cli    API version    Tower version 
=============  =============  ====================
3.1.x             v1           3.2.x and earlier
current           v2           3.2.x and later
=============  =============  ====================

This means that the release series 3.1.x is still open for fixes in
order to support communication with the v1 API and all Tower versions
that support that. Many elements of functionality are removed in the
transition to v2, so they are no longer carried with the current tower-cli
version.

Policy with AWX Versions
------------------------

Compatibility between tower-cli and the AWX project is only considered
for the most recent development version of tower-cli and most recent
version of AWX.

API Version Upgrade Guide
-------------------------

If you upgrade tower-cli across an API version change, existing scripts
will be broken.

This section highlights the most major
backward-incompatible changes that need to be taken into account in order
to migrate your scripts.

API v1->v2
~~~~~~~~~~

In API v2, credentials have a new related model "credential_type".
This enables custom credential types, and that old types now need to
reference the build-in credential types instead of the old
flat-text `kind` field.

Additionally, to allow fully arbitrary credential types, the fields used
by the credential in creating the necessary runtime environment are now
nested inside of a dictionary called `inputs`.

old:

.. code:: bash

    $ tower-cli credential create --name="AWS creds" --team=Ops --kind=aws --username=your_username --password=password

new:

.. code:: bash

    $ tower-cli credential create --name="AWS creds" --team=Ops --credential-type="Amazon Web Services" --inputs='{"username": "your_username", "password": "password"}'

When attaching credentials to job templates, the related link structure has
changed.

API v1 options:
 - `--machine-credential`
 - `--cloud-credential`
 - `--network-credential`

API v2 options:
 - `--credential`
 - `--vault-credential`
 - Related many-to-many `extra_credentials`

In order to add "extra" credentials (what used to be cloud credential),
use the association method, `tower-cli job_template associate_credential ...`.

In API v2, only "manual" groups can be created directly.
The parameters that used to be provided to a group to sync to a cloud source
now must be directly given to its inventory source.

old:

.. code:: bash

    $ tower-cli group create --name=EC2 --credential="AWS creds" --source=ec2 --description="EC2 hosts" --inventory=Production

new:

.. code:: bash

    $ tower-cli inventory_source create --name=EC2 --credential="AWS creds" --source=ec2 --description="EC2 hosts" --inventory=Production

To run an inventory update, use the `tower-cli inventory_source update` command.

Version-specific Secondary Install
----------------------------------

In order to use different versions of tower-cli simultaneously in order
to interact with different servers hosting different API versions, you can
use this tool packaged in the source code.

For example:

.. code:: bash

    $ make install_v1

This will install a new CLI entry point, `tower-cli-v1`, which will behave
the same as `tower-cli`. However, this installation will persist even
after upgrading the main program. This also provides the python package
`tower_cli_v1`.

Important note: the configuration file is also separate from the secondary
install, so you must re-enter your URL and credentials.

If you want to be sure that you *re-install* `tower-cli-v1`, you can do:

.. code:: bash

    $ make v1-refresh

The v1 install is only possible with the `v1` branch in the source tree.
The `master` branch currently tracks API v2, and the prior instructions
will work for a v2 secondary install, replacing v1 with v2.
