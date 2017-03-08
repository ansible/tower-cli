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

import json
import yaml

from six.moves import StringIO

import click

from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.conf import settings
from tower_cli.utils import debug, exceptions as exc

from tests.compat import unittest, mock


class ResourceMetaTests(unittest.TestCase):
    """A set of tests to establish that the ResourceMeta metaclass works
    in the way we expect.
    """
    def test_commands(self):
        """Establish that commands are appropriately classified within
        the resource, and that the stock commands are not present on a
        BaseResource subclass.
        """
        # Create the resource.
        class MyResource(models.BaseResource):
            endpoint = '/bogus/'

            @resources.command
            def foo(self):
                pass

            @resources.command
            def bar(self):
                pass

            def boring_method(self):
                pass

        # Establish that the commands are present on the resource where
        # we expect, and that the defined methods are still plain methods.
        #
        # Note: We can use something like types.FunctionType or
        # types.UnboundMethodType to test against directly, but using a
        # regular method is preferable because of differences between
        # the type internals in Python 2 vs. Python 3.
        #
        # By just getting the desirable control type from another method
        # on the resource, we are ensuring that it "just matches" regardless
        # of which version of Python is in use.
        self.assertIsInstance(MyResource.foo, type(MyResource.boring_method))
        self.assertIsInstance(MyResource.bar, type(MyResource.boring_method))
        self.assertEqual(set(MyResource.commands), set(['foo', 'bar']))

    def test_inherited_commands(self):
        """Establish that the stock commands are automatically present
        on classes inherited from Resource.
        """
        # Create the resource.
        class MyResource(models.Resource):
            endpoint = '/bogus/'

        # Establish it has the commands we expect.
        self.assertEqual(set(MyResource.commands),
                         set(['create', 'modify', 'list', 'get', 'delete']))

    def test_subclassed_commands(self):
        """Establish that commands overridden in subclasses retain their
        superclass implementation options.
        """
        # Create the subclass resource, overriding a superclass command.
        class MyResource(models.Resource):
            endpoint = '/bogus/'

            @resources.command
            def list(self, **kwargs):
                return super(MyResource, self).list(**kwargs)

        # Establish that it has one of the options added to the
        # superclass list command.
        self.assertTrue(any([i.name == 'query'
                            for i in MyResource.list.__click_params__]))

    def test_fields(self):
        """Establish that fields are appropriately classified within
        the resource.
        """
        # Create the resource.
        class MyResource(models.Resource):
            endpoint = '/bogus/'

            foo = models.Field(unique=True)
            bar = models.Field()

        # Establish that our fields lists are the length we expect.
        self.assertEqual(len(MyResource.fields), 2)
        self.assertEqual(len(MyResource.unique_fields), 1)

        # Establish that the fields are present in fields.
        self.assertEqual(MyResource.fields[0].name, 'foo')
        self.assertEqual(MyResource.fields[1].name, 'bar')
        self.assertEqual(MyResource.unique_fields, set(['foo']))

    def test_error_no_endpoint(self):
        """Establish that Resource subclasses are required to have
        an endpoint, and attempting to create one that lacks an endpoint
        raises TypeError.
        """
        with self.assertRaises(TypeError):
            class MyResource(models.Resource):
                pass

    def test_endpoint_normalization(self):
        """Establish that the endpoints have leading and trailing slashes
        added if they are not present on a resource.
        """
        class MyResource(models.Resource):
            endpoint = 'foo'
        self.assertEqual(MyResource.endpoint, '/foo/')


class SubcommandTests(unittest.TestCase):
    """A set of tests for establishing that the Subcommand class created
    on the basis of a Reosurce class works in the way we expect.
    """
    def setUp(self):
        """Install a resource instance sufficient for testing common
        things with subcommands.
        """
        class BasicResource(models.Resource):
            endpoint = '/basic/'
            name = models.Field(unique=True)
        self.resource = BasicResource()
        self.command = self.resource.as_command()

    def test_command_instance(self):
        """Establish that the command based on a resource is, in fact, a
        click MultiCommand.
        """
        # Assert that it is a click command, and that it has the commands
        # available on the resource.
        self.assertIsInstance(self.command, click.MultiCommand)

    def test_list_commands(self):
        """Establish that the `list_commands` method for the command
        corresponds to the commands available on the resource.
        """
        self.assertEqual(set(self.resource.commands),
                         set(self.command.list_commands(None)))

    def test_get_command(self):
        """Establish that the `get_command` method returns the appropriate
        resource method wrapped as a click command.
        """
        list_command = self.command.get_command(None, 'list')

        # Ensure that this is a click command.
        self.assertIsInstance(list_command, click.core.Command)

        # Ensure that this command has an option corresponding to the
        # "name" unique field.
        self.assertEqual(list_command.params[0].name, 'name')
        self.assertIn('--name', list_command.params[0].opts)

    def test_get_command_error(self):
        """Establish that if `get_command` is called against a command that
        does not actually exist on the resource, that null value is returned.
        """
        self.assertEqual(self.command.get_command(None, 'bogus'), None)

    def test_command_with_pk(self):
        """Establish that the `get_command` method appropriately adds a
        primary key argument if the method has a "pk" positional argument.
        """
        # Create a resource with an appropriate command.
        class PKResource(models.BaseResource):
            endpoint = '/pkr/'

            @resources.command
            def my_method(self, pk):
                pass

        # Get the command version of my_method.
        my_method = PKResource().as_command().get_command(None, 'my_method')

        # Establish that the `my_method` command does, in fact, have a PK
        # click argument attached.
        self.assertEqual(my_method.params[-1].name, 'pk')

    def test_use_fields_as_options_false(self):
        """Establish that the `use_fields_as_options` attribute is honored
        if set to False.
        """
        # Create a resource with a command that doesn't expect its
        # fields to become options.
        class NoOptResource(models.BaseResource):
            endpoint = '/nor/'

            f1 = models.Field()
            f2 = models.Field()

            @resources.command(use_fields_as_options=False)
            def noopt(self):
                pass

        # Make the resource into a command, and get the noopt subcommand.
        noopt = NoOptResource().as_command().get_command(None, 'noopt')

        # Establish that the noopt command does NOT have fields as options.
        self.assertFalse(any([o.name == 'f1' for o in noopt.params]))
        self.assertFalse(any([o.name == 'f2' for o in noopt.params]))

    def test_use_fields_as_options_enumerated(self):
        """Establish that the `use_fields_as_options` attribute is honored
        if set to a tuple containing a subset of fields.
        """
        # Create a resource with a command that doesn't expect its
        # fields to become options.
        class NoOptResource(models.BaseResource):
            endpoint = '/nor/'

            f1 = models.Field()
            f2 = models.Field()

            @resources.command(use_fields_as_options=('f2',))
            def noopt(self):
                pass

        # Make the resource into a command, and get the noopt subcommand.
        noopt = NoOptResource().as_command().get_command(None, 'noopt')

        # Establish that the noopt command does NOT have fields as options.
        self.assertFalse(any([o.name == 'f1' for o in noopt.params]))
        self.assertTrue(any([o.name == 'f2' for o in noopt.params]))

    def test_fields_not_options(self):
        """Establish that a field which is not an option is not made into
        an option for commands.
        """
        # Create a resource with a field that is an option and another
        # field that isn't.
        class NoOptionResource(models.Resource):
            endpoint = '/nor/'

            yes = models.Field()
            no = models.Field(is_option=False)

        # Make the resource into a command, and get a reasonably-arbitrary
        # subcommand.
        cmd = NoOptionResource().as_command().get_command(None, 'list')

        # Establish that "yes" is an option on the command and "no" is not.
        self.assertTrue(any([o.name == 'yes' for o in cmd.params]))
        self.assertFalse(any([o.name == 'no' for o in cmd.params]))

    def test_field_explicit_key(self):
        """Establish that if a field is given an explicit key, that they
        key is used for the field name instead of the implicit name.
        """
        # Create a resource with a field that has an explicit key.
        class ExplicitKeyResource(models.Resource):
            endpoint = '/ekr/'

            option_name = models.Field('internal_name')

        # Make the resource into a command, and get a reasonably-arbitrary
        # subcommand.
        cmd = ExplicitKeyResource().as_command().get_command(None, 'get')

        # Establish that the field has an option of --option-name, and
        # a name of internal_name.
        opt = cmd.params[0]
        self.assertEqual(opt.name, 'internal_name')
        self.assertEqual(opt.opts, ['--option-name'])

    def test_docstring_replacement_an(self):
        """Establish that for resources with names beginning with vowels,
        that the automatic docstring replacement is gramatically correct.
        """
        # Create a resource with an approriate name.
        class Oreo(models.Resource):
            resource_name = 'Oreo cookie'   # COOOOOOKIES!!!!
            endpoint = '/oreo/'

        # Get the Oreo resource's create method.
        create = Oreo().as_command().get_command(None, 'create')
        self.assertIn('Create an Oreo cookie', create.help)

    def test_docstring_replacement_y(self):
        """Establish that for resources with names ending in y, that plural
        replacement is correct.
        """
        # Create a resource with an approriate name.
        class Oreo(models.Resource):
            resource_name = 'telephony'
            endpoint = '/telephonies/'

        # Get the Oreo resource's create method.
        create = Oreo().as_command().get_command(None, 'list')
        self.assertIn('list of telephonies', create.help)

    def test_echo_method(self):
        """Establish that the _echo_method subcommand class works in the
        way we expect.
        """
        func = self.command._echo_method(lambda: {'foo': 'bar'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='json'):
                func()
            secho.assert_called_once_with(json.dumps({'foo': 'bar'}, indent=2))

    def test_echo_method_changed_false(self):
        """Establish that the _echo_method subcommand decorator works
        in the way we expect if we get an unchanged designation.
        """
        func = self.command._echo_method(lambda: {'changed': False})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='json', color=True):
                func()
            answer = json.dumps({'changed': False}, indent=2)
            secho.assert_called_once_with(answer, fg='green')

    def test_echo_method_changed_true(self):
        """Establish that the _echo_method subcommand decorator works
        in the way we expect if we get an changed designation.
        """
        func = self.command._echo_method(lambda: {'changed': True})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='json', color=True):
                func()
            answer = json.dumps({'changed': True}, indent=2)
            secho.assert_called_once_with(answer, fg='yellow')

    def test_echo_method_yaml_formatted(self):
        """Establish that the `_echo_method` properly returns YAML formatting
        when it gets back a list of objects.
        """
        func = self.command._echo_method(lambda: {'foo': 'bar'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='yaml'):
                func()
            secho.assert_called_once_with(yaml.safe_dump({'foo': 'bar'},
                                          indent=2,
                                          allow_unicode=True,
                                          default_flow_style=False))

    def test_echo_method_human_formatted(self):
        """Establish that the `_echo_method` properly returns human formatting
        when it gets back a list of objects.
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
            {'id': 2, 'name': 'Austin, TX'},
        ]})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('1 Durham, NC', output)
        self.assertIn('2 Austin, TX', output)

    def test_echo_method_human_formatted_changed(self):
        """Establish that if there is a change and no id is returned,
        we print a generic OK message.
        """
        func = self.command._echo_method(lambda: {'changed': False})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertEqual(output, 'OK. (changed: false)')

    def test_echo_method_human_formatted_no_records(self):
        """Establish that if there are no records sent to the human formatter,
        that it prints a terse message to that effect.
        """
        func = self.command._echo_method(lambda: {'results': []})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertEqual(output, 'No records found.')

    def test_echo_method_human_formatted_single_result(self):
        """Establish that a single result sent to the human formatter
        shows a table with a single row as expected.
        """
        f = self.command._echo_method(lambda: {'id': 1, 'name': 'Durham, NC'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                f()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('1 Durham, NC', output)

    def test_echo_method_human_boolean_formatting(self):
        """Establish that booleans are formatted right-aligned, lower-cased
        in human output.
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
            {'id': 2, 'name': True},
        ]})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('1 Durham, NC', output)
        self.assertIn('2       true', output)

    def test_echo_method_human_pagination(self):
        """Establish that pagination works in human formatting, and it
        prints the way we expect.
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
            {'id': 2, 'name': True},
        ], 'next': 3, 'count': 10, 'previous': 1})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('(Page 2 of 5.)', output)

    def test_echo_method_human_pagination_last_page(self):
        """Establish that pagination works in human formatting, and it
        prints the way we expect on the final page..
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
        ], 'next': None, 'count': 3, 'previous': 1})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('(Page 2 of 2.)', output)

    def test_echo_method_human_custom_output(self):
        """Establish that a custom dictionary with no ID is made into a
        table and printed as expected.
        """
        func = self.command._echo_method(lambda:
                                         {'foo': 'bar', 'spam': 'eggs'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('foo', output)
        self.assertIn('spam', output)
        self.assertIn('bar', output)
        self.assertIn('eggs', output)


class ResourceTests(unittest.TestCase):
    """A set of tests to establish that the Resource class works in the
    way that we expect.
    """
    def setUp(self):
        # Create a resource class that can be used across this particular
        # suite.
        class FooResource(models.Resource):
            endpoint = '/foo/'
            name = models.Field(unique=True)
            description = models.Field(required=False)
        self.res = FooResource()

    def test_get(self):
        """Establish that the Resource class' `get` method works in the
        way that we expect.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/', {'id': 42, 'description': 'bar',
                                         'name': 'foo'})
            result = self.res.get(42)
            self.assertEqual(result['id'], 42)
            self.assertEqual(result['name'], 'foo')

    def test_list_no_kwargs(self):
        """Establish that the Resource class' `list` method correctly
        requests the resource and parses out a list of results.
        """
        with client.test_mode as t:
            t.register_json('/foo/', {'count': 2, 'results': [
                {'id': 1, 'name': 'foo', 'description': 'bar'},
                {'id': 2, 'name': 'spam', 'description': 'eggs'},
            ], 'next': None, 'previous': None})
            result = self.res.list()
            self.assertEqual(t.requests[0].url,
                             'https://20.12.4.21/api/v1/foo/')
            self.assertEqual(result['count'], 2)
            self.assertEqual(result['results'][0]['id'], 1)

    def test_list_all_pages(self):
        """Establish that the Resource class' `list` method correctly
        accepts the --all-pages flag and checks follow-up pages.
        """
        with client.test_mode as t:
            # Register the first, second, and third page.
            t.register_json('/foo/', {'count': 3, 'results': [
                {'id': 1, 'name': 'foo', 'description': 'bar'},
            ], 'next': '/foo/?page=2', 'previous': None})
            t.register_json('/foo/?page=2', {'count': 3, 'results': [
                {'id': 2, 'name': 'spam', 'description': 'eggs'},
            ], 'next': '/foo/?page=3', 'previous': None})
            t.register_json('/foo/?page=3', {'count': 3, 'results': [
                {'id': 3, 'name': 'bacon', 'description': 'cheese'},
            ], 'next': None, 'previous': None})

            # Get the list
            result = self.res.list(all_pages=True)

            # Assert that there are three results, and three requests.
            self.assertEqual(len(t.requests), 3)
            self.assertEqual(len(result['results']), 3)

    def test_list_with_page_1_special_case(self):
        """Establish that the list function works even if the server gives
        /foo/ as the relative link for page 1.
        """
        with client.test_mode as t:
            # Register the 2nd page in order to test this.
            t.register_json('/foo/?page=2', {'count': 2, 'results': [
                {'id': 2, 'name': 'spam', 'description': 'eggs'},
            ], 'next': None, 'previous': '/foo/'})

            # Get the list
            result = self.res.list(page=2)

            # Check that the function knows that /foo/ is page 1
            self.assertEqual(result['previous'], 1)

    def test_list_custom_kwargs(self):
        """Establish that if we pass custom keyword arguments to list, that
        they are included in the final request.
        """
        with client.test_mode as t:
            t.register_json('/foo/?bar=baz', {'count': 0, 'results': [],
                                              'next': None, 'previous': None})
            self.res.list(query=[('bar', 'baz')])
            self.assertTrue(t.requests[0].url.endswith('bar=baz'))

    def test_list_duplicate_kwarg(self):
        """Establish that if we attempt to query on the same field twice,
        that we get an error.
        """
        with client.test_mode as t:
            with self.assertRaises(exc.BadRequest):
                self.res.list(name='Batman', query=[('name', 'Robin')])
            self.assertEqual(len(t.requests), 0)

    def test_get_unexpected_zero_results(self):
        """Establish that if a read method gets 0 results when it should have
        gotten one or more, that it raises NotFound.
        """
        with client.test_mode as t:
            t.register_json('/foo/?name=spam', {'count': 0, 'results': []})
            with self.assertRaises(exc.NotFound):
                self.res.get(name='spam')

    def test_get_no_debug_header(self):
        """Establish that if get is called with include_debug_header=False,
        no debug header is issued.
        """
        with mock.patch.object(type(self.res), 'read') as read:
            with mock.patch.object(debug, 'log') as dlog:
                read.return_value = {'results': [True]}
                result = self.res.get(42, include_debug_header=False)
                self.assertEqual(dlog.call_count, 0)
            self.assertTrue(result)

    def test_get_unexpected_multiple_results(self):
        """Establish that if a read method gets more than one result when
        it should have gotten one and exactly one, that it raises
        MultipleResults.
        """
        # Register the response to the request URL.
        # Note that this response should represent bad data, since name is
        # generally unique within Tower.  This doesn't matter for the purpose
        # of this test; what's important is that if we expected one and exactly
        # one result and we get two or more, that we complain in an expected
        # (and later, handled) way.
        with client.test_mode as t:
            t.register_json('/foo/?name=spam', {'count': 2, 'results': [
                {'id': 1, 'name': 'spam'},
                {'id': 2, 'name': 'spam'},
            ], 'next': None, 'previous': None})
            with self.assertRaises(exc.MultipleResults):
                self.res.get(name='spam')

    def test_list_with_none_kwargs(self):
        """Establish that if `list` is called with keyword arguments with
        None values, that these are ignored.

        This is to ensure that click's eagerness to send None values doesn't
        cause problems.
        """
        # Register the request and make the call.
        with client.test_mode as t:
            t.register_json('/foo/?name=foo', {'count': 1, 'results': [
                {'id': 1, 'name': 'foo', 'description': 'bar'},
            ], 'next': None, 'previous': None})
            self.res.list(name='foo', description=None)
            self.assertEqual(len(t.requests), 1)

            # Ensure that there are no other query param arguments other
            # than `?name=foo` in the request URL.
            self.assertNotIn('&', t.requests[0].url)
            self.assertTrue(t.requests[0].url.endswith('?name=foo'))

    def test_list_with_pagination(self):
        """Establish that the `list` method returns pages as integers
        if it is given pages at all.
        """
        with client.test_mode as t:
            t.register_json('/foo/', {'count': 10, 'results': [
                {'id': 1, 'name': 'bar'},
            ], 'next': '/api/v1/foo/?page=2', 'previous': None})
            result = self.res.list()
            self.assertEqual(result['next'], 2)

    def test_reading_with_file(self):
        """Establish that if we get a file-like object, that it is
        appropriately read.
        """
        # Note: This is primarily for a case of longer input that belongs
        # in files (such as SSH RSA/DSA private keys), but in this case we're
        # using something trivial; we need only provide a proof of concept
        # to test against.
        sio = StringIO('bar')
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 0, 'results': [],
                                               'next': None, 'previous': None})
            self.res.list(name=sio)
            self.assertTrue(t.requests[0].url.endswith('?name=bar'))

    def test_create(self):
        """Establish that a standard create call works in the way that
        we expect.
        """
        with client.test_mode as t:
            # `create` will attempt to see if the record already exists;
            # mock this to state that it does not.
            t.register_json('/foo/?name=bar', {'count': 0, 'results': [],
                                               'next': None, 'previous': None})
            t.register_json('/foo/', {'changed': True, 'id': 42},
                            method='POST')
            self.res.create(name='bar')
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'POST')

    def test_create_already_existing(self):
        """Establish that if we attempt to create a record that already exists,
        that no action ends up being taken.
        """
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 1, 'results': [
                {'id': 42, 'name': 'bar'},
            ], 'next': None, 'previous': None})
            result = self.res.create(name='bar')
            self.assertEqual(len(t.requests), 1)
            self.assertFalse(result['changed'])

    def test_create_missing_required_fields(self):
        """Establish that if we attempt to create a record and don't specify
        all required fields, that we raise BadRequest.
        """
        # Create a resource with a required field that isn't the name
        # field.
        class BarResource(models.Resource):
            endpoint = '/bar/'
            name = models.Field(unique=True)
            required = models.Field()
        res = BarResource()

        # Attempt to write the resource and prove that it fails.
        with client.test_mode as t:
            t.register_json('/bar/?name=foo', {'count': 0, 'results': [],
                                               'next': None, 'previous': None})
            with self.assertRaises(exc.BadRequest):
                res.create(name='foo')

    def test_modify(self):
        """Establish that the modify method works in the way we expect,
        given a normal circumstance.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/', {'id': 42, 'name': 'bar',
                                         'description': 'baz'})
            t.register_json('/foo/42/',
                            {'changed': True, 'id': 42}, method='PATCH')
            result = self.res.modify(42, description='spam')
            self.assertTrue(result['changed'])
            self.assertEqual(t.requests[1].body, '{"description": "spam"}')

    def test_modify_no_changes(self):
        """Establish that the modify method does not actually attempt
        a modification if there are no changes.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/', {'id': 42, 'name': 'bar',
                                         'description': 'baz'})
            result = self.res.modify(42, description='baz')
            self.assertFalse(result['changed'])
            self.assertEqual(len(t.requests), 1)

    def test_modify_ignore_kwargs_none(self):
        """Establish that we ignore keyword arguments set to None when
        performing writes.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/', {'id': 42, 'name': 'bar',
                                         'description': 'baz'})
            result = self.res.modify(42, name=None, description='baz')
            self.assertFalse(result['changed'])
            self.assertEqual(len(t.requests), 1)
            self.assertNotIn('name', t.requests[0].url)

    def test_write_file_like_object(self):
        """Establish that our write method, if it gets a file-like object,
        correctly reads it and uses the file's value as what it sends.
        """
        sio = StringIO('bar')
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 1, 'results': [
                {'id': 42, 'name': 'bar', 'description': 'baz'},
            ], 'next': None, 'previous': None})
            result = self.res.modify(name=sio, description='baz')
            self.assertFalse(result['changed'])
            self.assertIn('name=bar', t.requests[0].url)

    def test_write_with_null_field(self):
        """Establish that a resource with 'null' field is written."""
        with client.test_mode as t:
            t.register_json('/foo/42/', {'id': 42, 'name': 'bar',
                                         'description': 'baz'}, method='GET')
            t.register_json('/foo/42/', {'name': 'bar', 'id': 42,
                                         'inventory': 'null'}, method='PATCH')
            self.res.write(42, inventory='null')
            self.assertEqual(json.loads(t.requests[1].body)['inventory'], None)

    def test_delete_with_pk(self):
        """Establish that calling `delete` and providing a primary key
        works in the way that we expect.
        """
        with client.test_mode as t:
            t.register('/foo/42/', '', method='DELETE')
            result = self.res.delete(42)
        self.assertTrue(result['changed'])

    def test_delete_without_pk(self):
        """Establish that calling `delete` with keyword arguments works
        in the way that we expect.
        """
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 1, 'results': [
                {'id': 42, 'name': 'bar', 'description': 'baz'},
            ], 'next': None, 'previous': None})
            t.register('/foo/42/', '', method='DELETE')
            result = self.res.delete(name='bar')
            self.assertEqual(len(t.requests), 2)
            self.assertTrue(t.requests[1].url.endswith('/foo/42/'))
        self.assertTrue(result['changed'])

    def test_delete_with_pk_already_missing(self):
        """Establish that calling `delete` on a record that does not exist
        returns back an unchanged response.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/', '', method='DELETE', status_code=404)
            result = self.res.delete(42)
        self.assertFalse(result['changed'])

    def test_delete_with_pk_already_missing_exc(self):
        """Establish that calling `delete` on a record that does not
        exist raises an exception if requested.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/', '', method='DELETE', status_code=404)
            with self.assertRaises(exc.NotFound):
                self.res.delete(42, fail_on_missing=True)

    def test_delete_without_pk_already_missing(self):
        """Establish that calling `delete` on a record without a primary
        key correctly sends back an unchanged response.
        """
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 0, 'results': []})
            result = self.res.delete(name='bar')
            self.assertFalse(result['changed'])

    def test_delete_without_pk_already_missing_exc(self):
        """Establish that calling `delete` on a record without a primary
        key correctly sends back an unchanged response.
        """
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 0, 'results': []})
            with self.assertRaises(exc.NotFound):
                self.res.delete(name='bar', fail_on_missing=True)

    def test_assoc_already_present(self):
        """Establish that the _assoc method returns an unchanged status
        message if it attempts to associate two records that are already
        associated.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/bar/?id=84', {'count': 1, 'results': [
                {'id': 84},
            ], 'next': None, 'previous': None})
            result = self.res._assoc('bar', 42, 84)
            self.assertFalse(result['changed'])

    def test_assoc_not_already_present(self):
        """Establish that the _assoc method returns an changed status
        message and associates objects if appropriate.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/bar/?id=84', {'count': 0, 'results': []})
            t.register_json('/foo/42/bar/', {}, method='POST')
            result = self.res._assoc('bar', 42, 84)
            self.assertEqual(json.loads(t.requests[1].body),
                             {'associate': True, 'id': 84})
            self.assertTrue(result['changed'])

    def test_disassoc_not_already_present(self):
        """Establish that the _disassoc method returns an unchanged status
        message if it attempts to associate two records that are not
        associated.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/bar/?id=84', {'count': 0, 'results': []})
            result = self.res._disassoc('bar', 42, 84)
            self.assertFalse(result['changed'])

    def test_disassoc_already_present(self):
        """Establish that the _assoc method returns an changed status
        message and associates objects if appropriate.
        """
        with client.test_mode as t:
            t.register_json('/foo/42/bar/?id=84', {'count': 1, 'results': [
                {'id': 84},
            ], 'next': None, 'previous': None})
            t.register_json('/foo/42/bar/', {}, method='POST')
            result = self.res._disassoc('bar', 42, 84)
            self.assertEqual(json.loads(t.requests[1].body),
                             {'disassociate': True, 'id': 84})
            self.assertTrue(result['changed'])

    def test_lookup_with_unique_field_not_present(self):
        """Establish that a if _lookup is invoked without any unique
        field specified, that BadRequest is raised.
        """
        with client.test_mode:
            with self.assertRaises(exc.BadRequest):
                self.res._lookup(description='abcd')

    def test_lookup_errant_found(self):
        """Establish that if _lookup is invoked and finds a record when it
        should not, that an appropriate exception is raised.
        """
        with client.test_mode as t:
            t.register_json('/foo/?name=bar', {'count': 1, 'results': [
                {'id': 42, 'name': 'bar'},
            ], 'next': None, 'previous': None})
            with self.assertRaises(exc.Found):
                self.res._lookup(name='bar', fail_on_found=True)


class MonitorableResourcesTests(unittest.TestCase):
    """Estblaish that the MonitorableResource abstract class works in the
    way that we expect.
    """
    def test_status_not_implemented(self):
        """Establish that the abstract MonitorableResource's status
        method raises NotImplementedError.
        """
        with self.assertRaises(NotImplementedError):
            models.MonitorableResource().status(None)


class SurveyResourceTests(unittest.TestCase):
    """Test methods specific to survey models."""
    def setUp(self):
        self.res = models.SurveyResource()
        self.res.endpoint = '/job_templates/'

    def test_survey_no_op(self):
        with mock.patch.object(models.base.ResourceMethods, 'write') as w:
            self.res.modify(name='foobar')
            w.assert_called_once_with(
                create_on_missing=False, force_on_exists=True,
                name='foobar', pk=None)

    def test_survey_create(self):
        with mock.patch.object(models.base.ResourceMethods, 'write') as w:
            w.return_value = {'id': 42, 'survey_enabled': True}
            survey_data = {'foobar': 'foo'}
            with client.test_mode as t:
                t.register_json(
                    '/job_templates/42/survey_spec/', {},
                    method='POST'
                )
                self.res.modify(survey_spec=survey_data, verbose=True)
                self.assertEqual(t.requests[0].body, json.dumps(survey_data))

    def test_survey_delete(self):
        with mock.patch.object(models.base.ResourceMethods, 'write') as w:
            w.return_value = {'id': 42, 'survey_enabled': True}
            with client.test_mode as t:
                t.register_json(
                    '/job_templates/42/survey_spec/', {},
                    method='DELETE'
                )
                self.res.modify(survey_spec={}, verbose=True)
                self.assertEqual(t.requests[0].method, 'DELETE')
