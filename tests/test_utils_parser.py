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

import yaml

from tower_cli.utils import parser
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock


class ParserTests(unittest.TestCase):
    """A set of tests to establish that the parser methods read files and
    combine variables in the intended way.
    """
    def test_returns_input_text(self):
        """Give it only one file, and it should give it right back."""
        mock_text = "\n\nfoo:   baar\n\n\n"
        self.assertEqual(mock_text,
                         parser.extra_vars_loader_wrapper([mock_text]))

    def test_many_combinations(self):
        """Combine yaml with json with nonsense, check that values
        are preserved at the end."""
        adict = {"a": 1}
        bdict = {"b": 2}
        ayml = yaml.dump(adict)
        bjson = yaml.dump(bdict, default_flow_style=True)
        cyml = "5"
        result = parser.extra_vars_loader_wrapper([ayml, bjson, cyml])
        rdict = yaml.load(result)
        self.assertEqual(rdict['a'], 1)
        self.assertEqual(rdict['b'], 2)

    def test_read_from_file(self):
        """Give it some with '@' and test that it reads from the file"""
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.utils.parser.open', mock_open, create=True):
            manager = mock_open.return_value.__enter__.return_value
            manager.read.return_value = 'foo: bar'
            parser.extra_vars_loader_wrapper(["@fake_file1.yml"])
            parser.extra_vars_loader_wrapper(["@fake_file2.yml",
                                              "@fake_file3.yml"])

        # Ensure that "open" was triggered in test
        self.assertIn(mock.call("fake_file1.yml", 'r'), mock_open.mock_calls)
        self.assertIn(mock.call("fake_file2.yml", 'r'), mock_open.mock_calls)
        self.assertIn(mock.call("fake_file3.yml", 'r'), mock_open.mock_calls)

    def test_parse_error(self):
        """Given a yaml file with incorrect syntax, throw a warning"""
        with self.assertRaises(exc.TowerCLIError):
            parser.extra_vars_loader_wrapper(["a: b\nincorrect ]][ brackets"])
