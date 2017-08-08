# Copyright 2015, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tower_cli import models, resources
from tower_cli.utils import debug
from tower_cli.api import client
from tower_cli.cli import types


class Resource(models.Resource):
    """A resource for credentials."""
    cli_help = 'Manage credentials within Ansible Tower.'
    endpoint = '/credentials/'
    identity = ('organization', 'user', 'team', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)

    # Who owns this credential?
    user = models.Field(display=False, type=types.Related('user'), required=False)
    team = models.Field(display=False, type=types.Related('team'), required=False)
    organization = models.Field(display=False, type=types.Related('organization'), required=False)

    credential_type = models.Field(type=types.Related('credential_type'))
    inputs = models.Field(type=types.StructuredInput(), required=False, display=False)

    @resources.command
    def create(self, **kwargs):
        """Create a credential.

        Fields in the resource's `identity` tuple are used for a lookup;
        if a match is found, then no-op (unless `force_on_exists` is set) but
        do not fail (unless `fail_on_found` is set).

        =====API DOCS=====
        Create a credential.

        :param fail_on_found: Flag that if set, the operation fails if an object matching the unique criteria
                              already exists.
        :type fail_on_found: bool
        :param force_on_exists: Flag that if set, then if a match is found on unique fields, other fields will
                                be updated to the provided values.; If unset, a match causes the request to be
                                a no-op.
        :type force_on_exists: bool
        :param `**kwargs`: Keyword arguements which, all together, will be used as POST body to create the
                           resource object.
        :returns: A dictionary combining the JSON output of the created resource, as well as two extra fields:
                  "changed", a flag indicating if the resource is created successfully; "id", an integer which
                  is the primary key of the created object.
        :rtype: dict


        =====API DOCS=====
        """
        if (kwargs.get('user', False) or kwargs.get('team', False) or
                kwargs.get('organization', False)):
            debug.log('Checking Project API Details.', header='details')
            r = client.options('/credentials/')
            if 'organization' in r.json()['actions']['POST']:
                for i in range(len(self.fields)):
                    if self.fields[i].name in ('user', 'team'):
                        self.fields[i].no_lookup = True
        return super(Resource, self).create(**kwargs)
