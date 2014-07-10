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

import contextlib
import copy
import os
import warnings

import six
from six.moves import configparser
from six import StringIO

from sdict import adict


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
        - `/etc/awx/tower_cli.cfg`
        - `~/.tower_cli.cfg`
        - command line arguments

    """
    _parser_names = ['runtime', 'user', 'global', 'defaults']

    def __init__(self):
        """Create the settings object, and read from appropriate files as
        well as from `sys.argv`.
        """
        self._cache = {}

        # Initialize the data dictionary for the default level
        # precedence (that is, the bottom of the totem pole).
        defaults = {
            'format': 'human',
            'host': '127.0.0.1',
            'password': '',
            'username': '',
            'verbose': 'false',
        }
        self._defaults = Parser(defaults=defaults)
        self._defaults.add_section('general')

        # If there is a global settings file, initialize it.
        self._global = Parser()
        self._global.add_section('general')
        if os.path.isdir('/etc/awx/'):
            # Sanity check: Try to actually get a list of files in `/etc/awx/`.
            # 
            # The default Tower installation caused `/etc/awx/` to have
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
                global_settings = 'tower_cli.cfg' in os.listdir('/etc/awx/')
            except OSError:
                warnings.warn('/etc/awx/ is present, but not readable with '
                              'current permissions. Any settings defined in '
                              '/etc/awx/tower_cli.cfg will not be honored.',
                              RuntimeWarning)

            # If there is a global settings file for Tower CLI, read in its
            # contents.
            self._global.read('/etc/awx/tower_cli.cfg')

        # Initialize a parser for the user settings file.
        self._user = Parser()
        self._user.add_section('general')

        # If there is a user settings file, read it into the parser
        # object.
        user_filename = os.path.expanduser('~/.tower_cli.cfg')
        self._user.read(user_filename)

        # Put a stubbed runtime parser in.
        self._runtime = Parser()
        self._runtime.add_section('general')

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

    @contextlib.contextmanager
    def runtime_values(self, **kwargs):
        """Temporarily override the runtime settings, which exist at the
        highest precedence level.
        """
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


# The primary way to interact with settings is to simply hit the
# already constructed settings object.
settings = Settings()
