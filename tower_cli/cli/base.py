# Copyright 2017, Ansible by Red Hat
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

import os
import sys

import click

import tower_cli
from tower_cli import __version__
from tower_cli.utils import secho
from tower_cli.cli.resource import ResSubcommand
from tower_cli.cli import misc


class TowerCLI(click.MultiCommand):
    """Tower CLI is a command-line interface tool for interacting with
    [Ansible Tower][1]. It allows basic CRUD operations and job control
    from the Unix shell.

      [1]: http://www.ansible.com/tower/
    """
    def _get_all_res(self):
        pass

    def _get_all_misc_cmds(self):
        pass

    def list_commands(self, ctx):
        """Return a list of commands present in the commands and resources
        folders, but not subcommands.
        """
        answer = set()
        for filename in os.listdir('%s/%s/' % (tower_cli.whereami, 'resources')):
            if filename.endswith('.py') and not filename.startswith('_'):
                res = tower_cli.get_resource(filename[:-3])
                if not getattr(res, 'internal', False):
                    answer.add(filename[:-3])
        for cmd_name in misc.__all__:
            answer.add(cmd_name)
        return sorted(answer)

    def get_command(self, ctx, name):
        """Given a command identified by its name, import the appropriate
        module and return the decorated command.

        Resources are automatically commands, but if both a resource and
        a command are defined, the command takes precedence.
        """
        # First, attempt to get a basic command from `tower_cli.api.misc`.
        if name in misc.__all__:
            return getattr(misc, name)

        # No command was found; try to get a resource.
        try:
            resource = tower_cli.get_resource(name)
            return ResSubcommand(resource)
        except ImportError:
            pass

        # Okay, we weren't able to find a command.
        secho('No such command: %s.' % name, fg='red', bold=True)
        sys.exit(2)

    def invoke(self, ctx):
        if ctx.params.get('version', False):
            click.echo('Tower CLI %s' % __version__)
        else:
            return super(TowerCLI, self).invoke(ctx)
