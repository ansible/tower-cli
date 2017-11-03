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

from tower_cli.conf import settings
from tower_cli.utils import secho
from tower_cli.utils import grammar

from tests.compat import unittest, mock


class SechoTests(unittest.TestCase):
    """Establish that our wrapper around click.secho works in the way
    that we expect.
    """
    def test_color_true(self):
        """Establish that when the color setting is true, that color
        data is not stripped.
        """
        with settings.runtime_values(color=True):
            with mock.patch.object(click, 'secho') as click_secho:
                secho('foo bar baz', fg='green')
                click_secho.assert_called_once_with('foo bar baz',
                                                    fg='green')

    def test_color_false(self):
        """Establish that when the color setting is false, that color
        data is stripped.
        """
        with settings.runtime_values(color=False):
            with mock.patch.object(click, 'secho') as click_secho:
                secho('foo bar baz', fg='green')
                click_secho.assert_called_once_with('foo bar baz')


class GrammarTests(unittest.TestCase):

    def test_plurals(self):
        """English words changed from singular to plural"""
        self.assertEqual(grammar.pluralize("inventory"), "inventories")
        self.assertEqual(grammar.pluralize("job_template"), "job_templates")
        self.assertEqual(grammar.pluralize("workflow"), "workflow_job_templates")

    def test_singulars(self):
        """English words changed from singular to plural"""
        self.assertEqual(grammar.singularize("inventories"), "inventory")
        self.assertEqual(grammar.singularize("job_templates"), "job_template")
        self.assertEqual(grammar.singularize("job_template"), "job_template")
