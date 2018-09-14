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

import collections
import json
import os
import stat
import warnings

import click
import six

from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from tower_cli import __version__, exceptions as exc
from tower_cli.api import client
from tower_cli.conf import with_global_options, Parser, settings, _apply_runtime_setting
from tower_cli.utils import secho, supports_oauth
from tower_cli.constants import CUR_API_VERSION
from tower_cli.cli.transfer.common import SEND_ORDER

__all__ = ['version', 'config', 'login', 'logout', 'receive', 'send', 'empty']


@click.command()
@with_global_options
def version():
    """Display full version information."""

    # Print out the current version of Tower CLI.
    click.echo('Tower CLI %s' % __version__)

    # Print out the current API version of the current code base.
    click.echo('API %s' % CUR_API_VERSION)

    # Attempt to connect to the Ansible Tower server.
    # If we succeed, print a version; if not, generate a failure.
    try:
        r = client.get('/config/')
    except RequestException as ex:
        raise exc.TowerCLIError('Could not connect to Ansible Tower.\n%s' %
                                six.text_type(ex))
    config = r.json()
    license = config.get('license_info', {}).get('license_type', 'open')
    if license == 'open':
        server_type = 'AWX'
    else:
        server_type = 'Ansible Tower'
    click.echo('%s %s' % (server_type, config['version']))

    # Print out Ansible version of server
    click.echo('Ansible %s' % config['ansible_version'])


def _echo_setting(key):
    """Echo a setting to the CLI."""
    value = getattr(settings, key)
    secho('%s: ' % key, fg='magenta', bold=True, nl=False)
    secho(
        six.text_type(value),
        bold=True,
        fg='white' if isinstance(value, six.text_type) else 'cyan',
    )


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
            'environment': 'Options from environment variables.',
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
                _echo_setting(option)
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
        _echo_setting(key)
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


# TODO:
# Someday it would be nice to create these for us
# Thus the import reference to transfer.common.SEND_ORDER
@click.command()
@click.argument('username', required=True)
@click.option('--password', required=True, prompt=True, hide_input=True)
@click.option('--client-id', required=False)
@click.option('--client-secret', required=False)
@click.option('--scope', required=False, default='write',
              type=click.Choice(['read', 'write']))
@click.option('-v', '--verbose', default=None,
              help='Show information about requests being made.', is_flag=True,
              required=False, callback=_apply_runtime_setting, is_eager=True)
def login(username, password, scope, client_id, client_secret, verbose):
    """
    Retrieves and stores an OAuth2 personal auth token.
    """
    if not supports_oauth():
        raise exc.TowerCLIError(
            'This version of Tower does not support OAuth2.0. Set credentials using tower-cli config.'
        )

    # Explicitly set a basic auth header for PAT acquisition (so that we don't
    # try to auth w/ an existing user+pass or oauth2 token in a config file)

    req = collections.namedtuple('req', 'headers')({})
    if client_id and client_secret:
        HTTPBasicAuth(client_id, client_secret)(req)
        req.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        r = client.post(
            '/o/token/',
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": scope
            },
            headers=req.headers
        )
    elif client_id:
        req.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        r = client.post(
            '/o/token/',
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "client_id": client_id,
                "scope": scope
            },
            headers=req.headers
        )
    else:
        HTTPBasicAuth(username, password)(req)
        r = client.post(
            '/users/{}/personal_tokens/'.format(username),
            data={"description": "Tower CLI", "application": None, "scope": scope},
            headers=req.headers
        )

    if r.ok:
        result = r.json()
        result.pop('summary_fields', None)
        result.pop('related', None)
        if client_id:
            token = result.pop('access_token', None)
        else:
            token = result.pop('token', None)
        if settings.verbose:
            # only print the actual token if -v
            result['token'] = token
        secho(json.dumps(result, indent=1), fg='blue', bold=True)
        config.main(['oauth_token', token, '--scope=user'])


@click.command()
def logout():
    """
    Removes an OAuth2 personal auth token from config.
    """
    if not supports_oauth():
        raise exc.TowerCLIError(
            'This version of Tower does not support OAuth2.0'
        )
    config.main(['oauth_token', '--unset', '--scope=user'])


@click.command()
@with_global_options
@click.option('--organization', required=False, multiple=True)
@click.option('--user', required=False, multiple=True)
@click.option('--team', required=False, multiple=True)
@click.option('--credential_type', required=False, multiple=True)
@click.option('--credential', required=False, multiple=True)
@click.option('--notification_template', required=False, multiple=True)
@click.option('--inventory_script', required=False, multiple=True)
@click.option('--inventory', required=False, multiple=True)
@click.option('--project', required=False, multiple=True)
@click.option('--job_template', required=False, multiple=True)
@click.option('--workflow', required=False, multiple=True)
@click.option('--all', is_flag=True)
def receive(organization=None, user=None, team=None, credential_type=None, credential=None,
            notification_template=None, inventory_script=None, inventory=None, project=None, job_template=None,
            workflow=None, all=None):
    """Export assets from Tower.

    'tower receive' exports one or more assets from a Tower instance

    For all of the possible assets types the TEXT can either be the assets name
    (or username for the case of a user) or the keyword all. Specifying all
    will export all of the assets of that type.

    """

    from tower_cli.cli.transfer.receive import Receiver
    receiver = Receiver()
    assets_to_export = {}
    for asset_type in SEND_ORDER:
        assets_to_export[asset_type] = locals()[asset_type]
    receiver.receive(all=all, asset_input=assets_to_export)


@click.command()
@with_global_options
@click.argument('source', required=False, nargs=-1)
@click.option('--prevent', multiple=True, required=False,
              help='Prevents import of a specific asset type.\n'
              'Multiple prevent options can be passed.\n'
              'If an asset type in the prevent list tries to be imported an error will occur')
@click.option('--exclude', multiple=True, required=False, help='Ignore specific asset type.\n'
              'Multiple exclude options can be passed.\n'
              'If an asset type in the exclude list tries to be imprted it will be ignored without an error')
@click.option('--secret_management', multiple=False, required=False, default='default',
              type=click.Choice(['default', 'prompt', 'random']),
              help='What to do with secrets for new items.\n'
              'default - use "password", "token" or "secret" depending on the field'
              'prompt - prompt for the secret to use'
              'random - generate a random string for the secret'
              )
@click.option('--no-color', is_flag=True,
              help="Disable color output"
              )
def send(source=None, prevent=None, exclude=None, secret_management='default', no_color=False):
    """Import assets into Tower.

    'tower send' imports one or more assets into a Tower instance

    The import can take either JSON or YAML.
    Data can be sent on stdin (i.e. from tower-cli receive pipe) and/or from files
    or directories passed as parameters.

    If a directory is specified only files that end in .json, .yaml or .yml will be
    imported. Other files will be ignored.
    """

    from tower_cli.cli.transfer.send import Sender
    sender = Sender(no_color)
    sender.send(source, prevent, exclude, secret_management)


@click.command()
@with_global_options
@click.option('--organization', required=False, multiple=True)
@click.option('--user', required=False, multiple=True)
@click.option('--team', required=False, multiple=True)
@click.option('--credential_type', required=False, multiple=True)
@click.option('--credential', required=False, multiple=True)
@click.option('--notification_template', required=False, multiple=True)
@click.option('--inventory_script', required=False, multiple=True)
@click.option('--inventory', required=False, multiple=True)
@click.option('--project', required=False, multiple=True)
@click.option('--job_template', required=False, multiple=True)
@click.option('--workflow', required=False, multiple=True)
@click.option('--all', is_flag=True)
@click.option('--no-color', is_flag=True,
              help="Disable color output"
              )
def empty(organization=None, user=None, team=None, credential_type=None, credential=None, notification_template=None,
          inventory_script=None, inventory=None, project=None, job_template=None, workflow=None,
          all=None, no_color=False):
    """Empties assets from Tower.

    'tower empty' removes all assets from Tower

    """

    # Create an import/export object
    from tower_cli.cli.transfer.cleaner import Cleaner
    destroyer = Cleaner(no_color)
    assets_to_export = {}
    for asset_type in SEND_ORDER:
        assets_to_export[asset_type] = locals()[asset_type]
    destroyer.go_ham(all=all, asset_input=assets_to_export)
