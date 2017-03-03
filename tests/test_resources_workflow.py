# Copyright 2017 Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
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

import tower_cli
from tower_cli.resources.workflow import Resource

from tests.compat import unittest, mock


EXAMPLE_NODE_LIST = [
    {
        'id': 1,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [2],
        'unified_job_template': 48,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
    {
        'id': 2,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'unified_job_template': 98,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'project_update'
            }
        }
    }
]


class SchemaTests(unittest.TestCase):
    """
    Tests for the schema file in the tower_cli utils
    """

    def test_expected_output(self):
        """
        Test that the expected structure is returned from the method
        to reorganize workflow nodes in a heirarchy
        """
        output = Resource._workflow_node_structure(EXAMPLE_NODE_LIST)
        self.assertEqual(
            output,
            [
                {
                    'job_template': 48,
                    'always_nodes': [
                        {
                            'project': 98
                        }
                    ]
                }
            ]
        )


class NodeModelTests(unittest.TestCase):
    """
    Tests for workflow nodes
    """

    def setUp(self):
        self.res = tower_cli.get_resource('node')

    def test_translation_into_UJT(self):
        """
        Test application of additional decorator in __getattribute__
        """
        with mock.patch('tower_cli.models.base.ResourceMethods.write') as mck:
            mck.return_value = {'id': 589}
            mck.__name__ = 'create'
            self.res.create(workflow_job_template=1,
                            job_template=5)
            mck.assert_called_once_with(
                create_on_missing=True, fail_on_found=False,
                force_on_exists=False, unified_job_template=5,
                workflow_job_template=1)
