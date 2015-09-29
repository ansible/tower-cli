# Copyright 2015, Ansible, Inc.
# Alan Rominger <arominger@ansible.com>
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
        """Combine yaml with json with bare values, check that key:value
        pairs are preserved at the end."""
        adict = {"a": 1}
        bdict = {"b": 2}
        ayml = yaml.dump(adict)
        bjson = yaml.dump(bdict, default_flow_style=True)
        cyml = "5"
        result = parser.extra_vars_loader_wrapper([ayml, bjson, cyml])
        rdict = yaml.load(result)
        self.assertEqual(rdict['a'], 1)
        self.assertEqual(rdict['b'], 2)

    def test_combine_raw_params(self):
        """Given multiple files which all have raw parameters, make sure
        they are combined in the '_raw_params' key entry"""
        a_kv = "foo=bar\na"
        b_kv = "baz=fam\nb"
        result = parser.extra_vars_loader_wrapper([a_kv, b_kv])
        rdict = yaml.load(result)
        self.assertEqual(rdict['_raw_params'], "a b")

    def test_precedence(self):
        """Test that last value is the one that overwrites the others"""
        adict = {"a": 1}
        ayml = yaml.dump(adict)
        a2dict = {"a": 2}
        a2yml = yaml.dump(a2dict)
        result = parser.extra_vars_loader_wrapper([ayml, a2yml])
        rdict = yaml.load(result)
        self.assertEqual(rdict['a'], 2)

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
            parser.extra_vars_loader_wrapper(["a: b\nincorrect == brackets"])

        with self.assertRaises(exc.TowerCLIError):
            parser.extra_vars_loader_wrapper(["a: b\nincorrect = =brackets"])

    def test_handling_bad_data(self):
        """Check robustness of the parser functions in how it handles
        empty strings, null values, etc."""
        # Verrify that all parts of the computational chain can handle None
        return_dict = parser.parse_kv(None)
        self.assertEqual(return_dict, {})
        return_dict = parser.string_to_dict(None)
        self.assertEqual(return_dict, {})
        return_val = parser.file_or_yaml_split(None)
        self.assertEqual(return_val, None)

        # Verrify that all parts of computational chain can handle ""
        return_dict = parser.parse_kv("")
        self.assertEqual(return_dict, {})
        return_dict = parser.string_to_dict("")
        self.assertEqual(return_dict, {})
        return_val = parser.file_or_yaml_split("")
        self.assertEqual(return_val, "")

        # Check that the behavior is what we want if feeding it an int
        return_dict = parser.parse_kv(5)
        self.assertEqual(return_dict, {"_raw_params": "5"})
        return_dict = parser.parse_kv("foo=5")
        self.assertEqual(return_dict, {"foo": 5})


class TestSplitter_Gen(unittest.TestCase):
    """Set of strings paired with expected output is ran agains the parsing
    functions in this code in order to verrify desired accuracy.

    SPLIT_DATA is taken from Ansible tests located in:
        ansible/test/units/parsing/test_splitter.py
    within the ansible project source.
    """
    SPLIT_DATA = (
        (u'a',
            [u'a'],
            {u'_raw_params': u'a'}),
        (u'a=b',
            [u'a=b'],
            {u'a': u'b'}),
        (u'a="foo bar"',
            [u'a="foo bar"'],
            {u'a': u'foo bar'}),
        (u'"foo bar baz"',
            [u'"foo bar baz"'],
            {u'_raw_params': '"foo bar baz"'}),
        (u'foo bar baz',
            [u'foo', u'bar', u'baz'],
            {u'_raw_params': u'foo bar baz'}),
        (u'a=b c="foo bar"',
            [u'a=b', u'c="foo bar"'],
            {u'a': u'b', u'c': u'foo bar'}),
        (u'a="echo \\"hello world\\"" b=bar',
            [u'a="echo \\"hello world\\""', u'b=bar'],
            {u'a': u'echo "hello world"', u'b': u'bar'}),
        (u'a="multi\nline"',
            [u'a="multi\nline"'],
            {u'a': u'multi\nline'}),
        (u'a="blank\n\nline"',
            [u'a="blank\n\nline"'],
            {u'a': u'blank\n\nline'}),
        (u'a="blank\n\n\nlines"',
            [u'a="blank\n\n\nlines"'],
            {u'a': u'blank\n\n\nlines'}),
        (u'a="a long\nmessage\\\nabout a thing\n"',
            [u'a="a long\nmessage\\\nabout a thing\n"'],
            {u'a': u'a long\nmessage\\\nabout a thing\n'}),
        (u'a="multiline\nmessage1\\\n" b="multiline\nmessage2\\\n"',
            [u'a="multiline\nmessage1\\\n"', u'b="multiline\nmessage2\\\n"'],
            {u'a': 'multiline\nmessage1\\\n',
                   u'b': u'multiline\nmessage2\\\n'}),
        (u'a={{jinja}}',
            [u'a={{jinja}}'],
            {u'a': u'{{jinja}}'}),
        (u'a="{{ jinja }}"',  # edited for reduced scope
            [u'a={{ jinja }}'],
            {u'a': u'{{ jinja }}'}),
        (u'a="{{jinja}}"',
            [u'a="{{jinja}}"'],
            {u'a': u'{{jinja}}'}),
        (u'a="{{ jinja }}{{jinja2}}"',  # edited for reduced scope
            [u'a={{ jinja }}{{jinja2}}'],
            {u'a': u'{{ jinja }}{{jinja2}}'}),
        (u'a="{{ jinja }}{{jinja2}}"',
            [u'a="{{ jinja }}{{jinja2}}"'],
            {u'a': u'{{ jinja }}{{jinja2}}'}),
        (u'a={{jinja}} b={{jinja2}}',
            [u'a={{jinja}}', u'b={{jinja2}}'],
            {u'a': u'{{jinja}}', u'b': u'{{jinja2}}'}),
        (u'a="{{jinja}}\n" b="{{jinja2}}\n"',
            [u'a="{{jinja}}\n"', u'b="{{jinja2}}\n"'],
            {u'a': u'{{jinja}}\n', u'b': u'{{jinja2}}\n'}),
        )

    CUSTOM_DATA = [
        ("test=23 site=example.com", {"test": 23, "site": "example.com"}),
        ("2 site=example.com", {"_raw_params": '2', "site": "example.com"}),
        ('a=b\na', {'a': 'b', '_raw_params': 'a'}),
        ('var: value', {"var": "value"}),
        # key=value
        ('test=23 key="white space"', {"test": 23, "key": "white space"}),
        ("test=23 key='white space'", {"test": 23, "key": "white space"}),
        ('a="[1, 2, 3, 4, 5]" b="white space" ',
            {"a": [1, 2, 3, 4, 5], "b": 'white space'}),
        # YAML list
        ('a: [1, 2, 3, 4, 5]', {'a': [1, 2, 3, 4, 5]}),
        # JSON list
        ('{"a": [6,7,8,9]}', {'a': [6, 7, 8, 9]}),
        ("{'a': True, 'list_thing': [1, 2, 3, 4]}",
            {'a': True, 'list_thing': [1, 2, 3, 4]}),
        ("a: [1, 2, 3, 4, 5]\nb: 'white space' ",
            {"a": [1, 2, 3, 4, 5], "b": 'white space'}),
        ]

    # tests that combine two sources into one
    COMBINATION_DATA = [
        (["a: [1, 2, 3, 4, 5]", "b='white space'"],
            {"a": [1, 2, 3, 4, 5], "b": 'white space'}),
        (['{"a":3}', "b='white space'"],  # json
            {"a": 3, "b": 'white space'}),
    ]

    def test_parse_list(self):
        """Run tests on the data from Ansible core project."""
        for data in self.SPLIT_DATA:
            self.assertEqual(parser.string_to_dict(data[0]), data[2])

    def test_custom_parse_list(self):
        """Custom input-output scenario tests."""
        for data in self.CUSTOM_DATA:
            self.assertEqual(parser.string_to_dict(data[0]), data[1])

    def test_combination_parse_list(self):
        """Custom input-output scenario tests for 2 sources into one."""
        for data in self.COMBINATION_DATA:
            self.assertEqual(parser.load_extra_vars(data[0]), data[1])

    def test_unicode_dump(self):
        """Test that data is dumped without unicode character marking."""
        for data in self.COMBINATION_DATA:
            string_rep = parser.extra_vars_loader_wrapper(data[0])
            self.assertEqual(yaml.load(string_rep), data[1])
            assert "python/unicode" not in string_rep
            assert "\\n" not in string_rep
