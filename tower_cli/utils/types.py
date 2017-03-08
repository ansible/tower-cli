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

from __future__ import absolute_import, unicode_literals
import os
import re
import six

import click

import tower_cli
from tower_cli.utils import debug, exceptions as exc
from tower_cli.utils.compat import OrderedDict


class File(click.File):
    """A subclass of click.File that adds `os.path.expanduser`."""

    __name__ = 'file'

    def convert(self, value, param, ctx):
        if hasattr(value, 'read') or hasattr(value, 'write'):
            return value
        value = os.path.expanduser(value)
        return super(File, self).convert(value, param, ctx)


class Variables(click.File):
    """Allows reading from a file optionally with '@' prefix,
    otherwise passes through string as-is
    """
    name = 'variables'
    __name__ = 'variables'

    def convert(self, value, param, ctx):
        """Return file content if file, else, return value as-is
        """
        # Protect against corner cases of invalid inputs
        if not isinstance(value, str):
            return value
        if isinstance(value, six.binary_type):
            value = value.decode('UTF-8')
        # Read from a file under these cases
        if value.startswith('@'):
            filename = os.path.expanduser(value[1:])
            file_obj = super(Variables, self).convert(filename, param, ctx)
            if hasattr(file_obj, 'read'):
                # Sometimes click.File may return a buffer and not a string
                return file_obj.read()
            return file_obj

        # No file, use given string
        return value


class MappedChoice(click.Choice):
    """A subclass of click.Choice that allows a distinction between the
    choice sent to the method and the choice typed on the CLI.
    """
    __name__ = 'mapped_choice'

    def __init__(self, choices):
        # Call the superclass constructor and send it the **values**.
        # This will make the `click.Choice` things work as expected, since
        # the values are what we are interested in showing the person using
        # the command.
        choices = OrderedDict(choices)
        super(MappedChoice, self).__init__([i for i in choices.values()])

        # Save the keys the MappedChoice instance, and the `convert` method
        # will convert from values to keys.
        self.actual_choices = [i for i in choices.keys()]

    def convert(self, value, param, ctx):
        """Match against the appropriate choice value using the superclass
        implementation, and then return the actual choice.
        """
        choice = super(MappedChoice, self).convert(value, param, ctx)
        ix = self.choices.index(choice)
        return self.actual_choices[ix]


class Related(click.types.ParamType):
    """A subclass of click.types.ParamType that represents a value
    related to another resource.
    """
    __name__ = 'related'
    name = 'related'

    def __init__(self, resource_name):
        super(Related, self).__init__()
        self.resource_name = resource_name

    def convert(self, value, param, ctx):
        """Return the appropriate interger value. If a non-integer is
        provided, attempt a name-based lookup and return the primary key.
        """
        resource = tower_cli.get_resource(self.resource_name)

        # Ensure that None is passed through without trying to
        # do anything.
        if value is None:
            return None

        # If we were already given an integer, do nothing.
        # This ensures that the convert method is idempotent.
        if isinstance(value, int):
            return value

        # Do we have a string that contains only digits?
        # If so, then convert it to an integer and return it.
        if re.match(r'^[\d]+$', value):
            return int(value)

        # Special case to allow disassociations
        if value == 'null':
            return value

        # Okay, we have a string. Try to do a name-based lookup on the
        # resource, and return back the ID that we get from that.
        #
        # This has the chance of erroring out, which is fine.
        try:
            debug.log('The %s field is given as a name; '
                      'looking it up.' % param.name, header='details')
            rel = resource.get(**{resource.identity[-1]: value})
        except exc.MultipleResults as ex:
            raise exc.MultipleRelatedError(
                'Cannot look up {0} exclusively by name, because multiple {0} '
                'objects exist with that name.\n'
                'Please send an ID. You can get the ID for the {0} you want '
                'with:\n'
                '  tower-cli {0} list --name "{1}"'.format(self.resource_name,
                                                           value),
            )
        except exc.TowerCLIError as ex:
            raise exc.RelatedError('Could not get %s. %s' %
                                   (self.resource_name, str(ex)))

        # Done! Return the ID.
        return rel['id']

    def get_metavar(self, param):
        return self.resource_name.upper()
