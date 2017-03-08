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

from __future__ import absolute_import

import functools
import types

import click

from tower_cli.conf import settings


def command(method=None, **kwargs):
    """Cause the given function to become a click command, and add all
    global options.
    """
    # Define the actual decorator.
    # This is done in such a way as to allow @command, @command(), and
    # @command(foo='bar') to all work.
    def actual_decorator(method):
        # Create a wrapper function that will "eat" the authentication
        # if it's provided as keyword arguments and apply it to settings.
        @with_global_options
        @click.command(**kwargs)
        @functools.wraps(method)
        def answer(*inner_a, **inner_kw):
            runtime_settings = {
                'host': inner_kw.pop('tower_host', None),
                'password': inner_kw.pop('tower_password', None),
                'format': inner_kw.pop('format', None),
                'username': inner_kw.pop('tower_username', None),
                'verbose': inner_kw.pop('verbose', None),
                'description_on': inner_kw.pop('description_on', None),
                'insecure': inner_kw.pop('insecure', None),
                'certificate': inner_kw.pop('certificate', None)
            }
            with settings.runtime_values(**runtime_settings):
                return method(*inner_a, **inner_kw)

        # Done, return the wrapped-wrapped-wrapped-wrapped method.
        # BECAUSE WE WRAP ALL THE THINGS!
        return answer

    # If we got the method straight-up, apply the decorator and return
    # the decorated method; otherwise, return the actual decorator for
    # the Python interpreter to apply.
    if method and isinstance(method, types.FunctionType):
        return actual_decorator(method)
    else:
        return actual_decorator


def with_global_options(method):
    """Apply the global options that we desire on every method within
    tower-cli to the given click command.
    """
    # Create global options for the Tower host, username, and password.
    #
    # These are runtime options that will override the configuration file
    # settings.
    method = click.option(
        '-h', '--tower-host',
        help='The location of the Ansible Tower host. '
             'HTTPS is assumed as the protocol unless "http://" is explicitly '
             'provided. This will take precedence over a host provided to '
             '`tower config`, if any.',
        required=False,
    )(method)
    method = click.option(
        '-u', '--tower-username',
        help='Username to use to authenticate to Ansible Tower. '
             'This will take precedence over a username provided to '
             '`tower config`, if any.',
        required=False,
    )(method)
    method = click.option(
        '-p', '--tower-password',
        help='Password to use to authenticate to Ansible Tower. '
             'This will take precedence over a password provided to '
             '`tower config`, if any.',
        required=False,
    )(method)

    # Create a global verbose/debug option.
    method = click.option(
        '-f', '--format',
        help='Output format. The "human" format is intended for humans '
             'reading output on the CLI; the "json" and "yaml" formats '
             'provide more data.',
        type=click.Choice(['human', 'json', 'yaml']),
        required=False,
    )(method)
    method = click.option(
        '-v', '--verbose',
        default=None,
        help='Show information about requests being made.',
        is_flag=True,
        required=False,
    )(method)
    method = click.option(
        '--description-on',
        default=None,
        help='Show description in human-formatted output.',
        is_flag=True,
        required=False,
    )(method)

    # Create a global SSL warning option.
    method = click.option(
        '--insecure',
        default=None,
        help='Turn off insecure connection warnings. Set config verify_ssl '
             'to make this permanent.',
        is_flag=True,
        required=False,
    )(method)

    # Create a custom certificate specification option.
    method = click.option(
        '--certificate',
        default=None,
        help='Path to a custom certificate file that will be used throughout'
             ' the command. Overwritten by --insecure flag if set.',
        required=False,
    )(method)

    # Okay, we're done adding options; return the method.
    return method


def pop_option(function, name):
    """
    Used to remove an option applied by the @click.option decorator.

    This is useful for when you want to subclass a decorated resource command
    and *don't* want all of the options provided by the parent class'
    implementation.
    """
    for option in getattr(function, '__click_params__', tuple()):
        if option.name == name:
            function.__click_params__.remove(option)
