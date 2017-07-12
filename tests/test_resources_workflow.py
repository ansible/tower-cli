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

import json

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


CUR_WORKFLOW = [
    {
        'id': 1,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [2, 3],
        'workflow_job_template': 1,
        'unified_job_template': 1,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'project_update'
            }
        }
    },
    {
        'id': 2,
        'success_nodes': [4],
        'failure_nodes': [5],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 2,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'project_update'
            }
        }
    },
    {
        'id': 3,
        'success_nodes': [],
        'failure_nodes': [6, 7],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 3,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'project_update'
            }
        }
    },
    {
        'id': 4,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 4,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
    {
        'id': 5,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 5,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
    {
        'id': 6,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 6,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
    {
        'id': 7,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 7,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
    {
        'id': 8,
        'success_nodes': [9, 10],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 8,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'inventory_update'
            }
        }
    },
    {
        'id': 9,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [11],
        'workflow_job_template': 1,
        'unified_job_template': 9,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'inventory_update'
            }
        }
    },
    {
        'id': 10,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [12],
        'workflow_job_template': 1,
        'unified_job_template': 9,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'inventory_update'
            }
        }
    },
    {
        'id': 11,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 10,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
    {
        'id': 12,
        'success_nodes': [],
        'failure_nodes': [],
        'always_nodes': [],
        'workflow_job_template': 1,
        'unified_job_template': 10,
        'summary_fields': {
            'unified_job_template': {
                'unified_job_type': 'job'
            }
        }
    },
]


UPDATED_WORKFLOW = [
    {
        u'project': 1,
        u'always': [
            {
                u'project': 2,
                u'success': [
                    {
                        u'job_template': 4
                    }
                ],
                u'failure': [
                    {
                        u'job_template': 5,
                        u'success': [
                            {
                                u'job_template': 6
                            },
                            {
                                u'job_template': 7
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        u'inventory_source': 8,
        u'success': [
            {
                u'inventory_source': 9,
                u'always': [
                    {
                        u'job_template': 10,
                    }
                ]
            },
            {
                u'inventory_source': 9,
                u'always': [
                    {
                        u'job_template': 10,
                    }
                ]
            }
        ]
    }
]


UPDATED_RESULT = [
    {
        u'project': 1,
        u'always_nodes': [
            {
                u'project': 2,
                u'success_nodes': [
                    {
                        u'job_template': 4
                    }
                ],
                u'failure_nodes': [
                    {
                        u'job_template': 5,
                        u'success_nodes': [
                            {
                                u'job_template': 6
                            },
                            {
                                u'job_template': 7
                            }
                        ]
                    }
                ]
            }
        ]
    },
    {
        u'inventory_source': 8,
        u'success_nodes': [
            {
                u'job_template': 9,
                u'always_nodes': [
                    {
                        u'job_template': 10,
                    }
                ]
            },
            {
                u'job_template': 9,
                u'always_nodes': [
                    {
                        u'job_template': 10,
                    }
                ]
            }
        ]
    }
]


class NodeResMock(object):
    def __init__(self, init_list):
        self.db = {}
        self.cur_pk = 0
        for node in init_list:
            self.db[node['id']] = node
            self.cur_pk = max(self.cur_pk, node['id'])
        self.create_cnt = 0
        self.delete_cnt = 0
        self.associate_success_cnt = 0
        self.associate_failure_cnt = 0
        self.associate_always_cnt = 0

    def create(self, **kwargs):
        self.cur_pk += 1
        new_record = {
            'success_nodes': [],
            'failure_nodes': [],
            'always_nodes': [],
            'id': self.cur_pk,
            'summary_fields': {
                'unified_job_template': {
                    'unified_job_type': 'job'
                }
            }
        }
        new_record.update(kwargs)
        self.db[new_record['id']] = new_record
        self.create_cnt += 1
        return new_record

    def list(self, **kwargs):
        return {
            'count': len(self.db),
            'results': list(self.db.values()),
            'next': None,
            'previous': None
        }

    def delete(self, pk=None):
        if not pk:
            return
        self.db.pop(pk, None)
        for record in self.db.values():
            for rel in ['success_nodes', 'failure_nodes', 'always_nodes']:
                try:
                    record[rel].remove(pk)
                except ValueError:
                    pass
        self.delete_cnt += 1

    def associate_success_node(self, id, child=None):
        if not child or id not in self.db:
            return
        self.db[id]['success_nodes'].append(child)
        self.associate_success_cnt += 1

    def associate_failure_node(self, id, child=None):
        if not child or id not in self.db:
            return
        self.db[id]['failure_nodes'].append(child)
        self.associate_failure_cnt += 1

    def associate_always_node(self, id, child=None):
        if not child or id not in self.db:
            return
        self.db[id]['always_nodes'].append(child)
        self.associate_always_cnt += 1


class SchemaTests(unittest.TestCase):
    """
    Tests for the schema file in the tower_cli utils
    """
    def setUp(self):
        self.res = tower_cli.get_resource('workflow')

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
                    'id': 1,
                    'always_nodes': [
                        {
                            'id': 2,
                            'project': 98
                        }
                    ]
                }
            ]
        )

    def _remove_ids(self, input_list):
        for node in input_list:
            node.pop('id', None)
            for rel in ['success_nodes', 'failure_nodes', 'always_nodes']:
                if rel in node:
                    self._remove_ids(node[rel])
        return input_list

    def test_schema_update(self):
        node_res_mock = NodeResMock(CUR_WORKFLOW)
        with mock.patch('tower_cli.resources.workflow.get_resource', return_value=node_res_mock):
            res = self._remove_ids(self.res.schema(1, node_network=json.dumps(UPDATED_WORKFLOW)))
            self.assertEqual(res, UPDATED_RESULT)
            self.assertEqual(node_res_mock.create_cnt, 6)
            self.assertEqual(node_res_mock.delete_cnt, 7)
            self.assertEqual(node_res_mock.associate_success_cnt, 4)
            self.assertEqual(node_res_mock.associate_failure_cnt, 0)
            self.assertEqual(node_res_mock.associate_always_cnt, 2)


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
        with mock.patch('tower_cli.models.base.BaseResource.write') as mck:
            mck.return_value = {'id': 589}
            mck.__name__ = 'create'
            self.res.create(workflow_job_template=1,
                            job_template=5)
            self.assertEqual(mck.call_args[1]['unified_job_template'], 5)
            self.assertEqual(mck.call_args[1]['workflow_job_template'], 1)
