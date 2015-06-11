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

from tower_cli.utils.decorators import command

from tests.compat import unittest


class CommandTests(unittest.TestCase):
    """Establish that the @command decorator works as I expect,
    with and without a call signature.
    """
    def test_command_without_call_signature(self):
        """Establish that if we call the @command decorator without a
        call signature, that it decorates the function appropriately.
        """
        # Define a command.
        @command
        def foo():
            pass

        # Ensure that it's a command.
        self.assertIsInstance(foo, click.core.Command)

    def test_command_with_call_signature(self):
        """Establish that if we call the @command decorator with a call
        signature, that it decorates the function appropriately.
        """
        # Define a command
        @command()
        def foo():
            pass

        # Ensure that it's a command.
        self.assertIsInstance(foo, click.core.Command)
