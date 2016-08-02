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

from click.testing import CliRunner

import requests

import tower_cli
from tower_cli.api import client
from tower_cli.commands.version import version

from tests.compat import unittest, mock


class VersionTests(unittest.TestCase):
    """A set of tests to ensure that the version command runs in the way
    that we expect.
    """
    def setUp(self):
        self.runner = CliRunner()

    def test_version_command(self):
        """Establish that the version command returns the output we
        expect.
        """
        # Set up output from the /config/ endpoint in Tower and
        # invoke the command.
        with client.test_mode as t:
            t.register_json('/config/', {'version': '4.21'})
            result = self.runner.invoke(version)

            # Verify that we got the output we expected.
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output.strip(),
                'Tower CLI %s\nAnsible Tower 4.21' % tower_cli.__version__,
            )

    def test_cannot_connect(self):
        """Establish that the version command gives a nice error in cases
        where it cannot connect to Tower.
        """
        with mock.patch.object(client, 'get') as get:
            get.side_effect = requests.exceptions.RequestException
            result = self.runner.invoke(version)
            self.assertEqual(result.exit_code, 1)
            self.assertIn('Could not connect to Ansible Tower.', result.output)
