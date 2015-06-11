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

from tower_cli.utils.data_structures import OrderedDict

from tests.compat import unittest


class OrderedDictTests(unittest.TestCase):
    """A set of tests to ensure that the OrderedDict subclass that
    tower-cli provides works as expected.
    """
    def test_dunder_repr(self):
        """Establish that the OrderedDict __repr__ method works in the
        way we expect.
        """
        d = OrderedDict()
        d['foo'] = 'spam'
        d['bar'] = 'eggs'
        self.assertEqual(repr(d), "{'foo': 'spam', 'bar': 'eggs'}")
