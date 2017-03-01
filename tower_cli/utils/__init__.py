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

import functools

import click

from tower_cli.conf import settings


@functools.wraps(click.secho)
def secho(message, **kwargs):
    """A wrapper around click.secho that disables any coloring being used
    if colors have been disabled.
    """
    # If colors are disabled, remove any color or other style data
    # from keyword arguments.
    if not settings.color:
        for key in ('fg', 'bg', 'bold', 'blink'):
            kwargs.pop(key, None)

    # Okay, now call click.secho normally.
    return click.secho(message, **kwargs)
