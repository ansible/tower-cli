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

from tower_cli import models

from tests.compat import unittest


class FieldTests(unittest.TestCase):
    """A set of tests to establish that the base Field class works in the
    way we expect.
    """
    def test_dunder_lt(self):
        """Establish that the `__lt__` comparison method on fields works
        as expected.
        """
        f1 = models.Field()
        f2 = models.Field()
        self.assertTrue(f1 < f2)

    def test_dunder_gt(self):
        """Establish that the `__gt__` comparison method on fields works
        in the way we expect.
        """
        f1 = models.Field()
        f2 = models.Field()
        self.assertTrue(f2 > f1)

    def test_help_property_explicit(self):
        """Establish that an explicitly provided help text is preserved
        as the field's help.
        """
        f1 = models.Field(help_text='foo bar baz')
        self.assertEqual(f1.help, 'foo bar baz')

    def test_help_property_implicit(self):
        """Establish that a sane implicit help text is provided if none is
        specified.
        """
        f1 = models.Field()
        f1.name = 'f1'
        self.assertEqual(f1.help, 'The f1 field.')

    def test_flags_standard(self):
        """Establish that the `flags` property returns what I expect for a
        run-of-the-mill field.
        """
        f1 = models.Field()
        self.assertEqual(f1.flags, ['str'])

    def test_flags_unique_unfilterable(self):
        """Establish that the `flags` property successfully flags unfilterable
        and unique flags.
        """
        f1 = models.Field(unique=True, filterable=False)
        self.assertIn('unique', f1.flags)
        self.assertIn('not filterable', f1.flags)

    def test_flags_read_only(self):
        """Establish that the `flags` property successfully flags read-only
        flags.
        """
        f = models.Field(read_only=True)
        self.assertEqual(f.flags, ['str', 'read-only'])

    def test_flags_not_required(self):
        """Establish that the `flags` property successfully flags a
        not-required field.
        """
        f = models.Field(type=int, required=False)
        self.assertEqual(f.flags, ['int', 'not required'])

    def test_flags_type(self):
        """Establish that the flags property successfully shows the correct
        type name.
        """
        f = models.Field(type=bool)
        self.assertEqual(f.flags, ['bool'])
