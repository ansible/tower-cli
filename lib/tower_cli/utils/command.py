# Copyright 2014, Ansible, Inc.
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
    """
    # For some reason, click only supports this in `click.MultiCommand`.
    # Should that change, it would be possible to just use the `click.Command`
    # class instead of this one.
    parse_args = click.MultiCommand.parse_args

    def __init__(self, name=None, no_args_is_help=True, **kwargs):
        self.no_args_is_help = no_args_is_help
        super(Command, self).__init__(name=name, **kwargs)
