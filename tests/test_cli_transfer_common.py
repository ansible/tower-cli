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
