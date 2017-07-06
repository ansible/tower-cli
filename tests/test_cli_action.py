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

import click
from click.testing import CliRunner

from tower_cli.cli.action import ActionSubcommand

from tests.compat import unittest


CATEGORIZED_OUTPUT = """Usage: foo [OPTIONS]

Field Options:
  --bar TEXT  foobar

Local Options:
  --foo TEXT  foobar

Global Options:
  --tower-host TEXT  foobar

Other Options:
  --help  Show this message and exit.
"""


class ActionCommandTests(unittest.TestCase):
    """A set of tests to ensure that the tower_cli Command class works
    in the way we expect.
    """
    def setUp(self):
        self.runner = CliRunner()

    def test_dash_dash_help(self):
        """Establish that no_args_is_help causes the help to be printed,
        and an exit.
        """
        # Create a command with which to test.
        @click.command(no_args_is_help=True, cls=ActionSubcommand)
        @click.argument('parrot')
        def foo(parrot):
            click.echo(parrot)

        # Establish that this command echos if called with echo.
        self.assertEqual(self.runner.invoke(foo, ['bar']).output, 'bar\n')

        # Establish that this command sends help if called with nothing.
        result = self.runner.invoke(foo)
        self.assertIn('--help', result.output)
        self.assertIn('Show this message and exit.\n', result.output)

    def test_categorize_options(self):
        """Establish that options in help text are correctly categorized.
        """
        @click.command(cls=ActionSubcommand)
        @click.option('--foo', help='foobar')
        @click.option('--bar', help='[FIELD]foobar')
        @click.option('--tower-host', help='foobar')
        def foo():
            pass

        result = self.runner.invoke(foo)
        self.assertEqual(result.output, CATEGORIZED_OUTPUT)

        @click.command(cls=ActionSubcommand, add_help_option=False)
        def bar():
            pass

        result = self.runner.invoke(bar)
        self.assertEqual(result.output, 'Usage: bar [OPTIONS]\n')
