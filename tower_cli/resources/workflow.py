# Copyright 2016, Ansible by Red Hat
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

from __future__ import absolute_import, unicode_literals

from tower_cli import models, resources, get_resource
from tower_cli.cli import types
from tower_cli.utils.parser import string_to_dict
from tower_cli.exceptions import BadRequest
from tower_cli.conf import settings
from tower_cli.resources.node import NODE_STANDARD_FIELDS, JOB_TYPES

import click
from collections import deque


class TreeNode(object):
    def __init__(self, data, wfjt, include_id=False):
        ujt_attrs = list(JOB_TYPES.values())
        FK_FIELDS = ujt_attrs + ['inventory', 'credential']
        node_attrs = {}
        attr_names = NODE_STANDARD_FIELDS + ujt_attrs
        if include_id:
            attr_names.append('id')
        for fd in attr_names:
            if fd not in data:
                continue
            if fd in FK_FIELDS and not isinstance(data[fd], int):
                # Node's template was given by name, do lookup
                ujt_res = get_resource(fd)
                ujt_data = ujt_res.get(name=data[fd])
                node_attrs[fd] = ujt_data['id']
            else:
                node_attrs[fd] = data[fd]
        node_attrs['workflow_job_template'] = wfjt
        for ujt_name in ujt_attrs:
            if ujt_name not in node_attrs:
                continue
            if 'unified_job_template' not in node_attrs:
                node_attrs['unified_job_template'] = node_attrs.pop(ujt_name)
            else:
                raise BadRequest(
                    'You should not provide more than one of the attributes'
                    ' job_template, project and inventory_source.'
                )
        self.unified_job_template = node_attrs.get('unified_job_template', None)
        self.node_attrs = node_attrs
        for rel in ['success_nodes', 'failure_nodes', 'always_nodes']:
            setattr(
                self, rel,
                [TreeNode(x, wfjt, include_id=include_id) for x in data.get(rel, data.get(rel[: -6], []))]
            )

    def create(self, node_res):
        self.node_attrs['id'] = node_res.create(**self.node_attrs)['id']
        queue = deque()
        queue.append(self)
        while queue:
            node = queue.popleft()
            for rel in ['success_nodes', 'failure_nodes', 'always_nodes']:
                for sub_node in getattr(node, rel, []):
                    sub_node.node_attrs['id'] = node_res.create(**sub_node.node_attrs)['id']
                    getattr(node_res, 'associate_%s' % rel[:-1])(
                        node.node_attrs['id'], child=sub_node.node_attrs['id']
                    )
                    queue.append(sub_node)

    def delete(self, node_res):
        for rel in ['success_nodes', 'failure_nodes', 'always_nodes']:
            for sub_node in getattr(self, rel, []):
                sub_node.delete(node_res)
        node_res.delete(pk=self.node_attrs['id'])


def _compare_node_lists(old, new):
    '''
    Investigate two lists of workflow TreeNodes and categorize them.

    There will be three types of nodes after categorization:
        1. Nodes that only exists in the new list. These nodes will later be
        created recursively.
        2. Nodes that only exists in the old list. These nodes will later be
        deleted recursively.
        3. Node pairs that makes an exact match. These nodes will be further
        investigated.

    Corresponding nodes of old and new lists will be distinguished by their
    unified_job_template value. A special case is that both the old and the new
    lists contain one type of node, say A, and at least one of them contains
    duplicates. In this case all A nodes in the old list will be categorized as
    to-be-deleted and all A nodes in the new list will be categorized as
    to-be-created.
    '''
    to_expand = []
    to_delete = []
    to_recurse = []
    old_records = {}
    new_records = {}
    for tree_node in old:
        old_records.setdefault(tree_node.unified_job_template, [])
        old_records[tree_node.unified_job_template].append(tree_node)
    for tree_node in new:
        new_records.setdefault(tree_node.unified_job_template, [])
        new_records[tree_node.unified_job_template].append(tree_node)
    for ujt_id in old_records:
        if ujt_id not in new_records:
            to_delete.extend(old_records[ujt_id])
            continue
        old_list = old_records[ujt_id]
        new_list = new_records.pop(ujt_id)
        if len(old_list) == 1 and len(new_list) == 1:
            to_recurse.append((old_list[0], new_list[0]))
        else:
            to_delete.extend(old_list)
            to_expand.extend(new_list)
    for nodes in new_records.values():
        to_expand.extend(nodes)
    return to_expand, to_delete, to_recurse


def _do_update_workflow(existing_roots, updated_roots, node_res):
    to_expand, to_delete, to_recurse = _compare_node_lists(existing_roots, updated_roots)
    for node in to_delete:
        node.delete(node_res)
    for node in to_expand:
        node.create(node_res)
    for old_node, new_node in to_recurse:
        for rel in ['success_nodes', 'failure_nodes', 'always_nodes']:
            to_assoc = _do_update_workflow(getattr(old_node, rel, []), getattr(new_node, rel, []), node_res)
            for sub_node in to_assoc:
                getattr(node_res, 'associate_%s' % rel[:-1])(old_node.node_attrs['id'], child=sub_node.node_attrs['id'])
    return to_expand


def _update_workflow(existing_roots, updated_roots):
    # Node resource should be fetched *only once*.
    node_res = get_resource('node')
    _do_update_workflow(existing_roots, updated_roots, node_res)


class Resource(models.SurveyResource):
    cli_help = 'Manage workflow job templates.'
    endpoint = '/workflow_job_templates/'
    unified_job_type = '/workflow_jobs/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    extra_vars = models.Field(
        type=types.Variables(), required=False, display=False, multiple=True,
        help_text='Extra variables used by Ansible in YAML or key=value '
                  'format. Use @ to get YAML from a file. Use the option '
                  'multiple times to add multiple extra variables')
    organization = models.Field(type=types.Related('organization'),
                                required=False)
    survey_enabled = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for job type on launch.')
    survey_spec = models.Field(
        type=types.Variables(), required=False, display=False,
        help_text='On write commands, perform extra POST to the '
                  'survey_spec endpoint.')

    @staticmethod
    def _workflow_node_structure(node_results):
        '''
        Takes the list results from the API in `node_results` and
        translates this data into a dictionary organized in a
        human-readable heirarchial structure
        '''
        # Build list address translation, and create backlink lists
        node_list_pos = {}
        for i, node_result in enumerate(node_results):
            for rel in ['success', 'failure', 'always']:
                node_result['{0}_backlinks'.format(rel)] = []
            node_list_pos[node_result['id']] = i

        # Populate backlink lists
        for node_result in node_results:
            for rel in ['success', 'failure', 'always']:
                for sub_node_id in node_result['{0}_nodes'.format(rel)]:
                    j = node_list_pos[sub_node_id]
                    node_results[j]['{0}_backlinks'.format(rel)].append(
                        node_result['id'])

        # Find the root nodes
        root_nodes = []
        for node_result in node_results:
            is_root = True
            for rel in ['success', 'failure', 'always']:
                if node_result['{0}_backlinks'.format(rel)] != []:
                    is_root = False
                    break
            if is_root:
                root_nodes.append(node_result['id'])

        # Create network dictionary recursively from root nodes
        def branch_schema(node_id):
            i = node_list_pos[node_id]
            node_dict = node_results[i]
            ret_dict = {"id": node_id}
            for fd in NODE_STANDARD_FIELDS:
                val = node_dict.get(fd, None)
                if val is not None:
                    if fd == 'unified_job_template':
                        job_type = node_dict['summary_fields'][
                            'unified_job_template']['unified_job_type']
                        ujt_key = JOB_TYPES[job_type]
                        ret_dict[ujt_key] = val
                    else:
                        ret_dict[fd] = val
                for rel in ['success', 'failure', 'always']:
                    sub_node_id_list = node_dict['{0}_nodes'.format(rel)]
                    if len(sub_node_id_list) == 0:
                        continue
                    relationship_name = '{0}_nodes'.format(rel)
                    ret_dict[relationship_name] = []
                    for sub_node_id in sub_node_id_list:
                        ret_dict[relationship_name].append(
                            branch_schema(sub_node_id))
            return ret_dict

        schema_dict = []
        for root_node_id in root_nodes:
            schema_dict.append(branch_schema(root_node_id))
        return schema_dict

    def _get_schema(self, wfjt_id):
        """
        Returns a dictionary that represents the node network of the
        workflow job template
        """
        node_res = get_resource('node')
        node_results = node_res.list(workflow_job_template=wfjt_id,
                                     all_pages=True)['results']
        return self._workflow_node_structure(node_results)

    @resources.command(use_fields_as_options=False)
    @click.argument('wfjt', type=types.Related('workflow'))
    @click.argument('node_network', type=types.Variables(), required=False)
    def schema(self, wfjt, node_network=None):
        """
        Convert YAML/JSON content into workflow node objects if
        node_network param is given.
        If not, print a YAML representation of the node network.
        """
        existing_network = self._get_schema(wfjt)
        if not isinstance(existing_network, list):
            existing_network = []
        if node_network is None:
            if settings.format == 'human':
                settings.format = 'yaml'
            return existing_network

        if hasattr(node_network, 'read'):
            node_network = node_network.read()
        node_network = string_to_dict(
            node_network, allow_kv=False, require_dict=False)
        if not isinstance(node_network, list):
            node_network = []

        _update_workflow([TreeNode(x, wfjt, include_id=True) for x in existing_network],
                         [TreeNode(x, wfjt) for x in node_network])

        if settings.format == 'human':
            settings.format = 'yaml'
        return self._get_schema(wfjt)

    @resources.command(use_fields_as_options=False)
    @click.option('--workflow', type=types.Related('workflow'))
    @click.option('--label', type=types.Related('label'))
    def associate_label(self, workflow, label):
        """Associate an label with this workflow."""
        return self._assoc('labels', workflow, label)

    @resources.command(use_fields_as_options=False)
    @click.option('--workflow', type=types.Related('workflow'))
    @click.option('--label', type=types.Related('label'))
    def disassociate_label(self, workflow, label):
        """Disassociate an label from this workflow."""
        return self._disassoc('labels', workflow, label)

    @resources.command(use_fields_as_options=False)
    @click.option('--workflow', type=types.Related('workflow'))
    @click.option('--notification-template',
                  type=types.Related('notification_template'))
    @click.option('--status', type=click.Choice(['any', 'error', 'success']),
                  required=False, default='any', help='Specify job run status'
                  ' of job template to relate to.')
    def associate_notification_template(self, workflow,
                                        notification_template, status):
        """Associate a notification template from this workflow."""
        return self._assoc('notification_templates_%s' % status,
                           workflow, notification_template)

    @resources.command(use_fields_as_options=False)
    @click.option('--workflow', type=types.Related('workflow'))
    @click.option('--notification-template',
                  type=types.Related('notification_template'))
    @click.option('--status', type=click.Choice(['any', 'error', 'success']),
                  required=False, default='any', help='Specify job run status'
                  ' of job template to relate to.')
    def disassociate_notification_template(self, workflow,
                                           notification_template, status):
        """Disassociate a notification template from this workflow."""
        return self._disassoc('notification_templates_%s' % status,
                              workflow, notification_template)
