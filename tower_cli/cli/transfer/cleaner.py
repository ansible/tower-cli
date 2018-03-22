import click
from tower_cli.cli.transfer import common
from tower_cli.cli.transfer.logging_command import LoggingCommand
from tower_cli.exceptions import TowerCLIError
import tower_cli


class Cleaner(LoggingCommand):

    def __init__(self, no_color):
        self.no_color = no_color

    def go_ham(self, all=False, asset_input=None):
        stdout = click.get_text_stream('stdout')
        stdin = click.get_text_stream('stdin')

        assets_from_input = common.get_assets_from_input(all, asset_input)

        stdout.write("Please confirm that you want to clean the Tower instance by typing 'YES': ")
        response = stdin.readline()

        if response.strip() != 'YES':
            stdout.write("\nAborting request to empty the instance\n")
            return

        self.print_intro()

        for asset_type in common.SEND_ORDER[::-1]:
            if asset_type not in assets_from_input:
                continue

            identifier = common.get_identity(asset_type)

            assets_to_remove = []
            if assets_from_input[asset_type]['all']:
                resources = tower_cli.get_resource(asset_type).list(all_pages=True)
                if 'results' not in resources:
                    continue
                assets_to_remove = assets_to_remove + resources['results']
            else:
                for name in assets_from_input[asset_type]['names']:
                    try:
                        resource = tower_cli.get_resource(asset_type).get(**{identifier: name})
                        assets_to_remove.append(resource)
                    except TowerCLIError:
                        self.print_header_row(asset_type, name)
                        self.log_ok("Asset does not exist")

            for asset in assets_to_remove:
                self.print_header_row(asset_type, asset[identifier])

                if 'managed_by_tower' in asset and asset['managed_by_tower']:
                    self.log_warn("{} is managed by tower and can not be deleted".format(asset[identifier]))
                    continue

                try:
                    tower_cli.get_resource(asset_type).delete(asset['id'])
                    self.log_change("Asset removed")
                except Exception as e:
                    self.log_error("Unable to delete : {}".format(e))

        self.print_recap()
