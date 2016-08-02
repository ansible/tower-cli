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
import six

from requests.exceptions import RequestException

from tower_cli import __version__
from tower_cli.api import client
from tower_cli.utils.decorators import command
from tower_cli.utils.exceptions import TowerCLIError


@command
def version():
    """Display version information."""

    # Print out the current version of Tower CLI.
    click.echo('Tower CLI %s' % __version__)

    # Attempt to connect to the Ansible Tower server.
    # If we succeed, print a version; if not, generate a failure.
    try:
        r = client.get('/config/')
        click.echo('Ansible Tower %s' % r.json()['version'])
    except RequestException as ex:
        raise TowerCLIError('Could not connect to Ansible Tower.\n%s' %
                            six.text_type(ex))
