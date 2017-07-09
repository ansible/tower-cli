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

from __future__ import absolute_import, division

import functools
import inspect
import json
import yaml
import math
import re
from copy import copy

import six

import click

from tower_cli.conf import settings, with_global_options
from tower_cli.utils import parser, debug, secho
from tower_cli.cli.action import ActionSubcommand
from tower_cli.exceptions import MultipleRelatedError


class ResSubcommand(click.MultiCommand):
    """A subcommand that implements all command methods on the
    Resource.
    """
    def __init__(self, resource, *args, **kwargs):
        self.resource = resource
        self.resource_name = getattr(
            resource, 'resource_name',
            resource.__module__.split('.')[-1]
        )
        self.resource_name = self.resource_name.replace('_', ' ')
        super(ResSubcommand, self).__init__(
            *args,
            help=self.resource.cli_help,
            **kwargs
        )

    def list_commands(self, ctx):
        """Return a list of all methods decorated with the
        @resources.command decorator.
        """
        return self.resource.commands

    def _auto_help_text(self, help_text):
        """Given a method with a docstring, convert the docstring
        to more CLI appropriate wording, and also disambiguate the
        word "object" on the base class docstrings.
        """
        # Convert the word "object" to the appropriate type of
        # object being modified (e.g. user, organization).
        an_prefix = ('a', 'e', 'i', 'o')
        if not self.resource_name.lower().startswith(an_prefix):
            help_text = help_text.replace('an object',
                                          'a %s' % self.resource_name)
        if self.resource_name.lower().endswith('y'):
            help_text = help_text.replace(
                'objects',
                '%sies' % self.resource_name[:-1],
            )
        help_text = help_text.replace('object', self.resource_name)

        # Convert some common Python terms to their CLI equivalents.
        help_text = help_text.replace('keyword argument', 'option')
        help_text = help_text.replace('raise an exception',
                                      'abort with an error')

        # Convert keyword arguments specified in docstrings enclosed
        # by backticks to switches.
        for match in re.findall(r'`([\w_]+)`', help_text):
            option = '--%s' % match.replace('_', '-')
            help_text = help_text.replace('`%s`' % match, option)

        # Done; return the new help text.
        return help_text

    def _echo_method(self, method):
        """Given a method, return a method that runs the internal
        method and echos the result.
        """
        @functools.wraps(method)
        def func(*args, **kwargs):
            # Echo warning if this method is deprecated.
            if getattr(method, 'deprecated', False):
                debug.log('This method is deprecated in Tower 3.0.',
                          header='warning')

            result = method(*args, **kwargs)

            # If this was a request that could result in a modification
            # of data, print it in Ansible coloring.
            color_info = {}
            if 'changed' in result:
                if result['changed']:
                    color_info['fg'] = 'yellow'
                else:
                    color_info['fg'] = 'green'

            # Piece together the result into the proper format.
            format = getattr(self, '_format_%s' % settings.format)
            output = format(result)

            # Perform the echo.
            secho(output, **color_info)
        return func

    def _format_json(self, payload):
        """Convert the payload into a JSON string with proper
        indentation and return it.
        """
        return json.dumps(payload, indent=2)

    def _format_yaml(self, payload):
        """Convert the payload into a YAML string with proper
        indentation and return it.
        """
        return parser.ordered_dump(payload, Dumper=yaml.SafeDumper,
                                   default_flow_style=False)

    def _format_id(self, payload):
        """Echos only the id"""
        if 'id' in payload:
            return str(payload['id'])
        if 'results' in payload and payload['count'] == 1:
            return str(payload['results'][0]['id'])
        raise MultipleRelatedError(
            'Can not use id format when multiple objects are returned.')

    def _format_human(self, payload):
        """Convert the payload into an ASCII table suitable for
        printing on screen and return it.
        """
        page = None
        total_pages = None

        # What are the columns we will show?
        columns = [field.name for field in self.resource.fields
                   if field.display or settings.description_on and
                   field.name == 'description']
        columns.insert(0, 'id')

        # Save a dictionary-by-name of fields for later use
        fields_by_name = {}
        for field in self.resource.fields:
            fields_by_name[field.name] = field

        # Sanity check: If there is a "changed" key in our payload
        # and little else, we print a short message and not a table.
        # this specifically applies to deletion
        if 'changed' in payload and 'id' not in payload:
            return 'OK. (changed: {0})'.format(
                six.text_type(payload['changed']).lower(),
            )

        # Sanity check: If there is no ID and no results, then this
        # is unusual output; keep our table formatting, but plow
        # over the columns-as-keys stuff above.
        # this originally applied to launch/status/update methods
        # but it may become deprecated
        if 'id' not in payload and 'results' not in payload:
            columns = [i for i in payload.keys()]

        # Get our raw rows into a standard format.
        if 'results' in payload:
            raw_rows = payload['results']
            if payload.get('count', 0) > len(payload['results']):
                prev = payload.get('previous', 0) or 0
                page = prev + 1
                count = payload['count']
                if payload.get('next', None):
                    total_pages = math.ceil(count / len(raw_rows))
                else:
                    total_pages = page
        else:
            raw_rows = [payload]

        # If we have no rows to display, return this information
        # and don't do any further processing.
        if not raw_rows:
            return 'No records found.'

        # Determine the width for each column.
        widths = {}
        for col in columns:
            widths[col] = max(
                len(col),
                *[len(six.text_type(i.get(col, 'N/A'))) for i in raw_rows]
            )
            fd = fields_by_name.get(col, None)
            if fd is not None and fd.col_width is not None:
                widths[col] = fd.col_width

        # It's possible that the column widths will exceed our terminal
        # width; if so, reduce column widths accordingly.
        # TODO: Write this.

        # Put together the divider row.
        # This is easy and straightforward: it's simply a table divider
        # using the widths calculated.
        divider_row = ''
        for col in columns:
            divider_row += '=' * widths[col] + ' '
        divider_row.rstrip()

        # Put together the header row.
        # This is also easy and straightforward; simply center the
        # headers (which str.format does for us!).
        header_row = ''
        for col in columns:
            header_row += ('{0:^%d}' % widths[col]).format(col) + ' '
        header_row.rstrip()

        # Piece together each row of data.
        data_rows = []
        for raw_row in raw_rows:
            data_row = ''
            for col in columns:
                template = '{0:%d}' % widths[col]
                value = raw_row.get(col, 'N/A')
                if isinstance(raw_row.get(col, 'N/A'), bool):
                    template = template.replace('{0:', '{0:>')
                    value = six.text_type(value).lower()
                # Truncate the cell entry if exceeds manually
                # specified column width limit
                fd = fields_by_name.get(col, None)
                if fd is not None and fd.col_width is not None:
                    str_value = template.format(value or '')
                    if len(str_value) > fd.col_width:
                        value = str_value[:fd.col_width]
                data_row += template.format(value or '') + ' '
            data_rows.append(data_row.rstrip())

        # Result the resulting table.
        response = '\n'.join((
            divider_row, header_row, divider_row,
            '\n'.join(data_rows),
            divider_row,
        ))
        if page:
            response += '(Page %d of %d.)' % (page, total_pages)
        if payload.get('changed', False):
            response = 'Resource changed.\n' + response
        return response

    def get_command(self, ctx, name):
        """Retrieve the appropriate method from the Resource,
        decorate it as a click command, and return that method.
        """
        # Sanity check: Does a method exist corresponding to this
        # command? If not, None is returned for click to raise
        # exception.
        if not hasattr(self.resource, name):
            return None

        # Get the method.
        method = getattr(self.resource, name)

        # Get any attributes that were given at command-declaration
        # time.
        attrs = getattr(method, '_cli_command_attrs', {})

        # If the help message comes from the docstring, then
        # convert it into a message specifically for this resource.
        help_text = inspect.getdoc(method)
        attrs['help'] = self._auto_help_text(help_text or '')

        # On some methods, we ignore the defaults, which are intended
        # for writing and not reading; process this.
        ignore_defaults = attrs.pop('ignore_defaults', False)

        # Wrap the method, such that it outputs its final return
        # value rather than returning it.
        new_method = self._echo_method(method)

        # Soft copy the "__click_params__", if any exist.
        # This is the internal holding method that the click library
        # uses to store @click.option and @click.argument directives
        # before the method is converted into a command.
        #
        # Because self._echo_method uses @functools.wraps, this is
        # actually preserved; the purpose of copying it over is
        # so we can get our resource fields at the top of the help;
        # the easiest way to do this is to load them in before the
        # conversion takes place. (This is a happy result of Armin's
        # work to get around Python's processing decorators
        # bottom-to-top.)
        click_params = getattr(method, '__click_params__', [])
        new_method.__click_params__ = copy(click_params)
        new_method = with_global_options(new_method)

        # Write options based on the fields available on this resource.
        fao = attrs.pop('use_fields_as_options', True)
        if fao:
            for field in reversed(self.resource.fields):
                if not field.is_option:
                    continue

                # If we got an iterable rather than a boolean,
                # then it is a list of fields to use; check for
                # presence in that list.
                if not isinstance(fao, bool) and field.name not in fao:
                    continue

                # Create the initial arguments based on the
                # option value. If we have a different key to use
                # (which is what gets routed to the Tower API),
                # ensure that is the first argument.
                args = [field.option]
                if field.key:
                    args.insert(0, field.key)

                # short name aliases for common flags
                short_fields = {
                    'name': 'n',
                    'description': 'd',
                    'inventory': 'i',
                    'extra_vars': 'e'
                }
                if field.name in short_fields:
                    args.append('-'+short_fields[field.name])

                # Apply the option to the method.
                option_help = field.help
                if field.required:
                    option_help = '[REQUIRED] ' + option_help
                option_help = '[FIELD]' + option_help
                click.option(
                    *args,
                    default=field.default if not ignore_defaults else None,
                    help=option_help,
                    type=field.type,
                    show_default=field.show_default,
                    multiple=field.multiple,
                    is_eager=False
                )(new_method)

        # Make a click Command instance using this method
        # as the callback, and return it.
        cmd = click.command(name=name, cls=ActionSubcommand, **attrs)(new_method)

        # If this method has a `pk` positional argument,
        # then add a click argument for it.
        code = six.get_function_code(method)
        if 'pk' in code.co_varnames:
            click.argument('pk', nargs=1, required=False, type=str, metavar='[ID]')(cmd)

        # Done; return the command.
        return cmd
