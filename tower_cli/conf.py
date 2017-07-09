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

import click

import contextlib
import copy
import os
import stat
import warnings
from functools import wraps

import six
from six.moves import configparser
from six import StringIO


__all__ = ['settings', 'with_global_options', 'pop_option']


class Parser(configparser.ConfigParser):
    """ConfigParser subclass that doesn't strictly require section
    headers.
    """
    def _read(self, fp, fpname):
        """Read the configuration from the given file.

        If the file lacks any section header, add a [general] section
        header that encompasses the whole thing.
        """
        # Attempt to read the file using the superclass implementation.
        #
        # Check the permissions of the file we are considering reading
        # if the file exists and the permissions expose it to reads from
        # other users, raise a warning
        if os.path.isfile(fpname):
            file_permission = os.stat(fpname)
            if fpname != '/etc/tower/tower_cli.cfg' and (
                (file_permission.st_mode & stat.S_IRGRP) or
                (file_permission.st_mode & stat.S_IROTH)
            ):
                warnings.warn('File {0} readable by group or others.'
                              .format(fpname), RuntimeWarning)
        # If it doesn't work because there's no section header, then
        # create a section header and call the superclass implementation
        # again.
        try:
            return configparser.ConfigParser._read(self, fp, fpname)
        except configparser.MissingSectionHeaderError:
            fp.seek(0)
            string = '[general]\n%s' % fp.read()
            flo = StringIO(string)  # flo == file-like object
            return configparser.ConfigParser._read(self, flo, fpname)


class Settings(object):
    """An object that understands permanent configuration provided to
    tower-cli through configuration files or command-line arguments.

    The order of precedence for settings, from least to greatest, is:

        - defaults provided in this method
        - `/etc/tower/tower_cli.cfg`
        - `~/.tower_cli.cfg`
        - command line arguments

    """
    _parser_names = ['runtime', 'local', 'user', 'global', 'defaults']

    @staticmethod
    def _new_parser(defaults=None):
        if defaults:
            p = Parser(defaults=defaults)
        else:
            p = Parser()
        p.add_section('general')
        return p

    def __init__(self):
        """Create the settings object, and read from appropriate files as
        well as from `sys.argv`.
        """
        self._cache = {}

        # Initialize the data dictionary for the default level
        # precedence (that is, the bottom of the totem pole).
        defaults = {
            'color': 'true',
            'format': 'human',
            'host': '127.0.0.1',
            'password': '',
            'username': '',
            'verify_ssl': 'true',
            'verbose': 'false',
            'description_on': 'false',
            'certificate': '',
            'use_token': 'false',
        }
        self._defaults = self._new_parser(defaults=defaults)

        # If there is a global settings file, initialize it.
        self._global = self._new_parser()
        if os.path.isdir('/etc/tower/'):
            # Sanity check: Try to get a list of files in `/etc/tower/`.
            #
            # The default Tower installation caused `/etc/tower/` to have
            # extremely restrictive permissions, since it has its own user
            # and group and has a chmod of 0750.
            #
            # This makes it very easy for a user to fall into the mistake
            # of writing a config file under sudo which they then cannot read,
            # which could lead to difficult-to-troubleshoot situations.
            #
            # Therefore, check for that particular problem and give a warning
            # if we're in that situation.
            try:
                os.listdir('/etc/tower/')
            except OSError:
                warnings.warn('/etc/tower/ is present, but not readable with '
                              'current permissions. Any settings defined in '
                              '/etc/tower/tower_cli.cfg will not be honored.',
                              RuntimeWarning)

            # If there is a global settings file for Tower CLI, read in its
            # contents.
            self._global.read('/etc/tower/tower_cli.cfg')

        # Initialize a parser for the user settings file.
        self._user = self._new_parser()

        # If there is a user settings file, read it into the parser object.
        user_filename = os.path.expanduser('~/.tower_cli.cfg')
        self._user.read(user_filename)

        # Initialize a parser for the local settings file.
        self._local = self._new_parser()

        # If there is a local settings file in the current working directory
        # or any parent, read it into the parser object.
        #
        # As a first step, we need to get each of the parents.
        cwd = os.getcwd()
        local_dirs = []
        for i in range(0, len(cwd.split('/'))):
            local_dir = '/'.join(cwd.split('/')[0:i + 1])
            if len(local_dir) == 0:
                local_dir = '/'

            # Sanity check: if this directory corresponds to our global or
            # user directory, skip it.
            if local_dir in (os.path.expanduser('~'), '/etc/tower'):
                continue

            # Add this directory to the list.
            local_dirs.append(local_dir)

        # Iterate over each potential local config file and attempt to read
        # it (most won't exist, which is fine).
        for local_dir in local_dirs:
            local_filename = '%s/.tower_cli.cfg' % local_dir
            self._local.read(local_filename)

        # Put a stubbed runtime parser in.
        self._runtime = self._new_parser()

    def __getattr__(self, key):
        """Return the approprate value, intelligently type-casted in the
        case of numbers or booleans.
        """
        # Sanity check: Have I cached this value? If so, return that.
        if key in self._cache:
            return self._cache[key]

        # Run through each of the parsers and check for a value. Whenever
        # we actually find a value, try to determine the correct type for it
        # and cache and return a value of that type.
        for parser in self._parsers:
            # Get the value from this parser; if it's None, then this
            # key isn't present and we move on to the next one.
            try:
                value = parser.get('general', key)
            except configparser.NoOptionError:
                continue

            # We have a value; it may or may not be a string, though, so
            # try to return it as an int, float, or boolean (in that order)
            # before falling back to the string value.
            type_method = ('getint', 'getfloat', 'getboolean')
            for tm in type_method:
                try:
                    value = getattr(parser, tm)('general', key)
                    break
                except ValueError:
                    pass

            # Write the value to the cache, so we don't have to do this lookup
            # logic on subsequent requests.
            self._cache[key] = value
            return self._cache[key]

        # If we got here, that means that the attribute wasn't found, and
        # also that there is no default; raise an exception.
        raise AttributeError('No setting exists: %s.' % key.lower())

    @property
    def _parsers(self):
        """Return a tuple of all parsers, in order.

        This is referenced at runtime, to avoid gleefully ignoring the
        `runtime_values` context manager.
        """
        return tuple([getattr(self, '_%s' % i) for i in self._parser_names])

    def set_or_reset_runtime_param(self, key, value):
        """Maintains the context of the runtime settings for invoking
        a command.

        This should be called by a click.option callback, and only
        called once for each setting for each command invocation.

        If the setting exists, it follows that the runtime settings are
        stale, so the entire runtime settings are reset.
        """
        if self._runtime.has_option('general', key):
            self._runtime = self._new_parser()

        if value is None:
            return
        settings._runtime.set('general', key.replace('tower_', ''),
                              six.text_type(value))

    @contextlib.contextmanager
    def runtime_values(self, **kwargs):
        """Temporarily override the runtime settings, which exist at the
        highest precedence level.
        """
        kwargs = config_from_environment(kwargs)

        # Coerce all values to strings (to be coerced back by configparser
        # later) and defenestrate any None values.
        for k, v in copy.copy(kwargs).items():
            # If the value is None, just get rid of it.
            if v is None:
                kwargs.pop(k)
                continue

            # Remove these keys from the cache, if they are present.
            self._cache.pop(k, None)

            # Coerce values to strings.
            kwargs[k] = six.text_type(v)

        # Replace the `self._runtime` INI parser with a new one, using
        # the context manager's kwargs as the "defaults" (there can never
        # be anything other than defaults, but that isn't a problem for our
        # purposes because we're using our own precedence system).
        #
        # Ensure that everything is put back to rights at the end of the
        # context manager call.
        old_runtime_parser = self._runtime
        try:
            self._runtime = Parser(defaults=kwargs)
            self._runtime.add_section('general')
            yield self
        finally:
            # Revert the runtime configparser object.
            self._runtime = old_runtime_parser

            # Remove the keys from the cache again, since the settings
            # have been reverted.
            for key in kwargs:
                self._cache.pop(k, None)


def config_from_environment(kwargs):
    """Read tower-cli config values from the environment if present, being
    careful not to override config values that were explicitly passed in.
    """
    CONFIG_OPTIONS = ('host', 'username', 'password', 'verify_ssl', 'format',
                      'color', 'verbose', 'description_on', 'certificate',
                      'use_token')
    kwargs = copy.copy(kwargs)
    for k in CONFIG_OPTIONS:
        if k not in kwargs or kwargs[k] is None:
            env = 'TOWER_' + k.upper()
            v = os.getenv(env, None)
            if v is not None:
                kwargs[k] = v
    return kwargs


# The primary way to interact with settings is to simply hit the
# already constructed settings object.
settings = Settings()


def _apply_runtime_setting(ctx, param, value):
    settings.set_or_reset_runtime_param(param.name, value)


SETTINGS_PARMS = set([
    'tower_host', 'tower_password', 'format', 'tower_username', 'verbose',
    'description_on', 'insecure', 'certificate', 'use_token'
])


def runtime_context_manager(method):
    @wraps(method)
    def method_with_context_managed(*args, **kwargs):
        # Remove the settings before running the method
        for key in SETTINGS_PARMS:
            kwargs.pop(key, None)
        method(*args, **kwargs)
        # Destroy the runtime settings
        settings._runtime = settings._new_parser()
    return method_with_context_managed


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
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)
    method = click.option(
        '-u', '--tower-username',
        help='Username to use to authenticate to Ansible Tower. '
             'This will take precedence over a username provided to '
             '`tower config`, if any.',
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)
    method = click.option(
        '-p', '--tower-password',
        help='Password to use to authenticate to Ansible Tower. '
             'This will take precedence over a password provided to '
             '`tower config`, if any.',
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)

    # Create a global verbose/debug option.
    method = click.option(
        '-f', '--format',
        help='Output format. The "human" format is intended for humans '
             'reading output on the CLI; the "json" and "yaml" formats '
             'provide more data, and "id" echos the object id only.',
        type=click.Choice(['human', 'json', 'yaml', 'id']),
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)
    method = click.option(
        '-v', '--verbose',
        default=None,
        help='Show information about requests being made.',
        is_flag=True,
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)
    method = click.option(
        '--description-on',
        default=None,
        help='Show description in human-formatted output.',
        is_flag=True,
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)

    # Create a global SSL warning option.
    method = click.option(
        '--insecure',
        default=None,
        help='Turn off insecure connection warnings. Set config verify_ssl '
             'to make this permanent.',
        is_flag=True,
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)

    # Create a custom certificate specification option.
    method = click.option(
        '--certificate',
        default=None,
        help='Path to a custom certificate file that will be used throughout'
             ' the command. Overwritten by --insecure flag if set.',
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)

    method = click.option(
        '--use-token',
        default=None,
        help='Turn on Tower\'s token-based authentication. Set config'
             ' use_token to make this permanent.',
        is_flag=True,
        required=False, callback=_apply_runtime_setting,
        is_eager=True
    )(method)
    # Manage the runtime settings context
    method = runtime_context_manager(method)

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
