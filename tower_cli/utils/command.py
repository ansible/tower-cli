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


class Command(click.Command):
    """A Command subclass that adds support for the concept that invocation
    without arguments assumes `--help`.

    This code is adapted by taking code from click.MultiCommand and placing
    it here, to get just the --help functionality and nothing else.
    """
    def __init__(self, name=None, no_args_is_help=True, **kwargs):
        self.no_args_is_help = no_args_is_help
        super(Command, self).__init__(name=name, **kwargs)

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
        return super(Command, self).parse_args(ctx, args)
