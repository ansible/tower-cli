import tower_cli
from tower_cli.exceptions import TowerCLIError
from tower_cli.cli.transfer import common
from tower_cli.conf import settings
from tower_cli.utils import parser
from tower_cli.resources.role import RESOURCE_FIELDS
import click


class Receiver:
    def receive(self, all=False, asset_input=None):
        exported_objects = self.export_assets(all, asset_input)

        stdout = click.get_text_stream('stdout')
        if settings.format == 'human' or settings.format == 'json':
            import json
            stdout.write(json.dumps(exported_objects, indent=2))
        elif settings.format == 'yaml':
            import yaml
            stdout.write(parser.ordered_dump(exported_objects, Dumper=yaml.SafeDumper, default_flow_style=False))
        else:
            raise TowerCLIError("Format {} is unsupported".format(settings.format))
        stdout.write("\n")

    def export_assets(self, all, asset_input):
        # Extract and consolidate all of the items we got on the command line
        assets_to_export = common.get_assets_from_input(all, asset_input)

        # These will be returned from this method
        exported_objects = []

        for asset_type in assets_to_export:
            # Load the API options for this asset_type of asset
            types_api_options = common.get_api_options(asset_type)

            # Now we are going to extract the objects from Tower and put them into an array for processing
            acquired_assets_to_export = []
            identifier = common.get_identity(asset_type)

            # Now we are either going to get everything or just one item and append that to the assets_to_export
            if assets_to_export[asset_type]['all']:
                resources = tower_cli.get_resource(asset_type).list(all_pages=True)
                if 'results' not in resources:
                    continue
                acquired_assets_to_export = acquired_assets_to_export + resources['results']
            else:
                for name in assets_to_export[asset_type]['names']:
                    try:
                        resource = tower_cli.get_resource(asset_type).get(**{identifier: name})
                    except TowerCLIError as e:
                        raise TowerCLIError("Unable to get {} named {} : {}".format(asset_type, name, e))
                    acquired_assets_to_export.append(resource)

            # Next we are going to loop over the objects we got from Tower
            for asset in acquired_assets_to_export:
                # If this object is managed_by_tower then move on
                if 'managed_by_tower' in asset and asset['managed_by_tower']:
                    continue

                # Resolve the dependencies
                common.resolve_asset_dependencies(asset, asset_type)

                # Create a new object with the ASSET_TYPE_KEY and merge the options in from the object we got
                exported_asset = {common.ASSET_TYPE_KEY: asset_type}
                common.map_node_to_post_options(types_api_options, asset, exported_asset)

                # Clean up any $encrypted$ values
                common.remove_encrypted_values(exported_asset)

                # Special cases for touch up
                if asset_type == 'project':
                    # Exported projects that are not manual don't need a local path
                    common.remove_local_path_from_scm_project(exported_asset)

                # Next we are going to go after any of
                for relation in tower_cli.get_resource(asset_type).related:
                    if common.ASSET_RELATION_KEY not in exported_asset:
                        exported_asset[common.ASSET_RELATION_KEY] = {}

                    if relation == 'workflow_nodes':
                        exported_asset[common.ASSET_RELATION_KEY][relation] = common.extract_workflow_nodes(asset)

                    elif relation == 'survey_spec':
                        survey_spec = tower_cli.get_resource(asset_type).survey(asset['id'])
                        exported_asset[common.ASSET_RELATION_KEY][relation] = survey_spec

                    elif relation == 'host' or relation == 'inventory_source':
                        exported_asset[common.ASSET_RELATION_KEY][relation] = \
                            common.extract_inventory_relations(asset, relation)['items']

                    elif relation == 'group':
                        exported_asset[common.ASSET_RELATION_KEY][relation] = \
                            common.extract_inventory_groups(asset)['items']

                    elif relation == 'notification_templates':
                        for notification_type in common.NOTIFICATION_TYPES:
                            exported_asset[common.ASSET_RELATION_KEY][notification_type] = \
                                common.extract_notifications(asset, notification_type)

                    elif relation == 'credentials':
                        exported_asset[common.ASSET_RELATION_KEY][relation] =\
                            common.extract_credentials(asset)['items']

                    elif relation == 'schedules':
                        exported_asset[common.ASSET_RELATION_KEY][relation] =\
                            common.extract_schedules(asset)['items']

                    elif relation == 'labels':
                        exported_asset[common.ASSET_RELATION_KEY][relation] =\
                            common.extract_labels(asset)['items']

                # If this asset type is in the RESOURCE_FIELDS of the Role object than export its roles
                if asset_type in RESOURCE_FIELDS:
                    if common.ASSET_RELATION_KEY not in exported_asset:
                        exported_asset[common.ASSET_RELATION_KEY] = {}
                    exported_asset[common.ASSET_RELATION_KEY]['roles'] = common.extract_roles(asset)['items']

                # Finally add the object to the list of objects that are being exported
                exported_objects.append(exported_asset)

        return exported_objects
