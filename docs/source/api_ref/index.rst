.. _api_ref:

API Reference
=============

**NOTE:** This API documentation assumes you are using 3.2.0 and higher versions
of ansible-tower-cli. If you are using a lower version than 3.2.0, there is no
guarantee API usages in this documentation would work as expected.

Introduction
------------

Like Tower UI, Tower CLI is a client talking to multiple REST services of Tower backend, but via Python script
or UNIX command line. Thus the usage of Tower CLI's APIs are pretty straight-forward: get a resource corresponding
to its counterpart in Tower backend, and call public methods of that resource, which in term requests specific REST
endpoint and fetch/render response JSON. Here is a simple example of creating a new organization using Tower CLI in
Python:

.. code-block:: python

   from tower_cli import get_resource
   from tower_cli.exceptions import Found
   from tower_cli.conf import settings

   with settings.runtime_values(username='user', password='pass'):
       try:
           res = get_resource('organization')
           new_org = res.create(name='foo', description='bar', fail_on_found=True)
       except Found:
           print('This organization already exists.')
   assert isinstance(new_org, dict)
   print(new_org['id'])

The above example shows the pattern for most Tower CLI API use cases, which is composed of 3 parts: runtime
configuration, fetch resource and invoke its public methods, and exception handling.

Tower CLI needs a set of configurations to function properly, all configuration settings are stored in singleton
object ``tower_cli.conf.settings``, which provides a public context manager ``runtime_values`` to temporary override
settings on file with temporary runtime values. see more about Tower CLI configurations in 'Configuration' section.

Most of the resources listed at Tower's endpoint `/api/v2/` have client-side proxy classes in Tower CLI. The two
main ways of getting resource proxies in Tower CLI are:

.. code-block:: python

   from tower_cli import get_resource

   res = get_resource('<resource name>')

and

.. code-block:: python

   import tower_cli.resources.<resource module name>.Resource as <alias>

   res = <alias>()

A typical resource in Tower CLI has 2 components: fields and public methods. Resource fields can be seen as wrappers
around actual resource fields exposed by Tower REST API. They are generally used by public methods to create and
modify resources and filter when searching for specific resources; Public methods are the actual wrappers around
querying Tower REST APIs, they can be used both for general CRUD operations against Tower resources, like delete
a user, and for specific tasks like launching an ad hoc command, monitoring a job run or constructing a workflow
graph from script.

In the table of contents below, all available Tower CLI resources are listed, the documentation for each of them all
follow the same structure: a 'Description' section which gives an introduction to the resource; a 'Fields Table'
section which lists all available fields of that resource; and a 'API Specification' section, which expands the usage
detail of every available public method.

Note most public methods have a keyword argument ``**kwargs``. This argument basically contains and only contains
resource fields, unless specified.

Any usage errors or connection exceptions are thrown as subclasses of ``tower_cli.exceptions.TowerCLIError``, see
'Exceptions' section below for details.

.. toctree::
   :maxdepth: 1
   :caption: Environment Setup

   conf.rst
   exceptions.rst

API Reference Table of Contents
===============================

.. toctree::
   :maxdepth: 1
   :caption: Resource List

   resources/ad_hoc.rst
   resources/credential_type.rst
   resources/credential.rst
   resources/group.rst
   resources/host.rst
   resources/instance_group.rst
   resources/instance.rst
   resources/inventory_script.rst
   resources/inventory_source.rst
   resources/inventory_update.rst
   resources/inventory.rst
   resources/job_template.rst
   resources/job.rst
   resources/label.rst
   resources/node.rst
   resources/notification_template.rst
   resources/organization.rst
   resources/project.rst
   resources/project_update.rst
   resources/role.rst
   resources/schedule.rst
   resources/setting.rst
   resources/team.rst
   resources/user.rst
   resources/workflow_job.rst
   resources/workflow.rst
