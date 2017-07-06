# Copyright 2017, Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
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
from click.formatting import join_options

from tower_cli.conf import SETTINGS_PARMS


class ActionSubcommand(click.Command):
    """A Command subclass that adds support for the concept that invocation
    without arguments assumes `--help`.

    This code is adapted by taking code from click.MultiCommand and placing
    it here, to get just the --help functionality and nothing else.
    """
    def __init__(self, name=None, no_args_is_help=True, **kwargs):
        self.no_args_is_help = no_args_is_help
        super(ActionSubcommand, self).__init__(name=name, **kwargs)

    def parse_args(self, ctx, args):
        """Parse arguments sent to this command.

        The code for this method is taken from MultiCommand:
        https://github.com/mitsuhiko/click/blob/master/click/core.py

        It is Copyright (c) 2014 by Armin Ronacher.
        See the license:
        https://github.com/mitsuhiko/click/blob/master/LICENSE
        """
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            click.echo(ctx.get_help())
            ctx.exit()
        return super(ActionSubcommand, self).parse_args(ctx, args)

    def format_options(self, ctx, formatter):
        """Monkey-patch click's format_options method to support option categorization.
        """
        field_opts = []
        global_opts = []
        local_opts = []
        other_opts = []
        for param in self.params:
            if param.name in SETTINGS_PARMS:
                opts = global_opts
            elif getattr(param, 'help', None) and param.help.startswith('[FIELD]'):
                opts = field_opts
                param.help = param.help[len('[FIELD]'):]
            else:
                opts = local_opts
            rv = param.get_help_record(ctx)
            if rv is None:
                continue
            else:
                opts.append(rv)

        if self.add_help_option:
            help_options = self.get_help_option_names(ctx)
            if help_options:
                other_opts.append([join_options(help_options)[0], 'Show this message and exit.'])

        if field_opts:
            with formatter.section('Field Options'):
                formatter.write_dl(field_opts)
        if local_opts:
            with formatter.section('Local Options'):
                formatter.write_dl(local_opts)
        if global_opts:
            with formatter.section('Global Options'):
                formatter.write_dl(global_opts)
        if other_opts:
            with formatter.section('Other Options'):
                formatter.write_dl(other_opts)
