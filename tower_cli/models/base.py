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

from __future__ import absolute_import, division, unicode_literals

import functools
import inspect
import itertools
import json
import yaml
import math
import re
import sys
import time
from copy import copy
from base64 import b64decode

import six

import click
from click._compat import isatty as is_tty

from tower_cli import resources
from tower_cli.api import client
from tower_cli.conf import settings
from tower_cli.models.fields import Field
from tower_cli.utils import exceptions as exc, parser, debug, secho
from tower_cli.utils.command import Command
from tower_cli.utils.data_structures import OrderedDict
from tower_cli.utils.decorators import command


class ResourceMeta(type):
    """Metaclass for the creation of a Model subclass, which pulls fields
    aside into their appropriate tuple and handles other initialization.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(ResourceMeta, cls).__new__

        # Mark all `@resources.command` methods as CLI commands.
        commands = set()
        for base in bases:
            base_commands = getattr(base, 'commands', [])
            commands = commands.union(base_commands)

        # Read list of deprecated resource methods if present.
        deprecates = attrs.pop('deprecated_methods', [])

        for key, value in attrs.items():
            if getattr(value, '_cli_command', False):
                commands.add(key)
                if key in deprecates:
                    setattr(value, 'deprecated', True)

            # If this method has been overwritten from the superclass, copy
            # any click options or arguments from the superclass implementation
            # down to the subclass implementation.
            if not len(bases):
                continue
            superclass = bases[0]
            super_method = getattr(superclass, key, None)
            if super_method and getattr(super_method, '_cli_command', False):
                # Copy the click parameters from the parent method to the
                # child.
                cp = getattr(value, '__click_params__', [])
                cp = getattr(super_method, '__click_params__', []) + cp
                value.__click_params__ = cp

                # Copy the command attributes from the parent to the child,
                # if the child has not overridden them.
                for attkey, attval in super_method._cli_command_attrs.items():
                    value._cli_command_attrs.setdefault(attkey, attval)
        attrs['commands'] = sorted(commands)

        # Sanity check: Only perform remaining initialization for subclasses
        # actual resources, not abstract ones.
        if attrs.pop('abstract', False):
            return super_new(cls, name, bases, attrs)

        # Initialize a new attributes dictionary.
        newattrs = {}

        # Iterate over each of the fields and move them into a
        # `fields` list; port remaining attrs unchanged into newattrs.
        fields = []
        unique_fields = set()
        for k, v in attrs.items():
            if isinstance(v, Field):
                v.name = k
                fields.append(v)
                if v.unique:
                    unique_fields.add(v.name)
            else:
                newattrs[k] = v
        newattrs['fields'] = sorted(fields)
        newattrs['unique_fields'] = unique_fields

        # Cowardly refuse to create a Resource with no endpoint
        # (unless it's the base class).
        if not newattrs.get('endpoint', None):
            raise TypeError('Resource subclasses must have an `endpoint`.')

        # Ensure that the endpoint ends in a trailing slash, since we
        # expect this when we build URLs based on it.
        if isinstance(newattrs['endpoint'], six.string_types):
            if not newattrs['endpoint'].startswith('/'):
                newattrs['endpoint'] = '/' + newattrs['endpoint']
            if not newattrs['endpoint'].endswith('/'):
                newattrs['endpoint'] += '/'

        # Construct the class.
        return super_new(cls, name, bases, newattrs)


class BaseResource(six.with_metaclass(ResourceMeta)):
    """Abstract class representing resources within the Ansible Tower
    system, on which actions can be taken."""
    abstract = True  # Not inherited.
    cli_help = ''
    endpoint = None
    identity = ('name',)

    def as_command(self):
        """Return a `click.Command` class for interacting with this
        Resource.
        """
        class Subcommand(click.MultiCommand):
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
                super(Subcommand, self).__init__(
                    *args,
                    help=self.resource.cli_help,
                    **kwargs
                )

            def list_commands(self, ctx):
                """Return a list of all methods decorated with the
                @resources.command decorator.
                """
                return self.resource.commands

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
                        click.option(
                            *args,
                            default=field.default if not ignore_defaults
                            else None,
                            help=option_help,
                            type=field.type,
                            show_default=field.show_default,
                            multiple=field.multiple
                        )(new_method)

                # Make a click Command instance using this method
                # as the callback, and return it.
                cmd = command(name=name, cls=Command, **attrs)(new_method)

                # If this method has a `pk` positional argument,
                # then add a click argument for it.
                code = six.get_function_code(method)
                if 'pk' in code.co_varnames:
                    click.argument('pk', nargs=1, required=False,
                                   type=str, metavar='[ID]')(cmd)

                # Done; return the command.
                return cmd

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
                        *[len(six.text_type(i.get(col, 'N/A')))
                          for i in raw_rows]
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

        return Subcommand(resource=self)


class ResourceMethods(BaseResource):
    """Abstract subclass of BaseResource that adds the standard create,
    modify, list, get, and delete methods.

    Some of these methods are not created as commands, but will be
    implemented as commands inside of non-abstract child classes.
    Particularly, create is not a command in this class, but will be for
    some (but not all) child classes."""
    abstract = True  # Not inherited.

    # The basic methods for interacting with a resource are `read`, `write`,
    # and `delete`; these cover basic CRUD situations and have options
    # to handle most desired behavior.
    #
    # Most likely, `read` and `write` won't see much direct use; rather,
    # `get` and `list` are wrappers around `read` and `create` and
    # `modify` are wrappers around `write`.

    def _pop_none(self, kwargs):
        """Remove default values (anything where the value is None).
        click is unfortunately bad at the way it sends through unspecified
        defaults."""
        for key, value in copy(kwargs).items():
            if value is None:
                kwargs.pop(key)
            if hasattr(value, 'read'):
                kwargs[key] = value.read()

    def read(self, pk=None, fail_on_no_results=False,
             fail_on_multiple_results=False, **kwargs):
        """Retrieve and return objects from the Ansible Tower API.

        If an `object_id` is provided, only attempt to read that object,
        rather than the list at large.

        If `fail_on_no_results` is True, then zero results is considered
        a failure case and raises an exception; otherwise, empty list is
        returned. (Note: This is always True if a primary key is included.)

        If `fail_on_multiple_results` is True, then at most one result is
        expected, and more results constitutes a failure case.
        (Note: This is meaningless if a primary key is included, as there can
        never be multiple results.)
        """
        # Piece together the URL we will be hitting.
        url = self.endpoint
        if pk:
            url += '%s/' % pk

        # Pop the query parameter off of the keyword arguments; it will
        # require special handling (below).
        queries = kwargs.pop('query', [])

        # Remove default values (anything where the value is None).
        self._pop_none(kwargs)

        # Remove fields that are specifically excluded from lookup
        for field in self.fields:
            if field.no_lookup and field.name in kwargs:
                kwargs.pop(field.name)

        # If queries were provided, process them.
        for query in queries:
            if query[0] in kwargs:
                raise exc.BadRequest('Attempted to set %s twice.'
                                     % query[0].replace('_', '-'))
            kwargs[query[0]] = query[1]

        # Make the request to the Ansible Tower API.
        r = client.get(url, params=kwargs)
        resp = r.json()

        # If this was a request with a primary key included, then at the
        # point that we got a good result, we know that we're done and can
        # return the result.
        if pk:
            # Make the results all look the same, for easier parsing
            # by other methods.
            #
            # Note that the `get` method will effectively undo this operation,
            # but that's a good thing, because we might use `get` without a
            # primary key.
            return {'count': 1, 'results': [resp]}

        # Did we get zero results back when we shouldn't?
        # If so, this is an error, and we need to complain.
        if fail_on_no_results and resp['count'] == 0:
            raise exc.NotFound('The requested object could not be found.')

        # Did we get more than one result back?
        # If so, this is also an error, and we need to complain.
        if fail_on_multiple_results and resp['count'] >= 2:
            raise exc.MultipleResults('Expected one result, got %d. Possibly '
                                      'caused by not providing required '
                                      'fields. Please tighten '
                                      'your criteria.' % resp['count'])

        # Return the response.
        return resp

    def _get_patch_url(self, url, pk):
        """Overwrite this method to handle specific corner cases to
        the url passed to PATCH method."""
        return url + '%s/' % pk

    def write(self, pk=None, create_on_missing=False, fail_on_found=False,
              force_on_exists=True, **kwargs):
        """Modify the given object using the Ansible Tower API.
        Return the object and a boolean value informing us whether or not
        the record was changed.

        If `create_on_missing` is True, then an object matching the
        appropriate unique criteria is not found, then a new object is created.

        If there are no unique criteria on the model (other than the primary
        key), then this will always constitute a creation (even if a match
        exists) unless the primary key is sent.

        If `fail_on_found` is True, then if an object matching the unique
        criteria already exists, the operation fails.

        If `force_on_exists` is True, then if an object is modified based on
        matching via. unique fields (as opposed to the primary key), other
        fields are updated based on data sent. If `force_on_exists` is set
        to False, then the non-unique values are only written in a creation
        case.
        """
        existing_data = {}

        # Remove default values (anything where the value is None).
        self._pop_none(kwargs)

        # Determine which record we are writing, if we weren't given a
        # primary key.
        if not pk:
            debug.log('Checking for an existing record.', header='details')
            existing_data = self._lookup(
                fail_on_found=fail_on_found,
                fail_on_missing=not create_on_missing,
                include_debug_header=False,
                **kwargs
            )
            if existing_data:
                pk = existing_data['id']
        else:
            # We already know the primary key, but get the existing data.
            # This allows us to know whether the write made any changes.
            debug.log('Getting existing record.', header='details')
            existing_data = self.get(pk)

        # Sanity check: Are we missing required values?
        # If we don't have a primary key, then all required values must be
        # set, and if they're not, it's an error.
        missing_fields = []
        for i in self.fields:
            if i.key not in kwargs and i.name not in kwargs and i.required:
                missing_fields.append(i.key or i.name)
        if missing_fields and not pk:
            raise exc.BadRequest('Missing required fields: %s' %
                                 ', '.join(missing_fields).replace('_', '-'))

        # Sanity check: Do we need to do a write at all?
        # If `force_on_exists` is False and the record was, in fact, found,
        # then no action is required.
        if pk and not force_on_exists:
            debug.log('Record already exists, and --force-on-exists is off; '
                      'do nothing.', header='decision', nl=2)
            answer = OrderedDict((
                ('changed', False),
                ('id', pk),
            ))
            answer.update(existing_data)
            return answer

        # Similarly, if all existing data matches our write parameters,
        # there's no need to do anything.
        if all([kwargs[k] == existing_data.get(k, None)
                for k in kwargs.keys()]):
            debug.log('All provided fields match existing data; do nothing.',
                      header='decision', nl=2)
            answer = OrderedDict((
                ('changed', False),
                ('id', pk),
            ))
            answer.update(existing_data)
            return answer

        # Reinsert None for special case of null association
        for key in kwargs:
            if kwargs[key] == 'null':
                kwargs[key] = None

        # Get the URL and method to use for the write.
        url = self.endpoint
        method = 'POST'
        if pk:
            url = self._get_patch_url(url, pk)
            method = 'PATCH'

        # If debugging is on, print the URL and data being sent.
        debug.log('Writing the record.', header='details')

        # Actually perform the write.
        r = getattr(client, method.lower())(url, data=kwargs)

        # At this point, we know the write succeeded, and we know that data
        # was changed in the process.
        answer = OrderedDict((
            ('changed', True),
            ('id', r.json()['id']),
        ))
        answer.update(r.json())
        return answer

    @resources.command
    def delete(self, pk=None, fail_on_missing=False, **kwargs):
        """Remove the given object.

        If `fail_on_missing` is True, then the object's not being found is
        considered a failure; otherwise, a success with no change is reported.
        """
        # If we weren't given a primary key, determine which record we're
        # deleting.
        if not pk:
            existing_data = self._lookup(fail_on_missing=fail_on_missing,
                                         **kwargs)
            if not existing_data:
                return {'changed': False}
            pk = existing_data['id']

        # Attempt to delete the record.
        # If it turns out the record doesn't exist, handle the 404
        # appropriately (this is an okay response if `fail_on_missing` is
        # False).
        url = '%s%d/' % (self.endpoint, pk)
        debug.log('DELETE %s' % url, fg='blue', bold=True)
        try:
            client.delete(url)
            return {'changed': True}
        except exc.NotFound:
            if fail_on_missing:
                raise
            return {'changed': False}

    # Convenience wrappers around `read` and `write`:
    #   - read:  get, list
    #   - write: create, modify

    @resources.command(ignore_defaults=True)
    def get(self, pk=None, **kwargs):
        """Return one and exactly one object.

        Lookups may be through a primary key, specified as a positional
        argument, and/or through filters specified through keyword arguments.

        If the number of results does not equal one, raise an exception.
        """
        if kwargs.pop('include_debug_header', True):
            debug.log('Getting the record.', header='details')
        response = self.read(pk=pk, fail_on_no_results=True,
                             fail_on_multiple_results=True, **kwargs)
        return response['results'][0]

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    @click.option('all_pages', '-a', '--all-pages',
                  is_flag=True, default=False, show_default=True,
                  help='If set, collate all pages of content from the API '
                       'when returning results.')
    @click.option('--page', default=1, type=int, show_default=True,
                  help='The page to show. Ignored if --all-pages '
                       'is sent.')
    @click.option('-Q', '--query', required=False, nargs=2, multiple=True,
                  help='A key and value to be passed as an HTTP query string '
                       'key and value to the Tower API. Will be run through '
                       'HTTP escaping. This argument may be sent multiple '
                       'times.\nExample: `--query foo bar` would be passed '
                       'to Tower as ?foo=bar')
    def list(self, all_pages=False, **kwargs):
        """Return a list of objects.

        If one or more filters are provided through keyword arguments,
        filter the results accordingly.

        If no filters are provided, return all results.
        """
        # If the `all_pages` flag is set, then ignore any page that might
        # also be sent.
        if all_pages:
            kwargs.pop('page', None)

        # Get the response.
        debug.log('Getting records.', header='details')
        response = self.read(**kwargs)

        # Alter the "next" and "previous" to reflect simple integers,
        # rather than URLs, since this endpoint just takes integers.
        for key in ('next', 'previous'):
            if not response.get(key):
                continue
            match = re.search(r'page=(?P<num>[\d]+)', response[key])
            if match is None and key == 'previous':
                response[key] = 1
                continue
            response[key] = int(match.groupdict()['num'])

        # If we were asked for all pages, keep retrieving pages until we
        # have them all.
        if all_pages and response['next']:
            cursor = copy(response)
            while cursor['next']:
                cursor = self.list(**dict(kwargs, page=cursor['next']))
                response['results'] += cursor['results']

        # Done; return the response
        return response

    def _assoc(self, url_fragment, me, other):
        """Associate the `other` record with the `me` record."""

        # Get the endpoint for foreign records within this object.
        url = self.endpoint + '%d/%s/' % (me, url_fragment)

        # Attempt to determine whether the other record already exists here,
        # for the "changed" moniker.
        r = client.get(url, params={'id': other}).json()
        if r['count'] > 0:
            return {'changed': False}

        # Send a request adding the other record to this one.
        r = client.post(url, data={'associate': True, 'id': other})
        return {'changed': True}

    def _disassoc(self, url_fragment, me, other):
        """Disassociate the `other` record from the `me` record."""

        # Get the endpoint for foreign records within this object.
        url = self.endpoint + '%d/%s/' % (me, url_fragment)

        # Attempt to determine whether the other record already is absent, for
        # the "changed" moniker.
        r = client.get(url, params={'id': other}).json()
        if r['count'] == 0:
            return {'changed': False}

        # Send a request removing the foreign record from this one.
        r = client.post(url, data={'disassociate': True, 'id': other})
        return {'changed': True}

    def _lookup(self, fail_on_missing=False, fail_on_found=False,
                include_debug_header=True, **kwargs):
        """Attempt to perform a lookup that is expected to return a single
        result, and return the record.

        This method is a wrapper around `get` that strips out non-unique
        keys, and is used internally by `write` and `delete`.
        """
        # Determine which parameters we are using to determine
        # the appropriate field.
        read_params = {}
        for field_name in self.identity:
            if field_name in kwargs:
                read_params[field_name] = kwargs[field_name]

        # Special case of resources that only only addressable by id
        if 'id' in self.identity and len(self.identity) == 1:
            return {}

        # Sanity check: Do we have any parameters?
        # If not, then there's no way for us to do this read.
        if not read_params:
            raise exc.BadRequest('Cannot reliably determine which record '
                                 'to write. Include an ID or unique '
                                 'fields.')

        # Get the record to write.
        try:
            existing_data = self.get(include_debug_header=include_debug_header,
                                     **read_params)
            if fail_on_found:
                raise exc.Found('A record matching %s already exists, and '
                                'you requested a failure in that case.' %
                                read_params)
            return existing_data
        except exc.NotFound:
            if fail_on_missing:
                raise exc.NotFound('A record matching %s does not exist, and '
                                   'you requested a failure in that case.' %
                                   read_params)
            return {}


class MonitorableResource(ResourceMethods):
    """A resource that is able to be tied to a running task, such as a job
    or project, and thus able to be monitored.
    """
    abstract = True  # Not inherited.

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'unified_job_type'):
            self.unified_job_type = self.endpoint
        return super(MonitorableResource, self).__init__(*args, **kwargs)

    def status(self, pk, detail=False):
        """A stub method requesting the status of the resource."""
        raise NotImplementedError('This resource does not implement a status '
                                  'method, and must do so.')

    def last_job_data(self, pk=None, **kwargs):
        """
        Internal utility function for Unified Job Templates
        Returns data about the last job run off of that UJT
        """
        ujt = self.get(pk, include_debug_header=True, **kwargs)

        # Determine the appropriate inventory source update.
        if 'current_update' in ujt['related']:
            debug.log('A current job; retrieving it.', header='details')
            return client.get(ujt['related']['current_update'][7:]).json()
        elif ujt['related'].get('last_update', None):
            debug.log('No current job or update exists; retrieving the most '
                      'recent.', header='details')
            return client.get(ujt['related']['last_update'][7:]).json()
        else:
            raise exc.NotFound('No related jobs or updates exist.')

    def lookup_stdout(self, pk=None, start_line=None, end_line=None,
                      full=True):
        """
        Internal utility function to return standard out
        requires the pk of a unified job
        """
        stdout_url = '%s%d/stdout/' % (self.unified_job_type, pk)
        payload = {
            'format': 'json', 'content_encoding': 'base64',
            'content_format': 'ansi'}
        if start_line:
            payload['start_line'] = start_line
        if end_line:
            payload['end_line'] = end_line
        debug.log('Requesting a copy of job standard output', header='details')
        resp = client.get(stdout_url, params=payload).json()
        content = b64decode(resp['content'])

        return content

    @resources.command
    @click.option('--start-line', required=False, type=int,
                  help='Line at which to start printing the standard out.')
    @click.option('--end-line', required=False, type=int,
                  help='Line at which to end printing the standard out.')
    def stdout(self, pk, start_line=None, end_line=None, **kwargs):
        """
        Print out the standard out of a unified job to the command line.
        For Projects, print the standard out of most recent update.
        For Inventory Sources, print standard out of most recent sync.
        For Jobs, print the job's standard out.
        For Workflow Jobs, print a status table of its jobs.
        """
        # resource is Unified Job Template
        if self.unified_job_type != self.endpoint:
            unified_job = self.last_job_data(pk, **kwargs)
            pk = unified_job['id']
        # resource is Unified Job, but pk not given
        elif not pk:
            unified_job = self.get(**kwargs)
            pk = unified_job['id']

        content = self.lookup_stdout(pk, start_line, end_line)
        if len(content) > 0:
            click.echo(content, nl=1)

        return {"changed": False}

    @resources.command
    @click.option('--interval', default=0.2,
                  help='Polling interval to refresh content from Tower.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided, this command (not the job) will time out '
                       'after the given number of seconds.')
    def monitor(self, pk, parent_pk=None, timeout=None, interval=0.5,
                outfile=sys.stdout, **kwargs):
        """
        Stream the standard output from a
            job, project update, or inventory udpate.
        """
        # If we do not have the unified job info, infer it from parent
        if pk is None:
            pk = self.last_job_data(parent_pk, **kwargs)['id']
        job_endpoint = '%s%s/' % (self.unified_job_type, pk)

        # Pause until job is in running state
        self.wait(pk, exit_on=['running', 'successful'])

        # Loop initialization
        start = time.time()
        start_line = 0
        result = client.get(job_endpoint).json()

        click.echo('\033[0;91m------Starting Standard Out Stream------\033[0m',
                   nl=2, file=outfile)

        # Poll the Ansible Tower instance for status and content,
        # and print standard out to the out file
        while not result['failed'] and result['status'] != 'successful':

            result = client.get(job_endpoint).json()

            # Put the process to sleep briefly.
            time.sleep(interval)

            # Make request to get standard out
            content = self.lookup_stdout(pk, start_line, full=False)

            # In the first moments of running the job, the standard out
            # may not be available yet
            if not content.startswith("Waiting for results"):
                line_count = len(content.splitlines())
                start_line += line_count
                click.echo(content, nl=0)

            if timeout and time.time() - start > timeout:
                raise exc.Timeout('Monitoring aborted due to timeout.')

        # Special final line for closure with workflow jobs
        if self.endpoint == '/workflow_jobs/':
            click.echo(self.lookup_stdout(pk, start_line, full=True), nl=1)

        click.echo('\033[0;91m------End of Standard Out Stream--------\033[0m',
                   nl=2, file=outfile)

        if result['failed']:
            raise exc.JobFailure('Job failed.')

        # Return the job ID and other response data
        answer = OrderedDict((
            ('changed', True),
            ('id', pk),
        ))
        answer.update(result)
        # Make sure to return ID of resource and not update number
        # relevant for project creation and update
        if parent_pk:
            answer['id'] = parent_pk
        else:
            answer['id'] = pk
        return answer

    @resources.command
    @click.option('--min-interval',
                  default=1, help='The minimum interval to request an update '
                                  'from Tower.')
    @click.option('--max-interval',
                  default=30, help='The maximum interval to request an update '
                                   'from Tower.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided, this command (not the job) will time out '
                       'after the given number of seconds.')
    def wait(self, pk, parent_pk=None, min_interval=1, max_interval=30,
             timeout=None, outfile=sys.stdout, exit_on=['successful'],
             **kwargs):
        """
        Wait for a running job to finish.
        Blocks further input until the job completes (whether successfully or
        unsuccessfully) and a final status can be given.
        """
        # If we do not have the unified job info, infer it from parent
        if pk is None:
            pk = self.last_job_data(parent_pk, **kwargs)['id']
        job_endpoint = '%s%s/' % (self.unified_job_type, pk)

        dots = itertools.cycle([0, 1, 2, 3])
        longest_string = 0
        interval = min_interval
        start = time.time()

        # Poll the Ansible Tower instance for status, and print the status
        # to the outfile (usually standard out).
        #
        # Note that this is one of the few places where we use `secho`
        # even though we're in a function that might theoretically be imported
        # and run in Python.  This seems fine; outfile can be set to /dev/null
        # and very much the normal use for this method should be CLI
        # monitoring.
        result = client.get(job_endpoint).json()
        last_poll = time.time()
        timeout_check = 0
        while result['status'] not in exit_on:
            # If the job has failed, we want to raise an Exception for that
            # so we get a non-zero response.
            if result['failed']:
                if is_tty(outfile) and not settings.verbose:
                    secho('\r' + ' ' * longest_string + '\n', file=outfile)
                raise exc.JobFailure('Job failed.')

            # Sanity check: Have we officially timed out?
            # The timeout check is incremented below, so this is checking
            # to see if we were timed out as of the previous iteration.
            # If we are timed out, abort.
            if timeout and timeout_check - start > timeout:
                raise exc.Timeout('Monitoring aborted due to timeout.')

            # If the outfile is a TTY, print the current status.
            output = '\rCurrent status: %s%s' % (result['status'],
                                                 '.' * next(dots))
            if longest_string > len(output):
                output += ' ' * (longest_string - len(output))
            else:
                longest_string = len(output)
            if is_tty(outfile) and not settings.verbose:
                secho(output, nl=False, file=outfile)

            # Put the process to sleep briefly.
            time.sleep(0.2)

            # Sanity check: Have we reached our timeout?
            # If we're about to time out, then we need to ensure that we
            # do one last check.
            #
            # Note that the actual timeout will be performed at the start
            # of the **next** iteration, so there's a chance for the job's
            # completion to be noted first.
            timeout_check = time.time()
            if timeout and timeout_check - start > timeout:
                last_poll -= interval

            # If enough time has elapsed, ask the server for a new status.
            #
            # Note that this doesn't actually do a status check every single
            # time; we want the "spinner" to spin even if we're not actively
            # doing a check.
            #
            # So, what happens is that we are "counting down" (actually up)
            # to the next time that we intend to do a check, and once that
            # time hits, we do the status check as part of the normal cycle.
            if time.time() - last_poll > interval:
                result = client.get(job_endpoint).json()
                last_poll = time.time()
                interval = min(interval * 1.5, max_interval)

                # If the outfile is *not* a TTY, print a status update
                # when and only when we make an actual check to job status.
                if not is_tty(outfile) or settings.verbose:
                    click.echo('Current status: %s' % result['status'],
                               file=outfile)

            # Wipe out the previous output
            if is_tty(outfile) and not settings.verbose:
                secho('\r' + ' ' * longest_string, file=outfile, nl=False)
                secho('\r', file=outfile, nl=False)

        # Return the job ID and other response data
        answer = OrderedDict((
            ('changed', True),
            ('id', pk),
        ))
        answer.update(result)
        # Make sure to return ID of resource and not update number
        # relevant for project creation and update
        if parent_pk:
            answer['id'] = parent_pk
        else:
            answer['id'] = pk
        return answer


class ExeResource(MonitorableResource):
    """Executable resource - defines status and cancel methods"""
    abstract = True

    @resources.command
    @click.option('--detail', is_flag=True, default=False,
                  help='Print more detail.')
    def status(self, pk=None, detail=False, **kwargs):
        """Print the current job status. This is used to check a running job.
        You can look up the job with the same parameters used for a get
        request."""
        # Remove default values (anything where the value is None).
        self._pop_none(kwargs)

        # Search for the record if pk not given
        if not pk:
            job = self.get(include_debug_header=True, **kwargs)
        # Get the job from Ansible Tower if pk given
        else:
            debug.log('Asking for job status.', header='details')
            finished_endpoint = '%s%d/' % (self.endpoint, pk)
            job = client.get(finished_endpoint).json()

        # In most cases, we probably only want to know the status of the job
        # and the amount of time elapsed. However, if we were asked for
        # verbose information, provide it.
        if detail:
            return job

        # Print just the information we need.
        return {
            'elapsed': job['elapsed'],
            'failed': job['failed'],
            'status': job['status'],
        }

    @resources.command
    @click.option('--fail-if-not-running', is_flag=True, default=False,
                  help='Fail loudly if the job is not currently running.')
    def cancel(self, pk=None, fail_if_not_running=False, **kwargs):
        """Cancel a currently running job.

        Fails with a non-zero exit status if the job cannot be canceled.
        You must provide either a pk or parameters in the job's identity.
        """
        # Search for the record if pk not given
        if not pk:
            existing_data = self.get(**kwargs)
            pk = existing_data['id']

        cancel_endpoint = '%s%d/cancel/' % (self.endpoint, pk)
        # Attempt to cancel the job.
        try:
            client.post(cancel_endpoint)
            changed = True
        except exc.MethodNotAllowed:
            changed = False
            if fail_if_not_running:
                raise exc.TowerCLIError('Job not running.')

        # Return a success.
        return {'status': 'canceled', 'changed': changed}


class Resource(ResourceMethods):
    """This is the parent class for all standard resources."""
    abstract = True

    @resources.command
    @click.option('--fail-on-found', default=False,
                  show_default=True, type=bool, is_flag=True,
                  help='If used, return an error if a matching record already '
                       'exists.')
    @click.option('--force-on-exists', default=False,
                  show_default=True, type=bool, is_flag=True,
                  help='If used, if a match is found on unique fields, other '
                       'fields will be updated to the provided values. If '
                       'False, a match causes the request to be a no-op.')
    def create(self, fail_on_found=False, force_on_exists=False, **kwargs):
        """Create an object.

        Fields in the resource's `identity` tuple are used for a lookup;
        if a match is found, then no-op (unless `force_on_exists` is set) but
        do not fail (unless `fail_on_found` is set).
        """
        return super(Resource, self).write(
            create_on_missing=True,
            fail_on_found=fail_on_found, force_on_exists=force_on_exists,
            **kwargs
        )

    @resources.command(ignore_defaults=True)
    @click.option('--create-on-missing', default=False,
                  show_default=True, type=bool, is_flag=True,
                  help='If used, and if options rather than a primary key are '
                       'used to attempt to match a record, will create the '
                       'record if it does not exist. This is an alias to '
                       '`create --force-on-exists`.')
    def modify(self, pk=None, create_on_missing=False, **kwargs):
        """Modify an already existing object.

        Fields in the resource's `identity` tuple can be used in lieu of a
        primary key for a lookup; in such a case, only other fields are
        written.

        To modify unique fields, you must use the primary key for the lookup.
        """
        return self.write(pk, create_on_missing=create_on_missing,
                          force_on_exists=True, **kwargs)


class SurveyResource(Resource):
    """Contains utilities and commands common to "job template" models,
    which take extra_vars and have a survey_spec."""
    abstract = True

    def _survey_endpoint(self, pk):
        return '{0}{1}/survey_spec/'.format(self.endpoint, pk)

    def write(self, pk=None, **kwargs):
        survey_input = kwargs.pop('survey_spec', None)
        if kwargs.get('extra_vars', None):
            kwargs['extra_vars'] = parser.process_extra_vars(
                kwargs['extra_vars'])
        ret = super(SurveyResource, self).write(pk=pk, **kwargs)
        if survey_input is not None and ret.get('id', None):
            if not isinstance(survey_input, dict):
                survey_input = json.loads(survey_input.strip(' '))
            if survey_input == {}:
                debug.log('Deleting the survey_spec.', header='details')
                r = client.delete(self._survey_endpoint(ret['id']))
            else:
                debug.log('Saving the survey_spec.', header='details')
                r = client.post(self._survey_endpoint(ret['id']),
                                data=survey_input)
            if r.status_code == 200:
                ret['changed'] = True
            if survey_input and not ret['survey_enabled']:
                debug.log('For survey to take effect, set survey_enabled'
                          ' field to True.', header='warning')
        return ret

    @resources.command
    def survey(self, pk=None, **kwargs):
        """Get the survey_spec for the job template.
        To write a survey, use the modify command with the --survey-spec
        parameter."""
        job_template = self.get(pk=pk, **kwargs)
        if settings.format == 'human':
            settings.format = 'json'
        return client.get(self._survey_endpoint(job_template['id'])).json()
