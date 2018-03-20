from tower_cli.api import client
from tower_cli.cli.transfer import common
from tower_cli.utils.data_structures import OrderedDict

from tests.compat import unittest


class TransferCommonTests(unittest.TestCase):
    """A set of tests to establish that the Common class works
    in the way we expect.
    """

    def test_get_api_options(self):
        # Assert that an entry without a POST section returns None
        with client.test_mode as t:
            t.register_json('/inventories/', {'actions': {'PUT': {'FIRST': {'type': 'integer'}}}}, method='OPTIONS')
            inventory_options = common.get_api_options('inventory')
            self.assertIsNone(inventory_options)

        # Assert that an entry with a POST section returns the post section
        with client.test_mode as t:
            t.register_json('/job_templates/', {'actions': {'POST': {'test': 'string'}}}, method='OPTIONS')
            job_template_options = common.get_api_options('job_template')
            self.assertEqual(job_template_options, {'test': 'string'}, "Failed to extract POST options")
            # Test a cached API options
            job_template_options = common.get_api_options('job_template')
            self.assertEqual(job_template_options, {'test': 'string'}, "Failed to extract POST options")

    def test_map_node_to_post_options(self):
        source_node = {
            "name": "My Name",
            "created_on": "now",
            "some_value": "the default value",
            "some_other_value": "Not the default",
        }

        target_node = {}

        post_options = {
            "name": {"required": True},
            "some_value": {"required": False, "default": "the default value"},
            # Note, this function does not care if a required value is missing
            "some_missing_required_value": {"required": True},
            "some_other_value": {"default": "The default"},
        }

        # First test that nothing happens if post_options is None
        common.map_node_to_post_options(None, source_node, target_node)
        self.assertEqual(target_node, {}, "Post options of None modified the target node")

        common.map_node_to_post_options(post_options, source_node, target_node)
        self.assertEqual(target_node, {"name": "My Name", "some_other_value": "Not the default"}, "Failed node mapping")

#    def test_resolve_asset_dependencies(self):
#        # Takes an asset and loops over the defined dependences
#        # These are things that may be other objects in Tower
#        # For example, a credential can be tied to an Organization
#        # If the user gave me an Organization like Default (which is what is expected) we need
#        #   to resolve that to Defaults ID
#        def resolve_asset_dependencies(an_asset, asset_type):
#            for relation in an_asset['related']:
#                if relation in an_asset:
#                    # Multiple credentials on things like job templates come through as:
#                    #   vault_credential
#                    #   machine_credential
#                    if relation.endswith("credential"):
#                        model_type = "credential"
#                    else:
#                        model_type = relation
#
#                    try:
#                        expanded_relation = tower_cli.get_resource(model_type).get(an_asset[relation])
#                    except TowerCLIError as e:
#                        raise TowerCLIError("Unable to get {} named {}: {}".format(model_type, an_asset[relation], e))
#
#                    identifier = get_identity(asset_type)
#                    if identifier in expanded_relation:
#                        an_asset[relation] = expanded_relation[identifier]
#
    def test_get_identity(self):
        identity = common.get_identity('schedules')
        self.assertEqual(identity, 'name', 'Schedules did not get proper identity {}'.format(identity))
        identity = common.get_identity('inventory')
        self.assertEqual(identity, 'name', 'Inventory did not get proper identity {}'.format(identity))
        identity = common.get_identity('user')
        self.assertEqual(identity, 'username', 'User did not get proper identity {}'.format(identity))

    def test_remove_encrypted_value(self):
        test_hash = {
            'first': 'ok',
            'second': common.ENCRYPTED_VALUE,
            'sub': OrderedDict({
                'first': common.ENCRYPTED_VALUE,
                'second': 'ok',
            }),
        }
        result_hash = {
            'first': 'ok',
            'second': '',
            'sub': {
                'first': '',
                'second': 'ok',
            },
        }
        common.remove_encrypted_values(test_hash)
        self.assertEqual(test_hash, result_hash, "Failed to remove encrypted values from hash")
#
#        def extract_workflow_nodes(asset):
#            # If workflow_node_post_options is not filled out, get it
#            workflow_node_post_options = get_api_options('node')
#
#            # Get the workflow nodes
#            query_params = [("workflow_job_template", asset['id'])]
#            nodes = tower_cli.get_resource('node').list(**{
#                "query": query_params,
#                'fail_on_multiple_results': False,
#                'all_pages': True
#            })
#
#            # We have to temporarily stash these.
#            # At the end of the process we need to go through all of the nodes and resolve the different
#            # node types from their IDs to their names
#            workflow_nodes_extracted = []
#
#            # This is a stash for us to map the IDs back to the labels
#            workflow_node_to_name_mapping = {}
#
#            node_number = 0
#            for workflow_node in nodes['results']:
#                node_name = 'node{}'.format(node_number)
#                node_number = node_number + 1
#                node_to_add = {
#                    "name": node_name,
#                }
#                workflow_node_to_name_mapping[workflow_node['id']] = node_name
#
#                map_node_to_post_options(workflow_node_post_options, workflow_node, node_to_add)
#
#                # We can delete the workflow_job_template since we will be applying it to this workflow
#                del node_to_add["workflow_job_template"]
#
#                # Now we need to resolve the unified job template
#                del node_to_add["unified_job_template"]
#                node_to_add['unified_job_type'] = workflow_node["summary_fields"]["unified_job_template"][
#                    "unified_job_type"]
#                node_to_add['unified_job_name'] = workflow_node["summary_fields"]["unified_job_template"]["name"]
#
#                if 'credential' in workflow_node and workflow_node['credential']:
#                    node_to_add['credential'] = tower_cli.get_resource('credential').get(workflow_node['credential'])[
#                        'name']
#
#                if 'inventory' in workflow_node and workflow_node['inventory']:
#                    node_to_add['inventory'] = tower_cli.get_resource('inventory').get(workflow_node['inventory'])[
#                        'name']
#
#                # Finally copy over the different node types
#                for node_type in tower_cli.get_resource('workflow').workflow_node_types:
#                    if node_type in workflow_node:
#                        node_to_add[node_type] = workflow_node[node_type]
#
#                workflow_nodes_extracted.append(node_to_add)
#
#            # Finally we need to resolve all of the node IDs in the different types
#            for workflow_node in workflow_nodes_extracted:
#                for node_type in tower_cli.get_resource('workflow').workflow_node_types:
#                    # Resolved nodes will be the resolved node names instead of IDs
#                    resolved_nodes = []
#                    for a_node_id in workflow_node[node_type]:
#                        # If we found a node that does not resolve raise an exception
#                        if a_node_id not in workflow_node_to_name_mapping:
#                            raise TowerCLIError("Workflow export exception: unable to resolve node {} from {}".format(
#                                a_node_id, asset['name'])
#                            )
#
#                        # Add the new node to the list of resolved node
#                        resolved_nodes.append(workflow_node_to_name_mapping[a_node_id])
#
#                    # Put the resolved nodes back into the object
#                    workflow_node[node_type] = resolved_nodes
#
#            return workflow_nodes_extracted
#
#        def extract_inventory_relations(asset, relation_type):
#            # Get the API options for the relation
#            post_options = get_api_options(relation_type)
#
#            # Get all of the hosts
#            try:
#                relations = tower_cli.get_resource(relation_type).list(all_pages=True, **{'inventory': asset['id']})
#            except TowerCLIError as e:
#                raise TowerCLIError("Unable to get {} for {} : {}".format(relation_type, asset['id'], e))
#
#            return_relations = []
#            # If there are no results return an empty array
#            if 'results' not in relations:
#                return return_relations
#
#            name_to_id_map = {}
#            for relation in relations['results']:
#                name_to_id_map[relation['name']] = relation['id']
#                new_relation = {}
#                map_node_to_post_options(post_options, relation, new_relation)
#                if relation_type == 'inventory_source':
#                    # If this is an inventory source we also need to resolve the source_project
#                    if 'source_project' in relation and relation['source_project']:
#                        try:
#                            project = tower_cli.get_resource('project').get(relation['source_project'])
#                        except TowerCLIError as e:
#                            raise TowerCLIError("Unable to get project {} for {} : {}".format(
#                                relation['source_project'], relation_type, e
#                            ))
#                        new_relation['source_project'] = project['name']
#                    if 'source_script' in relation and relation['source_script']:
#                        try:
#                            script = tower_cli.get_resource('inventory_script').get(relation['source_script'])
#                        except TowerCLIError as e:
#                            raise TowerCLIError("Unable to get inventory script {} for {} : {}".format(
#                                relation['source_script'], relation_type, e
#                            ))
#                        new_relation['source_script'] = script['name']
#                    if 'credential' in relation and relation['credential']:
#                        try:
#                            credential = tower_cli.get_resource('credential').get(relation['credential'])
#                        except TowerCLIError as e:
#                            raise TowerCLIError("Unable to get inventory credential {} for {} : {}".format(
#                                relation['credential'], relation_type, e
#                            ))
#                        new_relation['credential'] = credential['name']
#
#                    # Now get the schedules for this source
#                    if 'related' in relation and 'schedules' in relation['related']:
#                        schedule_data = extract_schedules(relation)
#                        new_relation['schedules'] = schedule_data['items']
#
#                del new_relation['inventory']
#
#                return_relations.append(new_relation)
#
#            return {'items': return_relations, 'existing_name_to_id_map': name_to_id_map}
#
#        def extract_inventory_groups(asset):
#            return_asset = []
#            name_to_id_map = {}
#
#            if 'related' not in asset or 'root_groups' not in asset['related']:
#                debug.log("Asset {} does not have root_groups to process".format(asset['name']))
#                return return_asset
#
#            root_groups_response = load_all_assets(asset['related']['root_groups'])
#            for root_group in root_groups_response['results']:
#                name_to_id_map[root_group['name']] = {
#                    'id': root_group['id'],
#                    'sub_groups': {}
#                }
#                process_inv_group_data = process_inventory_groups(root_group)
#                return_asset.append(process_inv_group_data['items'])
#                name_to_id_map[root_group['name']]['sub_groups'] = process_inv_group_data['name_to_id_map']
#
#            return {'items': return_asset, 'existing_name_to_id_map': name_to_id_map}
#
#        def process_inventory_groups(group_json):
#            group_post_options = get_api_options('group')
#            group_to_return = {}
#            map_node_to_post_options(group_post_options, group_json, group_to_return)
#            name_to_id_map = {}
#
#            # Now we need to get the children for the group (which should all be groups)
#            if 'related' in group_json and 'children' in group_json['related']:
#                group_to_return['sub_groups'] = []
#
#                children = load_all_assets(group_json['related']['children'])
#                for child in children['results']:
#                    if 'type' not in child:
#                        debug.log("Found a child without a type in group {} : {}".format(group_json['name'], child))
#                        continue
#
#                    if child['type'] == 'group':
#                        process_inv_data = process_inventory_groups(child)
#                        group_to_return['sub_groups'].append(process_inv_data['items'])
#                        name_to_id_map[child['name']] = {
#                            'id': child['id'],
#                            'sub_groups': process_inv_data['name_to_id_map']
#                        }
#                    else:
#                        debug.log("Found unexpected child type of {} when processing group {}".format(
#                            child['type'], group_json['name']
#                        ))
#
#            # And also get the hosts in this group
#            if 'related' in group_json and 'hosts' in group_json['related']:
#                group_to_return['hosts'] = []
#
#                hosts = load_all_assets(group_json['related']['hosts'])
#
#                for host in hosts['results']:
#                    if 'name' not in host:
#                        debug.log("Found a host without a name in group {} : {}".format(group_json['name'], host))
#                        continue
#                    group_to_return['hosts'].append(host['name'])
#
#            # we can remove the inventory option because we are appending this group directory to an inventory object
#            if 'inventory' in group_to_return:
#                del group_to_return['inventory']
#            return {'items': group_to_return, 'name_to_id_map': name_to_id_map}
#
#        def load_all_assets(url_to_load):
#            keep_loading = True
#            results = {
#                'count': 0,
#                'results': []
#            }
#
#            while keep_loading:
#                # Assume we are done
#                keep_loading = False
#
#                # Get the URL
#                response_object = client.request('GET', url_to_load)
#                response = response_object.json()
#
#                # Update the count and results
#                results['count'] += response['count']
#                results['results'] += response['results']
#
#                # Check if we have a next
#                if 'next' in response and response['next']:
#                    url_to_load = response['next']
#                    keep_loading = True
#
#            return results
#
#        def extract_notifications(asset, notification_type):
#            notifications = []
#            if 'related' in asset and notification_type in asset['related']:
#                response = load_all_assets(asset['related'][notification_type])
#                if 'results' in response:
#                    for notification in response['results']:
#                        notifications.append(notification['name'])
#
#            return notifications
#

    def test_remove_local_path_from_scm_project(self):
        asset = {
            'scm_type': 'Manual',
            'local_path': 'somewhere',
        }
        result_asset = {
            'scm_type': 'Manual',
            'local_path': 'somewhere',
        }
        # Test a no change for either Manual or '' scm_type
        common.remove_local_path_from_scm_project(asset)
        self.assertEqual(asset, result_asset, "Incorrectly removed the local path for manual project")
        asset['scm_type'] = ''
        result_asset['scm_type'] = ''
        common.remove_local_path_from_scm_project(asset)
        self.assertEqual(asset, result_asset, "Incorrectly removed the local path for blank project")

        # Test a change for a git scm_type
        asset['scm_type'] = "git"
        result_asset['scm_type'] = 'git'
        del result_asset['local_path']
        common.remove_local_path_from_scm_project(asset)
        self.assertEqual(asset, result_asset, "Failed to remove the local path for git project")

#        def get_assets_from_input(all=False, asset_input=None):
#            return_assets = {}
#            if all:
#                for aType in SEND_ORDER:
#                    if aType not in return_assets:
#                        return_assets[aType] = {'all': True, 'names': []}
#                    return_assets[aType]['all'] = True
#            else:
#                for asset_type in asset_input:
#                    return_assets[asset_type] = {'all': False, 'names': []}
#
#                    for asset_name in asset_input[asset_type]:
#                        if asset_name == 'all':
#                            return_assets[asset_type]['all'] = True
#                        else:
#                            return_assets[asset_type]['names'].append(asset_name)
#
#            if return_assets == {}:
#                raise TowerCLIError("Nothing assets were specified")
#
#            return return_assets
#
#        def extract_extra_credentials(asset):
#            return_credentials = []
#            name_to_id_map = {}
#
#            extra_credentials = load_all_assets(asset['related']['extra_credentials'])
#            for a_credential in extra_credentials['results']:
#                name_to_id_map[a_credential['name']] = a_credential['id']
#                return_credentials.append(a_credential['name'])
#
#            return {'items': return_credentials, 'existing_name_to_id_map': name_to_id_map}
#
#        def extract_schedules(asset):
#            return_schedules = []
#            name_to_object_map = {}
#
#            schedule_options = get_api_options('schedules')
#            schedules = load_all_assets(asset['related']['schedules'])
#            for a_schedule in schedules['results']:
#                name_to_object_map[a_schedule['name']] = a_schedule
#                reduced_schedule = {}
#                map_node_to_post_options(schedule_options, a_schedule, reduced_schedule)
#                del (reduced_schedule['unified_job_template'])
#                return_schedules.append(reduced_schedule)
#
#            return {'items': return_schedules, 'existing_name_to_object_map': name_to_object_map}
