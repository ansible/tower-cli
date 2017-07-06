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

from six.moves import StringIO

from tower_cli import models, resources, exceptions as exc
from tower_cli.api import client
from tower_cli.utils import debug

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
        self.assertEqual(set(MyResource.commands), set(['foo', 'bar', 'list', 'delete', 'get']))

    def test_inherited_commands(self):
        """Establish that the stock commands are automatically present
        on classes inherited from Resource.
        """
        # Create the resource.
        class MyResource(models.Resource):
            endpoint = '/bogus/'

        # Establish it has the commands we expect.
        self.assertEqual(set(MyResource.commands),
                         set(['create', 'copy', 'modify', 'list', 'get',
                              'delete']))

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
        with mock.patch.object(models.base.BaseResource, 'write') as w:
            self.res.modify(name='foobar')
            w.assert_called_once_with(
                create_on_missing=False, force_on_exists=True,
                name='foobar', pk=None)

    def test_survey_create(self):
        with mock.patch.object(models.base.BaseResource, 'write') as w:
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
        with mock.patch.object(models.base.BaseResource, 'write') as w:
            w.return_value = {'id': 42, 'survey_enabled': True}
            with client.test_mode as t:
                t.register_json(
                    '/job_templates/42/survey_spec/', {},
                    method='DELETE'
                )
                self.res.modify(survey_spec={}, verbose=True)
                self.assertEqual(t.requests[0].method, 'DELETE')
