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

import os
import stat
import warnings

import six

import click

from tower_cli.conf import Parser, settings
from tower_cli.utils import exceptions as exc, secho


# Note: This uses `click.command`, not `tower_cli.utils.decorators.command`,
# because we don't want the "global" options that t.u.d.command adds.
@click.command()
@click.argument('key', required=False)
@click.argument('value', required=False)
@click.option('global_', '--global', is_flag=True,
              help='Write this config option to the global configuration. '
                   'Probably will require sudo.\n'
                   'Deprecated: Use `--scope=global` instead.')
@click.option('--scope', type=click.Choice(['local', 'user', 'global']),
              default='user',
              help='The config file to write. '
                   '"local" writes to a config file in the local '
                   'directory; "user" writes to the home directory,'
                   ' and "global" to a system-wide directory '
                   '(probably requires sudo).')
@click.option('--unset', is_flag=True,
              help='Remove reference to this configuration option from '
                   'the config file.')
def config(key=None, value=None, scope='user', global_=False, unset=False):
    """Read or write tower-cli configuration.

    `tower config` saves the given setting to the appropriate Tower CLI;
    either the user's ~/.tower_cli.cfg file, or the /etc/tower/tower_cli.cfg
    file if --global is used.

    Writing to /etc/tower/tower_cli.cfg is likely to require heightened
    permissions (in other words, sudo).
    """
    # If the old-style `global_` option is set, issue a deprecation notice.
    if global_:
        scope = 'global'
        warnings.warn('The `--global` option is deprecated and will be '
                      'removed. Use `--scope=global` to get the same effect.',
                      DeprecationWarning)

    # If no key was provided, print out the current configuration
    # in play.
    if not key:
        seen = set()
        parser_desc = {
            'runtime': 'Runtime options.',
            'local': 'Local options (set with `tower-cli config '
                     '--scope=local`; stored in .tower_cli.cfg of this '
                     'directory or a parent)',
            'user': 'User options (set with `tower-cli config`; stored in '
                    '~/.tower_cli.cfg).',
            'global': 'Global options (set with `tower-cli config '
                      '--scope=global`, stored in /etc/tower/tower_cli.cfg).',
            'defaults': 'Defaults.',
        }

        # Iterate over each parser (English: location we can get settings from)
        # and print any settings that we haven't already seen.
        #
        # We iterate over settings from highest precedence to lowest, so any
        # seen settings are overridden by the version we iterated over already.
        click.echo('')
        for name, parser in zip(settings._parser_names, settings._parsers):
            # Determine if we're going to see any options in this
            # parser that get echoed.
            will_echo = False
            for option in parser.options('general'):
                if option in seen:
                    continue
                will_echo = True

            # Print a segment header
            if will_echo:
                secho('# %s' % parser_desc[name], fg='green', bold=True)

            # Iterate over each option in the parser and, if we haven't
            # already seen an option at higher precedence, print it.
            for option in parser.options('general'):
                if option in seen:
                    continue
                echo_setting(option)
                seen.add(option)

            # Print a nice newline, for formatting.
            if will_echo:
                click.echo('')
        return

    # Sanity check: Is this a valid configuration option? If it's not
    # a key we recognize, abort.
    if not hasattr(settings, key):
        raise exc.TowerCLIError('Invalid configuration option "%s".' % key)

    # Sanity check: The combination of a value and --unset makes no
    # sense.
    if value and unset:
        raise exc.UsageError('Cannot provide both a value and --unset.')

    # If a key was provided but no value was provided, then just
    # print the current value for that key.
    if key and not value and not unset:
        echo_setting(key)
        return

    # Okay, so we're *writing* a key. Let's do this.
    # First, we need the appropriate file.
    filename = os.path.expanduser('~/.tower_cli.cfg')
    if scope == 'global':
        if not os.path.isdir('/etc/tower/'):
            raise exc.TowerCLIError('/etc/tower/ does not exist, and this '
                                    'command cowardly declines to create it.')
        filename = '/etc/tower/tower_cli.cfg'
    elif scope == 'local':
        filename = '.tower_cli.cfg'

    # Read in the appropriate config file, write this value, and save
    # the result back to the file.
    parser = Parser()
    parser.add_section('general')
    parser.read(filename)
    if unset:
        parser.remove_option('general', key)
    else:
        parser.set('general', key, value)
    with open(filename, 'w') as config_file:
        parser.write(config_file)

    # Give rw permissions to user only fix for issue number 48
    try:
        os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)
    except Exception as e:
        warnings.warn(
            'Unable to set permissions on {0} - {1} '.format(filename, e),
            UserWarning
            )
    click.echo('Configuration updated successfully.')


def echo_setting(key):
    """Echo a setting to the CLI."""
    value = getattr(settings, key)
    secho('%s: ' % key, fg='magenta', bold=True, nl=False)
    secho(
        six.text_type(value),
        bold=True,
        fg='white' if isinstance(value, six.text_type) else 'cyan',
    )
