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

import click

from tower_cli import models, resources
from tower_cli.utils import types, debug
from tower_cli.api import client


PROMPT = '[Type "ASK" to make this field promptable]'


class Resource(models.Resource):
    cli_help = 'Manage credentials within Ansible Tower.'
    endpoint = '/credentials/'
    identity = ('organization', 'user', 'team', 'kind', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)

    # Who owns this credential?
    user = models.Field(
        display=False,
        type=types.Related('user'),
        required=False,
    )
    team = models.Field(
        display=False,
        type=types.Related('team'),
        required=False,
    )
    organization = models.Field(
        display=False,
        type=types.Related('organization'),
        required=False,
    )

    # What type of credential is this (machine, SCM, etc.)?
    kind = models.Field(
        display=True,
        help_text='The type of credential being added. '
                  'Valid options are: ssh, net, scm, aws, rax, vmware,'
                  ' foreman, cloudforms, gce, azure, azure_rm, openstack.',
        type=click.Choice(['ssh', 'net', 'scm', 'aws', 'rax', 'vmware',
                           'foreman', 'cloudforms', 'gce', 'azure',
                           'azure_rm', 'openstack']),
    )

    # need host in order to use VMware
    host = models.Field(
        help_text='The hostname or IP address to use.',
        required=False, display=False
    )
    # need project to use openstack
    project = models.Field(
        help_text='The identifier for the project.',
        required=False, display=False
    )

    # SSH and SCM fields.
    username = models.Field(
        help_text='The username. For AWS credentials, the access key.',
        required=False,
    )
    password = models.Field(
        help_text='%sThe password. For AWS credentials, the secret key. '
                  'For Rackspace credentials, the API key.' % PROMPT,
        password=True,
        required=False,
    )
    ssh_key_data = models.Field(
        'ssh_key_data',
        display=False,
        help_text="The full path to the SSH private key to store. "
                  "(Don't worry; it's encrypted.)",
        required=False,
        type=models.File('r'),
    )
    ssh_key_unlock = models.Field(help_text='%sssh_key_unlock' % PROMPT,
                                  password=True, required=False)

    # Extra fields in 3.0
    authorize = models.Field(
        help_text='Whether to use the authorize mechanism when type is "net".',
        required=False, display=False,
        type=click.BOOL,
    )
    authorize_password = models.Field(
        help_text='Password used by the authorize mechanism when type is '
                  '"net".',
        password=True, required=False, display=False,
    )
    client = models.Field(
        help_text='Client Id or Application Id for the credential when type '
                  'is "azure_rm".',
        required=False, display=False,
    )
    secret = models.Field(
        help_text='Secret Token for this credential when type is "azure_rm".',
        required=False, display=False
    )
    subscription = models.Field(
        help_text='Subscription identifier for this credential when type is '
                  '"azure_rm".',
        required=False, display=False,
    )
    tenant = models.Field(
        help_text='Tenant identifier for this credential when type is '
                  '"azure_rm"',
        required=False, display=False,
    )
    domain = models.Field(
        help_text='Domain name for this credential when type is "openstack".',
        required=False, display=False,
    )

    # Method with which to esclate
    become_method = models.Field(
        display=False,
        help_text='Privledge escalation method. ',
        type=types.MappedChoice([
            ('', 'None'),
            ('sudo', 'sudo'),
            ('su', 'su'),
            ('pbrun', 'pbrun'),
            ('pfexec', 'pfexec'),
        ]),
        required=False,
    )

    # SSH specific fields.
    become_username = models.Field(required=False, display=False)
    become_password = models.Field(password=True, required=False,
                                   help_text='%sThe become_password field' %
                                   PROMPT)
    vault_password = models.Field(password=True, required=False,
                                  help_text='%sThe vault_password field' %
                                  PROMPT)

    @resources.command
    def create(self, **kwargs):
        """Create a credential.
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
