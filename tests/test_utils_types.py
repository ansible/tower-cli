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

import os.path

from six.moves import StringIO

import click

from tower_cli.api import client
from tower_cli.utils import exceptions as exc, types
from tower_cli import get_resource

from tests.compat import unittest, mock


class FileTests(unittest.TestCase):
    """A set of tests establishing that the tower_cli subclass of click.File
    works in the way we expect.
    """
    def test_convert_file_object(self):
        """Establish that if we receive a file-like object to the convert
        method, that it is passed through without action.
        """
        sio = StringIO('The cat is trying to eat my goldfish crackers.')
        f = types.File('r')
        self.assertEqual(sio, f.convert(sio, 'myfile', None))

    def test_convert_expanduser(self):
        """Establish that if a filename is specified with a user home directory
        shortcut, that it is expanded appropriately.
        """
        f = types.File('f')
        with mock.patch.object(click.File, 'convert') as convert:
            f.convert('~/my_file.txt', 'myfile', None)
            convert.assert_called_with(os.path.expanduser('~/my_file.txt'),
                                       'myfile', None)

    def test_variables_file(self):
        """Establish that file with variables is opened in this type."""
        f = types.Variables()
        with mock.patch.object(click.File, 'convert') as convert:
            convert.return_value = "foo: bar"

            foo_converted = f.convert('@foobar.yml', 'myfile', None)

            convert.assert_called_once_with("foobar.yml", 'myfile', None)
            self.assertEqual(foo_converted, 'foo: bar')

    def test_variables_no_file(self):
        """Establish that plain variables are passed as-is."""
        f = types.Variables()
        foo_converted = f.convert('foo: barz', 'myfile', None)
        self.assertEqual(foo_converted, 'foo: barz')

    def test_variables_backup_option(self):
        """Establish that non-string input is protected against."""
        f = types.Variables()
        foo_converted = f.convert(54, 'myfile', None)
        self.assertEqual(foo_converted, 54)


class MappedChoiceTests(unittest.TestCase):
    """A set of tests to establish that the MappedChoice class works in the
    way that we expect.
    """
    def test_convert(self):
        """Establish that the convert method converts from the value
        provided to the user to the internal value, and calls the superclass
        method.
        """
        mc = types.MappedChoice({'foo': 'bar', 'spam': 'eggs'})
        self.assertEqual(mc.convert('bar', 'myopt', None), 'foo')
        self.assertEqual(mc.convert('eggs', 'myopt', None), 'spam')


class RelatedTests(unittest.TestCase):
    """A set of tests to establish that the Related class works in the way
    that we expect.
    """
    def setUp(self):
        self.related = types.Related('user')

    def test_convert_none(self):
        """Establish that attempting to convert None just returns None,
        as required by click.
        """
        self.assertEqual(self.related.convert(None, 'mything', None), None)

    def test_convert_null_no_record(self):
        """Establish 'null' passes through as-is"""
        self.assertEqual(self.related.convert('null', 'mything', None), 'null')

    def test_convert_int(self):
        """Establish that if we get an integer sent to the convert method,
        that it's passed through with no action taken on it (idempotency).
        """
        self.assertEqual(self.related.convert(42, 'mything', None), 42)

    def test_convert_number_as_string(self):
        """Establish that if we get a string value that looks like an integer,
        that we pass it through with no action taken (except to convert it
        to a true integer).
        """
        self.assertEqual(self.related.convert('42', 'mything', None), 42)

    def test_convert_by_lookup(self):
        """Establish that if we get a string value, we do a lookup against
        the resource's identity, and return back the ID that we get back
        in response.
        """
        p = click.Option(('name', '-n'))
        with client.test_mode as t:
            t.register_json('/users/?username=meagan', {
                'count': 1,
                'results': [{'id': 42}],
            })
            self.assertEqual(self.related.convert('meagan', p, None), 42)

    def test_convert_by_lookup_error(self):
        """Establish that if doing a foriegn key lookup fails, that we
        raise an appropriate exception.
        """
        p = click.Option(('name', '-n'))
        with client.test_mode as t:
            t.register_json('/users/?username=meagan', {}, status_code=404)
            with self.assertRaises(exc.RelatedError):
                self.related.convert('meagan', p, None)

    def test_convert_by_lookup_multi(self):
        """Establish that if doing a foreign key lookup returns multiple
        results, that we return a special error.
        """
        p = click.Option(('name', '-n'))
        with client.test_mode as t:
            t.register_json('/users/?username=meagan', {
                'count': 2,
                'results': [{'id': 42}, {'id': 84}],
            })
            with self.assertRaises(exc.MultipleRelatedError):
                self.assertEqual(self.related.convert('meagan', p, None), 42)

    def test_get_metavar(self):
        """Establish that the metavar ends up being what we expect,
        which is the resource name, but in uppercase.
        """
        self.assertEqual(self.related.get_metavar(None), 'USER')


class GeneralTests(unittest.TestCase):
    """A set of tests that are not specific to any type.
    """
    def test_type_name(self):
        """Establish that custom types are equipped with __name__ field and the
        upstream click.Choice's issue of having no __name__ field is properly
        dealt with.
        """
        names = [
            'ad_hoc',
            'credential',
            'group',
            'host',
            'inventory',
            'inventory_source',
            'job',
            'job_template',
            'organization',
            'project',
            'team',
            'user'
        ]
        for res_name in names:
            res = get_resource(res_name)
            self.assertEqual(type(res.fields), type([]))
            self.assertEqual(str(res.fields).startswith('[<Field:'), True)
