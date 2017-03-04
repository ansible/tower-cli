# -*- coding: utf-8 -*-
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
from tower_cli.utils.data_structures import OrderedDict

from tests.compat import unittest, mock


class ParserTests(unittest.TestCase):
    """A set of tests to establish that the parser methods read files and
    combine variables in the intended way.
    """

    def test_many_combinations(self):
        """Combine yaml with json with bare values, check that key:value
        pairs are preserved at the end."""
        adict = {"a": 1}
        bdict = {"b": 2}
        ayml = yaml.dump(adict)
        bjson = yaml.dump(bdict, default_flow_style=True)
        cyml = "c: 5"
        result = parser.process_extra_vars([ayml, bjson, cyml])
        rdict = yaml.load(result)
        self.assertEqual(rdict['a'], 1)
        self.assertEqual(rdict['b'], 2)

        yaml_w_comment = "a: b\n# comment\nc: d"
        self.assertEqual(
            parser.process_extra_vars([yaml_w_comment], force_json=False),
            yaml_w_comment
        )
        yaml_w_comment = '{a: b,\n# comment\nc: d}'
        json_text = '{"z":"p"}'
        self.assertDictContainsSubset(
            yaml.load(yaml_w_comment),
            yaml.load(parser.process_extra_vars(
                [yaml_w_comment, json_text], force_json=False
            ))
        )
        # Test that it correctly combines a diverse set of YAML
        yml1 = "a: 1\n# a comment on second line \nb: 2"
        yml2 = "c: 3"
        self.assertEqual(
            yaml.load(parser.process_extra_vars(
                [yml1, yml2], force_json=False)),
            {'a': 1, 'b': 2, 'c': 3}
        )
        # make sure it combined them into valid yaml
        self.assertFalse("{" in parser.process_extra_vars(
            [yml1, yml2], force_json=False))

    def test_precedence(self):
        """Test that last value is the one that overwrites the others"""
        adict = {"a": 1}
        ayml = yaml.dump(adict)
        a2dict = {"a": 2}
        a2yml = yaml.dump(a2dict)
        result = parser.process_extra_vars([ayml, a2yml])
        rdict = yaml.load(result)
        self.assertEqual(rdict['a'], 2)

    def test_read_from_file(self):
        """Give it some with '@' and test that it reads from the file"""
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.utils.parser.open', mock_open, create=True):
            manager = mock_open.return_value.__enter__.return_value
            manager.read.return_value = 'foo: bar'
            parser.process_extra_vars(["@fake_file1.yml"])
            parser.process_extra_vars(["@fake_file2.yml",
                                       "@fake_file3.yml"])

        # Ensure that "open" was triggered in test
        self.assertIn(mock.call("fake_file1.yml", 'r'), mock_open.mock_calls)
        self.assertIn(mock.call("fake_file2.yml", 'r'), mock_open.mock_calls)
        self.assertIn(mock.call("fake_file3.yml", 'r'), mock_open.mock_calls)

    def test_parse_error(self):
        """Given a yaml file with incorrect syntax, throw a warning"""
        with self.assertRaises(exc.TowerCLIError):
            parser.process_extra_vars(["mixing: yaml\nwith=keyval"])

        with self.assertRaises(exc.TowerCLIError):
            parser.process_extra_vars(["incorrect == brackets"])

        # but accept data if there are just two equals
        res = parser.process_extra_vars(['password==pa#exp&U=!9Rop'])
        self.assertEqual(yaml.load(res)['password'], '=pa#exp&U=!9Rop')

        with self.assertRaises(exc.TowerCLIError):
            parser.process_extra_vars(["left_param="])

        with self.assertRaises(exc.TowerCLIError):
            parser.process_extra_vars(["incorrect = =brackets"])

        # Do not accept _raw_params
        with self.assertRaises(exc.TowerCLIError):
            parser.process_extra_vars(["42"])

    def test_handling_bad_data(self):
        """Check robustness of the parser functions in how it handles
        empty strings, null values, etc."""
        # Verify that all parts of the computational chain can handle None
        return_dict = parser.parse_kv(None)
        self.assertEqual(return_dict, {})
        return_dict = parser.string_to_dict(None)
        self.assertEqual(return_dict, {})

        # Verrify that all parts of computational chain can handle ""
        return_dict = parser.parse_kv("")
        self.assertEqual(return_dict, {})
        return_dict = parser.string_to_dict("")
        self.assertEqual(return_dict, {})

        # Check that the behavior is what we want if feeding it an int
        return_dict = parser.parse_kv("foo=5")
        self.assertEqual(return_dict, {"foo": 5})

        # Check that an empty extra_vars list doesn't blow up
        return_str = parser.process_extra_vars([])
        self.assertEqual(return_str, "")
        return_str = parser.process_extra_vars([""], force_json=False)
        self.assertEqual(return_str, "")

    def test_handling_unicode(self):
        """Verify that unicode strings are correctly parsed and
        converted to desired python objects"""
        input_unicode = u"the_user_name='äöü ÄÖÜ'"
        return_dict = parser.string_to_dict(input_unicode)
        self.assertEqual(return_dict, {u'the_user_name': u'äöü ÄÖÜ'})


class TestSplitter_Gen(unittest.TestCase):
    """Set of strings paired with expected output is ran agains the parsing
    functions in this code in order to verrify desired accuracy.

    SPLIT_DATA is taken from Ansible tests located in:
        ansible/test/units/parsing/test_splitter.py
    within the ansible project source.
    """
    SPLIT_DATA = (
        (u'a=b',
            [u'a=b'],
            {u'a': u'b'}),
        (u'a="foo bar"',
            [u'a="foo bar"'],
            {u'a': u'foo bar'}),
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
            self.assertEqual(
                parser.string_to_dict(data[0], allow_kv=True), data[2])

    def test_custom_parse_list(self):
        """Custom input-output scenario tests."""
        for data in self.CUSTOM_DATA:
            self.assertEqual(
                parser.string_to_dict(data[0], allow_kv=True), data[1])

    def test_combination_parse_list(self):
        """Custom input-output scenario tests for 2 sources into one."""
        for data in self.COMBINATION_DATA:
            self.assertEqual(
                yaml.load(parser.process_extra_vars(data[0])),
                data[1]
            )

    def test_unicode_dump(self):
        """Test that data is dumped without unicode character marking."""
        for data in self.COMBINATION_DATA:
            string_rep = parser.process_extra_vars(data[0])
            self.assertEqual(yaml.load(string_rep), data[1])
            assert "python/unicode" not in string_rep
            assert "\\n" not in string_rep


class TestOrderedDump(unittest.TestCase):
    """Set of tests for testing function ordered_dump."""

    CORRECT_OUTPUT = "g: 6\nf: 5\ne: 4\nd: 3\nc: 2\nb: 1\na: 0\n"

    def test_output_order(self):
        """Test that ordered_dump perserves the order of OrderedDict."""
        ordered_dict = OrderedDict()
        for i in reversed('abcdefg'):
            ordered_dict[i] = ord(i) - ord('a')
        self.assertEqual(parser.ordered_dump(ordered_dict,
                                             Dumper=yaml.SafeDumper,
                                             default_flow_style=False),
                         self.CORRECT_OUTPUT)

    def test_mixture(self):
        """Test to ensure that both dict and OrderedDict can be parsed
        by ordered_dump."""
        ordered_dict = OrderedDict()
        ordered_dict['a'] = {}
        ordered_dict['b'] = OrderedDict()
        for item in ordered_dict.values():
            for i in reversed('abcdefg'):
                item[i] = ord(i) - ord('a')
        try:
            parser.ordered_dump(ordered_dict,
                                Dumper=yaml.SafeDumper,
                                default_flow_style=False)
        except Exception:
            self.fail("No exceptions should be raised here.")
