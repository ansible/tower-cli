import tower_cli
import json
from tower_cli.exceptions import TowerCLIError, CannotStartJob, JobFailure
import tower_cli.cli.transfer.common as common
from tower_cli.cli.transfer.logging_command import LoggingCommand
from tower_cli.utils import parser
from tower_cli.resources.role import ACTOR_FIELDS
import click
import os
import sys
from tower_cli.api import client
import copy


class Sender(LoggingCommand):
    my_user = None
    secret_management = 'default'
    columns = None
    sorted_assets = {}
    credential_type_objects = {}

    def __init__(self, no_color):
        self.no_color = no_color

    def send(self, source, prevent, exclude, secret_management):
        self.secret_management = secret_management

        self.print_intro()

        # First lets get all of the assets from the input this will raise if there are errors
        import_json = self.get_all_objects(source)
        if self.error_messages != 0:
            raise TowerCLIError("Unable to get assets from input")

        # Next we will sort all of the assets by their type again, will raise if there are errors
        # This is setting sorted_assets
        self.prep_and_sort_all_assets(import_json, prevent, exclude)

        for asset_type in common.SEND_ORDER:
            # If we don't have any of this asset type we can move on
            if asset_type not in self.sorted_assets or len(self.sorted_assets[asset_type]) == 0:
                continue

            identifier = common.get_identity(asset_type)
            resource = tower_cli.get_resource(asset_type)
            post_options = common.get_api_options(asset_type)

            for an_asset in self.sorted_assets[asset_type]:
                asset_name = an_asset[identifier]

                self.print_header_row(asset_type, asset_name)

                # First, validate and resolve all of the dependencies resolve
                # I.e. change an org name from "Default" to "1"
                # This has to be done here instead of in the prepAndSort because we may be building an asset
                if not self.resolve_asset_dependencies(asset_type, an_asset):
                    continue

                # Next validate all of the fields in the request
                # Again, we can't do this in the prep because we might be building something that we need
                # For example, we might build a credential_type that fulfills the type field of a credential
                if not self.can_object_post(asset_type, an_asset, post_options):
                    continue

                # See if we can get an existing object with this identifier
                existing_object = None
                try:
                    existing_object = resource.get(**{identifier: asset_name})
                except TowerCLIError:
                    pass

                # Extract the relations (we don't want to add them into the objects
                relations = None
                if common.ASSET_RELATION_KEY in an_asset:
                    relations = an_asset[common.ASSET_RELATION_KEY]
                    del an_asset[common.ASSET_RELATION_KEY]

                asset_changed = False
                # If not, we need to create one, otherwise we can check it for update
                if existing_object is None:
                    # Here are some special cases
                    if asset_type == 'user' and 'password' not in an_asset:
                        password = self.get_secret(
                            "Enter the user password for {}".format(asset_name),
                            "Setting password of user {}".format(asset_name),
                            'password'
                        )
                        an_asset['password'] = password

                    # If we are a credential there are a couple of conditions to match
                    if asset_type == 'credential':
                        # First, if we don't have an org, user or team we need to get our user and set that as user
                        # Otherwise the API will throw an exception
                        if 'organization' not in an_asset and 'user' not in an_asset and 'team' not in an_asset:
                            if self.my_user is None:
                                # First use the API to get the user
                                from tower_cli.api import Client
                                api_client = Client()
                                me_response = api_client.request('GET', 'me')
                                response_json = me_response.json()
                                if 'results' not in response_json or 'id' not in response_json['results'][0]:
                                    raise TowerCLIError("Unable to get user information from Tower")
                                self.my_user = response_json['results'][0]['id']
                            an_asset['user'] = self.my_user

                        # Second, if this is a custom defined template we need to see if there is a required
                        # password field in it
                        self.set_password_in_custom_credential(an_asset, asset_name)

                        # Third we need to make sure that any required passwords are set
                        if 'inputs' in an_asset:
                            if 'vault_password' in an_asset['inputs'] and an_asset['inputs']['vault_password'] == '':
                                an_asset['inputs']['vault_password'] = self.get_secret(
                                    'Enter vault password for {}'.format(asset_name),
                                    "Setting vault_password for {}".format(asset_name),
                                    'password'
                                )
                            if 'password' in an_asset['inputs'] and an_asset['inputs']['password'] == '':
                                an_asset['inputs']['password'] = self.get_secret(
                                    "Enter the password for {}".format(asset_name),
                                    "Setting password for {}".format(asset_name),
                                    'password'
                                )
                            if 'security_token' in an_asset['inputs'] and an_asset['inputs']['security_token'] == '':
                                an_asset['inputs']['security_token'] = self.get_secret(
                                    'Enter the security token for {}'.format(asset_name),
                                    "Setting security token for {}".format(asset_name),
                                    'token'
                                )
                            if 'become_password' in an_asset['inputs'] and an_asset['inputs']['become_password'] == '':
                                an_asset['inputs']['become_password'] = self.get_secret(
                                    'Enter the become password for {}'.format(asset_name),
                                    "Setting become password for {}".format(asset_name),
                                    'password'
                                )
                            if 'secret' in an_asset['inputs'] and an_asset['inputs']['secret'] == '':
                                an_asset['inputs']['secret'] = self.get_secret(
                                    'Enter the secret for {}'.format(asset_name),
                                    "Setting secret for {}".format(asset_name),
                                    'secret'
                                )
                            if 'authorize_password' in an_asset['inputs']\
                                    and an_asset['inputs']['authorize_password'] == '':
                                an_asset['inputs']['authorize_password'] = self.get_secret(
                                    'Enter the authorize password for {}'.format(asset_name),
                                    "Setting authorize password for {}".format(asset_name),
                                    'password'
                                )
                            if 'ssh_key_unlock' in an_asset['inputs'] and an_asset['inputs']['ssh_key_unlock'] == '':
                                self.log_warn("*** Setting ssh key for {} to 'password'".format(asset_name))
                                an_asset['inputs']['ssh_key_unlock'] = 'password'
                                an_asset['inputs']['ssh_key_data'] = "-----BEGIN RSA PRIVATE KEY-----\n" \
                                    "Proc-Type: 4,ENCRYPTED\n" \
                                    "DEK-Info: AES-128-CBC,410307D0168F2A93EAAD78F85C136ED8\n" \
                                    "\n" \
                                    "Vtjf3RaotxIMjgKLfoDeR3xEksmOWXk8Ei4iK5T8dEWxkRsM/asRe6gMeGyOPv73\n" \
                                    "wxjPunVmovY/09FyXIk7W2HT4gt7kF3Qvz028taTjkF/T1YAvMarBSL6PgPdamCq\n" \
                                    "oXAfPjHoqBdRqEmEcclIZ7WW4bXIEzw1f5ad1mERl+5O2/KNdM0R6EhemporF46/\n" \
                                    "En8jQm+kQefxgI9EDH79WkRK0BhcW7Ho7Jb4EfHEJnBaoo0NGp8rJh0bCNoaa1Q7\n" \
                                    "nlFHJNbZioNDsEaVc7nzZdIfISWx5UAPWj6meuvhylbaZXydxfkUccCI4bP+YYFf\n" \
                                    "y7qfkkfqBpcVelYmO5Ymwd4bLCayUB8HszHpPoKcfyANt/hCFjavb8rffsH31c+r\n" \
                                    "4eSWr2XD1OVFUTQpKizp7NyaoPZMhgi1CUTc23NZOc/YBoVIyAj1NfL8Vw1xafwo\n" \
                                    "VKoePmLO7Gk5FblQKWldDsigcRNtgSzBWTHtzBPcHDzHO9k1H6spxFANgaSS792f\n" \
                                    "h24bUAjq0Q1/nER5k1HyS2ZfWsYUeSh0DEkdZ1LqGA49H/XwAPHpSZSremFm7yuM\n" \
                                    "98EFzIne21/hJ0qefrggPGcy9wHbF+RqpLIDR7K/gSfJKxD/vb9GBaBn1Wl1jskV\n" \
                                    "wOsnlxDk0jBIZ+P6c7Werp8ZyDh9kupMUjYNrl4WaftF/y2dT1RRzAVEgEMt/Y6H\n" \
                                    "giGNQmVnC7Q6Gl7bO6qt6rjcAoc8R0Y+LfgEFXRio3oD8n7K/lq5wAfs9K1SbKTi\n" \
                                    "FBiUrQInsmeioBNlz1AHW3VrRbWCeu7xqCFK8B5ZTcPD4w6DY86SGmzPBIP65Rhd\n" \
                                    "mqxIiXqfC5z+xkZGT9LNFwzO3Ooa7aBMK9g/3l50bqiMeHUcBK0hdWPoZgbRHcOK\n" \
                                    "cNIcbDBy9FeVpYRYtQNh0HKR/B/JmwajegGWGVy1tw3t+JTFsdFh2XbBELvfHvfg\n" \
                                    "W/RRHIaupD+t9GELZNWs2NigOvy0vXXC1rivVvQM6YX3qO0TLwuX0c9jUixK1bga\n" \
                                    "tZy8GLMoeI6jMPDWi1pGEBvtKTHLryWU3WOTr+9UH6Sqh0nf9ErcMHX9GchesjIW\n" \
                                    "EOyQWeVRx/xzGL9d76Wtnl5r07k666G9+6XyoOiPtdc2C6kRBD+RvgHC2iLGiRfW\n" \
                                    "6Su5234VUz5HbGmwRKnfYJiJwmfiSNyP7K6WTDaefczyziN6rY7IpfbM+VysP2xz\n" \
                                    "57inDRvuJCgGSoW0o3zCRSwSpNrf6W6I0HWbD3D7kiuVwukXEYoQUqIaCWjD0+yR\n" \
                                    "ps8Oq/JDBlTqjMY3TbwOEkw0LJaeFtVp9vyz1JLzpTYWAjGJJHZEX1pjgRk2JCHK\n" \
                                    "+Muo8WEv0pW82h0UxlgUkYYdSEItjmPkCDdIyZRCuMoPci1wS4kvlIKjsKoydZJP\n" \
                                    "fR/nifcvaEWGuGHzpzi6kVefmfrB+BvHBvkwSz0Q2xeGkcx46CYpoQ6OvWj0sz7v\n" \
                                    "mQqh574xfKPrJcFmIs/CYpzeh/eCMzYVEKQ/BPhpji2AiLnqjFy25kSw21kNClPP\n" \
                                    "N5uEso3u8YlILmnyfIzA78riIz1EukMinrNQRHMirAeCtuSzfgeE0zUjWZnL1Xus\n" \
                                    "-----END RSA PRIVATE KEY-----\n"
                            elif 'ssh_key_data' in an_asset['inputs'] and an_asset['inputs']['ssh_key_data'] == '':
                                self.log_warn("*** Setting ssh key for {} to some random default".format(asset_name))
                                an_asset['inputs']['ssh_key_data'] = "-----BEGIN RSA PRIVATE KEY-----\n" \
                                    "MIIEowIBAAKCAQEA0TNd16gyE0o4end0fpUZGMuseXyggUZiFsvkzSgwqMks4Rws\n" \
                                    "khN59Wzz3F1FPPDzUKu3x2DRDMPH8Js7YMaFXE+EY20dP75gPrykWeGZoyJWcWMf\n" \
                                    "PjITj7veNwrYsGxvPZd7qUg4WVo5rVrKiMtLaVAdQdqNiF/lQNCxwyew7HMj6Hkg\n" \
                                    "WpR9XbdSE8SnS8j9R+FA4B2u6oy/FxDRDs5Rq866Tv782kqxG1vcdwTeuc4kWVji\n" \
                                    "zpsOkZ7Ur1pXiyFoAOJ2sDCIja0/D9u+4ey4s+pLCZpeY8NVFu9P4rKKcNJ5O3e0\n" \
                                    "d8nNxHckXALp3nnEVgKGojNhWM1gPQR0PQREBwIDAQABAoIBACosjNKZGd9Bqzkl\n" \
                                    "M9sA+9o/1Tl4onLtWYD3Ad1KKOUeCWooX+PjAUc0+8SFGRw8BxFQTPBo2DwWjAw5\n" \
                                    "fzL3UpNVhH721Fqxan27Ufa8wFhe58ZcEURcnAzx9s5p5V1LvvFPxKJP6Ow6gD4u\n" \
                                    "e34wXbeRaxSHltjTXEhAylVpfwVro0xo9TokAgz3+xAW5d4343aYFrSU2ExrP79U\n" \
                                    "UQaW60OSkHCJ2Dx5hT/u8qJx4rsR8Zjv7PKwMC5qvy1jRwL6E0guIftJP+fT4Ijj\n" \
                                    "dY6yyCiKEYXyhOFO2R2kSGmNMtpiNm1jITTCNQzm4v6McXD6GP1HiviHNKv5MfVZ\n" \
                                    "TWxwj6ECgYEA+mXdCqLIHE7cAn7do5GEtwZYDlt9LgjT+yIDRPahoJTrXPtF4sFf\n" \
                                    "o31wFWjQ/WvtIl80DT7heBbL5Hdql6ppqzFe08T5rf9VoccozghCqGaawDN1nob6\n" \
                                    "dv9vt0UYV/Z5yMMG2a5abBUQDywgtDczGadz5/5qBIfAu3c2J49HmMMCgYEA1eGM\n" \
                                    "eXwYaHrIPnOdWLqynAGaTQML/Hpqe1zA9xKsOsSenfvdg7EumrnRr580ejQiVO3y\n" \
                                    "L83wj5vcrFI9onWpbsvr6qlFrEO1d156ZF5sn8cHRHYdGWJotsmAQP/FNGxzzOw0\n" \
                                    "HiQgrbwxN/WIdWmrE1N6Ys3oQ5DWvXKUWW7rU20CgYEAyAxvz5qDs5IRVfETlCWj\n" \
                                    "WTI5UacoWIn3CfF/mS5NrOStMYkSqXoCtbR2wrQOHBmIx+g1xstRCUd1OB9ryqX8\n" \
                                    "bCgycZAyRh/zwx9Ba3HQB4iJ5Dp4ouGF42JqV4pdS5GAdLPTmkAgv68IOIbxzek3\n" \
                                    "6ywMfvGUs+/dPCie3HYtJk8CgYAe586ip1nnjwZsb8xmy+OPQ3QGeNA8lXvZg5em\n" \
                                    "nB4jB9Jbxc9Gfk3bscoo9HpixjHHz/JVEg8W0VDb3a5mUVZAWlsmt3sH32jTbOWG\n" \
                                    "p1ZO6DWWoPKnfl7fOtK7kbnvT1SUYfVN/a5zLGR4T5R+UtyTmFZw/Iv5Z26ARZRG\n" \
                                    "MA71KQKBgEvMsDIWGl47l12UJ6KBwzV4c5WVjzKf7GUpbsLIyv71pNgfXkhLF6Nf\n" \
                                    "OKb4Dr4esKGodApTIj3dlsU88E1g7zD5jRuHYutbnCen1TEN91DtGgWkeYSuk9/z\n" \
                                    "mZ1uQonJSPmz97kj5L6i/4UZbTDRiyVOyIq5/lTsE/v7258DzKQe\n" \
                                    "-----END RSA PRIVATE KEY-----"

                    # TowerCLI wants extra_vars to be in a list, not a string
                    self.touchup_extra_vars(an_asset)

                    try:
                        existing_object = resource.create(**an_asset)
                        asset_changed = True
                        self.log_change("Created {} {}".format(asset_type, asset_name))
                    except TowerCLIError as e:
                        self.log_error("Failed to create {} {} : {}".format(asset_type, asset_name, e))
                        continue

                else:
                    # First take off the ID
                    object_id = existing_object['id']

                    # Special cases
                    if asset_type == 'project':
                        common.remove_local_path_from_scm_project(an_asset)
                        common.remove_local_path_from_scm_project(existing_object)

                    # This will compare an_asset to existing_object and update an_asset if needed
                    # For example, if the new Tower instance has additional stuff it will make sure it gets removed
                    reduced_object = copy.deepcopy(an_asset)

                    if self.does_asset_need_update(reduced_object, existing_object, post_options):
                        # When reducing an object, there may be fields we need to copy back in.
                        # For example, if the credential type is the same they will be removed from reduced_object
                        # But the API needs the credential type to be set in order to process the request
                        if asset_type == 'credential':
                            if 'credential_type' not in reduced_object:
                                reduced_object['credential_type'] = an_asset['credential_type']

                        # TowerCLI wants extra_vars to be in a list, not a string
                        self.touchup_extra_vars(reduced_object)

                        try:
                            resource.write(pk=object_id, **reduced_object)
                            asset_changed = True
                            self.log_change("Updated asset")
                        except TowerCLIError as e:
                            self.log_error("Failed to update {} {} : {}".format(asset_type, asset_name, e))
                            continue
                    else:
                        self.log_ok("Asset up to date")

                # If there are relations, import them
                if relations is not None:
                    for a_relation in relations:
                        if a_relation == 'survey_spec':
                            survey = tower_cli.get_resource(asset_type).survey(existing_object['id'])
                            if survey != relations[a_relation]:
                                self.log_change("Updating survey")
                                resource.modify(pk=existing_object['id'], survey_spec=relations[a_relation])
                            else:
                                self.log_ok("Survey up to date")
                        elif a_relation == 'workflow_nodes':
                            # In can_object_post, we deep copy the initial set of nodes and add it to the
                            # end of the array This enables us to compare the exported nodes from the target
                            # server to the unresolved nodes in the original import request
                            # This has to be done because the can_object_post method resolves all of the dependencies
                            existing_workflow_nodes = common.extract_workflow_nodes(existing_object)
                            new_workflow_nodes_unresolved = relations[a_relation].pop()

                            if not self.are_workflow_nodes_the_same(
                                    existing_workflow_nodes, new_workflow_nodes_unresolved
                            ):
                                self.import_workflow_nodes(existing_object, relations[a_relation])
                            else:
                                self.log_ok("Workflow nodes up to date")
                        elif a_relation == 'host' or a_relation == 'inventory_source':
                            self.import_inventory_relations(existing_object, relations[a_relation], a_relation)
                        elif a_relation == 'group':
                            self.import_inventory_groups(existing_object, relations[a_relation])
                        elif a_relation in common.NOTIFICATION_TYPES:
                            self.import_notification_relations(existing_object, relations[a_relation], a_relation)
                        elif a_relation == 'extra_credentials':
                            self.import_extra_credentials(existing_object, relations[a_relation])
                        elif a_relation == 'schedules':
                            self.import_schedules(existing_object, relations[a_relation], asset_type)
                        elif a_relation == 'roles':
                            self.import_roles(existing_object, relations[a_relation], asset_type)
                        elif a_relation == 'labels':
                            self.import_labels(existing_object, relations[a_relation], asset_type)
                        else:
                            self.log_error("Relation {} is not supported".format(a_relation))

                # Checking for post update actions on the different objects
                if asset_changed:
                    if asset_type == 'project':
                        try:
                            resource.update(existing_object['id'], wait=True)
                        except CannotStartJob:
                            # Manual projects will raise a CannotStartJob exception
                            pass
                        except JobFailure:
                            self.log_warn("Failed to update project {} : This may cause other errors.".format(
                                existing_object['name'])
                            )

        self.print_recap()

    def get_secret(self, prompt, default_string, default):
        # Generate a random secret
        if self.secret_management == 'random':
            # Generate random string
            import random
            import string
            password = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(12))
            self.log_warn("{} to '{}'".format(default_string, password))
            return password

        # prompt for a secret
        if self.secret_management == 'prompt':
            # Prompt the user
            import getpass
            while True:
                password = getpass.getpass("{}: ".format(prompt))
                password_confirm = getpass.getpass("Enter that again to confirm: ")
                if password == password_confirm:
                    return password
                print("")
                print("Mismatch, please try again")
                print("")

        self.log_warn("{} to '{}'".format(default_string, default))
        return default

    # Takes an object and the post definition and validates that all the bits and pieces are there.
    def can_object_post(self, asset_type, an_asset, post_options):

        # Somethings might not have post_options, if so we can't check them so just return no errors
        if post_options is None:
            return True

        post_check_succeeded = True
        if common.get_identity(asset_type) not in an_asset:
            return False

        name = an_asset[common.get_identity(asset_type)]

        # First, make sure that all of the required options were given to us
        # We have to do this first because later we are going to delete
        # required to make sure we are not missing an option
        for option in post_options:
            if "required" not in post_options[option]:
                self.log_error("Required is not defined for {}\n{}".format(
                    option, json.dumps(post_options[option], indent=4)
                ))
                post_check_succeeded = False
                continue

            if "required" in post_options[option] and post_options[option]["required"] and option not in an_asset:
                self.log_error("{} is required but is not defined for {} {}".format(option, asset_type, name))
                post_check_succeeded = False

        # Next check to make sure that any entries that the user gave us is actually an option for the post method
        for option in an_asset:
            # We know these do not matter
            if option == common.ASSET_TYPE_KEY or option == common.ASSET_RELATION_KEY:
                continue

            if option not in post_options:
                self.log_error("Option {} is not a valid option for {} {}".format(option, asset_type, name))
                post_check_succeeded = False
                continue

            # If there is a max_length make sure the size is right
            if "max_length" in post_options[option]:
                if len(an_asset[option]) > post_options[option]["max_length"]:
                    self.log_error("Option {} has exceeded max length of {} for {} {}".format(
                        option, post_options[option]["max_length"], asset_type, name
                    ))
                    post_check_succeeded = False

            # If it is an option check to make sure that the value matches
            if "choices" in post_options[option]:
                valid_choice = False
                # Choices is an array like [ [ value, label ], [value, label], ... ]
                valid_options = []
                for a_choice in post_options[option]["choices"]:
                    value = a_choice[0]
                    label = a_choice[1]
                    valid_options.append(value)
                    valid_options.append(label)

                    if an_asset[option] == label:
                        an_asset[option] = value
                        valid_choice = True
                    elif an_asset[option] == value:
                        valid_choice = True

                if not valid_choice:
                    self.log_error("Value {} is not a valid choice for option {} for {} {}".format(
                        an_asset[option], option, asset_type, name
                    ))
                    post_check_succeeded = False

            # This is intended for development to let me know if there is another kind of check we need to perform
            # The notification_configuration of notification_template has a funky thing where it lists
            # additional options for notification types
            if option == 'notification_configuration' and asset_type == 'notification_template':
                continue
            # We will remove the remaining "known" types of checks and then see if there is anything left
            known_types = ["help_text", "default", "required", "type", "label", "max_length",
                           "choices", "min_value", "max_value", "filterable"]
            if len(set(post_options[option].keys()).difference(known_types)) > 0:
                self.log_warn("BUG, unknown keys for option {} found in asset type of {}:\n{}".format(
                    option, asset_type, json.dumps(post_options[option], indent=4)
                ))

        # Now lets check for any related assets
        if common.ASSET_RELATION_KEY in an_asset:
            for relation in an_asset[common.ASSET_RELATION_KEY]:
                if relation == 'survey_spec':
                    # TODO
                    # Someday we could try and check all of the fields at some point
                    pass
                elif relation == "workflow_nodes":
                    # We need to take a copy of the original workflow nodes so that (if we pass this check)
                    # we can check to see if they have actually changed
                    # If we validate we just append the initial list as the last item in the list
                    initial_nodes = copy.deepcopy(an_asset[common.ASSET_RELATION_KEY][relation])
                    self.validate_workflow_nodes(an_asset[common.ASSET_RELATION_KEY][relation])
                    an_asset[common.ASSET_RELATION_KEY][relation].append(initial_nodes)
                elif relation == 'host':
                    host_api_options = common.get_api_options('host')
                    for host in an_asset[common.ASSET_RELATION_KEY][relation]:
                        # We have to add an inventory for a host to validate
                        # The export process will remove the inventory field because we
                        # know what inventory we are tied to
                        host['inventory'] = 1
                        self.can_object_post('host', host, host_api_options)
                        # Now we want to remove it because below we are going to extract existing inventories
                        # and compare them to the new inventories. The extracted inventories will not have
                        # the inventory field
                        del host['inventory']
                elif relation == 'group':
                    group_api_options = common.get_api_options('group')
                    for group in an_asset[common.ASSET_RELATION_KEY][relation]:
                        # We have to add an inventory for the group to validate the export process will remove
                        # the inventory field because we know what inventory we are tied to
                        group['inventory'] = 1
                        # Now we need to take the sub_groups and hosts off of the inventory
                        # These are not valid fields for a group
                        sub_groups = group.pop('sub_groups', None)
                        hosts = group.pop('hosts', None)

                        # Next check the group
                        self.can_object_post('group', group, group_api_options)

                        # Finally, remove the inventory field and add back any sub_groups or hosts
                        del group['inventory']
                        if sub_groups is not None:
                            group['sub_groups'] = sub_groups
                        if hosts is not None:
                            group['hosts'] = hosts

                elif relation in common.NOTIFICATION_TYPES:
                    for notification_name in an_asset[common.ASSET_RELATION_KEY][relation]:
                        if 'notification_template' in self.sorted_assets and\
                                notification_name in self.sorted_assets['notification_template']:
                            continue

                        try:
                            tower_cli.get_resource('notification_template').get(**{'name': notification_name})
                        except TowerCLIError:
                            self.log_error("Unable to resolve {} {}".format(relation, notification_name))
                            post_check_succeeded = False

                elif relation == 'inventory_source':
                    # TODO
                    # Someday we could go and try to resolve inventory projects or scripts
                    pass

                elif relation == 'extra_credentials':
                    for credential in an_asset[common.ASSET_RELATION_KEY][relation]:
                        if 'credential' in self.sorted_assets and credential in self.sorted_assets['credential']:
                            continue
                        try:
                            tower_cli.get_resource('credential').get(**{'name': credential})
                        except TowerCLIError:
                            self.log_error("Unable to resolve extra_credential {}".format(credential))
                            post_check_succeeded = False

                elif relation == 'schedules':
                    for schedule in an_asset[common.ASSET_RELATION_KEY][relation]:
                        # A unified job template is required to post a schedule
                        # But the exported schedules won't have a template
                        # So we are going to add one, check it and then remove it
                        schedule['unified_job_template'] = 1
                        self.can_object_post('schedules', schedule, common.get_api_options('schedules'))
                        del schedule['unified_job_template']

                elif relation == 'roles':
                    for role in an_asset[common.ASSET_RELATION_KEY][relation]:
                        # For each role we are going to look at each user and team
                        # And make sure that the user/team is either defined in Tower
                        # or is specified as something to import
                        for actor in ACTOR_FIELDS:
                            if actor in role:
                                for item in role[actor]:
                                    if actor in self.sorted_assets and item in self.sorted_assets[actor]:
                                        continue
                                    try:
                                        identity_field = common.get_identity(actor)
                                        existing_item = tower_cli.get_resource(actor).list(**{identity_field: item})
                                        if existing_item['count'] != 1:
                                            raise TowerCLIError("Unable to find user")
                                        continue
                                    except TowerCLIError:
                                        pass

                                    self.log_error("Unable to resolve {} name {} to add roles".format(actor, item))
                                    post_check_succeeded = False

                elif relation == 'labels':
                    for label in an_asset[common.ASSET_RELATION_KEY][relation]:
                        # Make sure it can post, this will also validate that the label has an org
                        self.can_object_post('label', label, common.get_api_options('label'))

                        # We also need to manually check the name (the post options don't include that)
                        if 'name' not in label:
                            self.log_error("Label is missing a name")
                            post_check_succeeded = False

                        # Now lets make sure that the org resolves
                        try:
                            tower_cli.get_resource('organization').get(**{'name': label['organization']})
                        except TowerCLIError:
                            self.log_error("Unable to resolve organization {} for label {}".format(
                                label['organization'], label['name']))
                            post_check_succeeded = False

                else:
                    self.log_warn("WARNING: Relation {} is not checked".format(relation))

        return post_check_succeeded

    def prep_and_sort_all_assets(self, import_json, prevent, exclude):
        self.sorted_assets = {}
        had_sort_issues = False
        for asset in import_json:
            if common.ASSET_TYPE_KEY not in asset:
                self.log_error("Object is missing an asset type")
                had_sort_issues = True
                continue

            asset_type = asset[common.ASSET_TYPE_KEY]

            # If we don't have a valid asset_type add an error and return
            if asset_type not in common.SEND_ORDER:
                self.log_error("Asset type of {} is invalid".format(asset_type))
                had_sort_issues = True
                continue

            # Make sure we are able to import this asset type
            if prevent is not None and asset_type in prevent:
                self.log_error("Asset of type {} is prevented from importation".format(asset_type))
                had_sort_issues = True
                continue

            # Make sure we want to import this asset type
            if exclude is not None and asset_type in exclude:
                self.log_ok("Asset of type {} is prevented from importation".format(asset_type))
                continue

            # Make sure the object has its identifier field
            identifier = common.get_identity(asset_type)
            if identifier not in asset:
                self.log_error("Asset of type {} is missing identifier field {}".format(asset_type, identifier))
                had_sort_issues = True
                continue

            # If everything validates we can delete the ASSET_TYPE_KEY
            del asset[common.ASSET_TYPE_KEY]

            # We made it here so the asset should be ok to try and import so add it to a list to import
            if asset_type not in self.sorted_assets:
                self.sorted_assets[asset_type] = []
            self.sorted_assets[asset_type].append(asset)

        # If we got any errors when sorting the assets raise an exception
        if had_sort_issues:
            raise TowerCLIError("One or more errors encountered in provided assets, stopping import")

    def get_all_objects(self, source):
        all_objects = []

        # First we are going to read everything from stdin
        self.get_assets_from_std_in(all_objects)

        # Now read all of the files passed in
        self.get_assets_from_files(source, all_objects)

        return all_objects

    def get_assets_from_std_in(self, assets):
        # If stdin is a TTY then we didn't get stuff passed to us so we can just return []
        if sys.stdin.isatty():
            return

        stdin = click.get_text_stream('stdin')
        stdin_lines = ''.join(stdin.readlines())

        # If we didn't get anything from stdin we can just return
        if not stdin_lines or stdin_lines is None or stdin_lines == '':
            return

        try:
            # parser.string_to_dict
            stdin_input = parser.string_to_dict(stdin_lines, require_dict=False)

            # If this is a list append each item in the list
            # Otherwise just append the item
            if type(stdin_input) == list:
                for asset in stdin_input:
                    assets.append(asset)
            else:
                assets.append(stdin_input)

        except Exception as e:
            self.log_error("Read from stdin failed to parse {}".format(e))

    def get_assets_from_files(self, input_files, assets):
        files = []
        for a_source in input_files:
            if os.path.isfile(a_source):
                files.append(a_source)
            elif os.path.isdir(a_source):
                for aFile in os.listdir(a_source):
                    # When loading a directory only load JSON or YAML files
                    if not aFile.endswith(".json") and not aFile.endswith(".yml") and not aFile.endswith(".yaml"):
                        continue
                    files.append("{}/{}".format(a_source.rstrip("/"), aFile))
            else:
                self.log_error("{} is not a file or directory".format(a_source))

        # Loop over all of the files were were given
        for fileName in files:
            # Open then and try to read the json and then close the file
            with open(fileName, 'r') as f:
                try:
                    loaded_assets = parser.string_to_dict(f, require_dict=False)
                except Exception as e:
                    self.log_error("Unable to load json from {} : {}".format(fileName, e))
                    continue
                finally:
                    try:
                        f.close()
                    except IOError:
                        pass

            # If we got a json object instead of an array make an array of one item
            if type(loaded_assets) != list:
                loaded_assets = [loaded_assets]

            # loop over all of the items in the file
            for asset in loaded_assets:
                assets.append(asset)

    # Takes an asset and loops over the defined dependences
    # These are things that may be other objects in Tower
    # For example, a credential can be tied to an Organization
    # If the user gave me an Organization like Default (which is what is expected)
    # we need to resolve that to Defaults ID
    def resolve_asset_dependencies(self, asset_type, an_asset):
        resolution_succeeded = True
        # Loop through the list of dependencies for this asset_type
        for a_dependency in tower_cli.get_resource(asset_type).dependencies:
            # This the asset we are building does not have the dependency defined we can move on
            if a_dependency not in an_asset:
                continue

            dependency_type = a_dependency
            # A job template might contain vault_credential which is really just a credential
            if a_dependency == 'vault_credential':
                dependency_type = 'credential'

            identifier = common.get_identity(dependency_type)
            try:
                dependency_object = tower_cli.get_resource(dependency_type).get(**{identifier: an_asset[a_dependency]})
                an_asset[a_dependency] = dependency_object["id"]
            except TowerCLIError:
                self.log_error("Failed to resolve {} {} for {} {}".format(
                    a_dependency, an_asset[a_dependency], asset_type, an_asset[identifier])
                )
                resolution_succeeded = False

        return resolution_succeeded

    # If an asset exists, this function is called
    # This function will decide if we need to actually update it or not
    # The three cases we want to catch:
    #    1)  A property is defined in the input that is not defined in the the target (set the property on the target)
    #    2)  A property is defined in the target that is not defined in the input  (remove the property on the target)
    #    3)  A property is defined in both but has different values (set the property on the target)
    def does_asset_need_update(self, an_asset, existing_object, post_options):
        needs_update = False

        # Create an empty object and strip out the "junk" from the existing_object
        reduced_existing_object = {}
        common.map_node_to_post_options(post_options, existing_object, reduced_existing_object)

        # Remove any encrypted objects because the passed object will likely not have them either
        common.remove_encrypted_values(reduced_existing_object)

        # Loop over each of the properties
        # This will check for condition 2 and 3
        for object_property in reduced_existing_object:
            # if the object_property is in the existing object and the object_property has changed than
            # we need to update.
            # Otherwise we can just remove the property from anObject

            if object_property in an_asset:
                if object_property == 'extra_vars':
                    # If we are extra_vars we want to convert ourselves into a dict for the comparison.
                    # Extra vars can be either JSON or YAML and can be displayed in the UI either way.
                    # This will make sure that if someone simply changes the display from JSON to YAML it won't
                    # update the object if they are still the same.
                    # This also resolves issues where the JSON may have a ' instead of a "
                    existing_extra_vars_dict = parser.string_to_dict(reduced_existing_object[object_property])
                    new_extra_vars_dict = parser.string_to_dict(an_asset[object_property])

                    if existing_extra_vars_dict != new_extra_vars_dict:
                        self.log_change("Need to update extra_vars from:")
                        for line in reduced_existing_object[object_property].split("\n"):
                            self.log_change("\t{}".format(line))
                        self.log_change("To:")
                        for line in an_asset[object_property].split("\n"):
                            self.log_change("\t{}".format(line))
                        needs_update = True
                    else:
                        del an_asset[object_property]
                elif reduced_existing_object[object_property] == an_asset[object_property]:
                    del an_asset[object_property]
                else:
                    self.log_change("Need to update property {} from '{}' to '{}'".format(
                        object_property, reduced_existing_object[object_property], an_asset[object_property]
                    ))
                    needs_update = True
            else:
                needs_update = True
                # There is a object_property in the existing object that is NOT in the new object, we need to add a
                # new default value to existing object
                self.log_change("Removing property {}".format(object_property))
                # Assume the default value is nothing but try to get a default value out of the post_options
                default_value = ''
                if object_property in post_options and 'default' in post_options[object_property]:
                    default_value = post_options[object_property]['default']
                an_asset[object_property] = default_value

        # Now check for condition 1
        for object_property in an_asset:
            if object_property not in reduced_existing_object:
                needs_update = True
                self.log_change("Adding property {}".format(object_property))

        return needs_update

    def import_workflow_nodes(self, workflow, new_nodes):
        # Get the existing workflow nodes
        query_params = [("workflow_job_template", workflow['id'])]
        existing_nodes = tower_cli.get_resource('node').list(**{
            "query": query_params,
            'fail_on_multiple_results': False,
            'all_pages': True
        })

        # Now delete the existing nodes
        node_errors = False
        if existing_nodes['count'] > 0:
            self.log_change("Deleting existing workflow nodes")
            for node in existing_nodes['results']:
                try:
                    tower_cli.get_resource('node').delete(node['id'])
                except TowerCLIError as e:
                    node_errors = True
                    self.log_error("Unable to delete existing workflow node: {}".format(e))

        # if we failed to remove an old node don't try to import, that could leave a real mess
        if node_errors:
            return

        node_name_to_id_map = {}

        # Loop over all of the nodes to import just the nodes
        self.log_change("Building new workflow nodes")
        for node in new_nodes:
            # Build an object with the workflow_job_template
            node_to_import = {'workflow_job_template': workflow['id']}

            # Suck in all of the values from the node
            for option in node:
                if option != 'name' and option not in tower_cli.get_resource('workflow').workflow_node_types:
                    node_to_import[option] = node[option]

            # Nodes may have credentials or inventories in them. If so, we need to resolve them
            for lookup_type in ['credential', 'inventory']:
                if lookup_type in node_to_import:
                    try:
                        item = self.get_item_by_name(lookup_type, node_to_import[lookup_type])
                        node_to_import[lookup_type] = item['id']
                    except TowerCLIError as e:
                        self.log_error("Failed to resolve {} {} : {}".format(
                            lookup_type, node_to_import[lookup_type], e
                        ))
                        node_errors = True
            # If we could not resolve something, continue
            if node_errors:
                continue

            # Build an asset for this node
            try:
                built_node = tower_cli.get_resource("node").create(**node_to_import)
            except TowerCLIError as e:
                self.log_error("Failed to create new workflow node : {}".format(e))
                node_errors = True
                continue

            # If it failed gawk
            if built_node is None:
                self.log_error("Failed to create new workflow node")
                node_errors = True
                continue

            node_name_to_id_map[node['name']] = built_node['id']

        # If we failed to build all of the nodes, don't try to order them
        if node_errors:
            return

        self.log_change("Building workflow node relations")
        # Now that all of the nodes are built we need to define their relations
        for node in new_nodes:
            for relation_type in tower_cli.get_resource('workflow').workflow_node_types:
                if relation_type in node:
                    for relation in node[relation_type]:
                        post_data = {'id': node_name_to_id_map[relation]}
                        node_id = node_name_to_id_map[node['name']]

                        response = client.post(
                            'workflow_job_template_nodes/{}/{}/'.format(node_id, relation_type),
                            post_data
                        )
                        if response.status_code != 204:
                            self.log_error("Failed to link {} to {} for {} ({})".format(
                                relation, relation_type, node['name'], response.status_code
                            ))

    def validate_workflow_nodes(self, nodes):
        self.log_ok("Checking on workflow_nodes")

        # Loop over each node
        for a_node in nodes:
            # Make sure we have the correct things:
            if 'name' not in a_node:
                self.log_error("Workflow node is not named")
                continue

            if 'unified_job_type' not in a_node or 'unified_job_name' not in a_node:
                self.log_error("Node {} is missing unified_job_name or unified_job_type".format(a_node['name']))
                continue

            # Validate the unified job type
            if a_node['unified_job_type'] == 'job':
                job_type = 'job'
            elif a_node['unified_job_type'] == 'project_update':
                job_type = 'project'
            elif a_node['unified_job_type'] == 'inventory_update':
                job_type = 'inventory'
            elif a_node['unified_job_type'] == 'workflow_job':
                job_type = 'workflow'
            else:
                self.log_error('Node {} has an invalid unified job type {}'.format(
                    a_node['name'], a_node['unified_job_type']
                ))
                continue

            # Lookup the unified job
            job_name = a_node['unified_job_name']
            unified_job_results = client.request(
                'get',
                "unified_job_templates",
                {'name': job_name, 'type__contains': job_type}
            )

            # If it failed, move on

            if unified_job_results.status_code != 200:
                self.log_error("Unable to lookup unified job template {}/{} for {} ({})".format(
                    job_type, job_name, a_node['name'], unified_job_results.status_code
                ))
                continue

            possible_unified_jobs = unified_job_results.json()

            # If we got 0 or >1 move on

            if possible_unified_jobs['count'] == 0:
                self.log_error("Could not find a unified job for {}/{}".format(job_type, job_name))
                continue
            elif possible_unified_jobs['count'] > 1:
                self.log_error("Found more than one unified job for {}/{}".format(job_type, job_name))
                continue

            # This will be the node we end up importing
            a_node['unified_job_template'] = possible_unified_jobs['results'][0]['id']
            del a_node['unified_job_type']
            del a_node['unified_job_name']

    def import_extra_credentials(self, existing_object, new_creds):
        # Credentials are just an array of names
        # So importing these can be done very easily by comparing new_creds vs existing_creds
        existing_creds_data = common.extract_extra_credentials(existing_object)
        existing_creds = existing_creds_data['items']
        existing_name_to_id = existing_creds_data['existing_name_to_id_map']
        if existing_creds == new_creds:
            self.log_ok("All extra creds are up to date")
            return

        # Creds to remove is the difference between new_creds and existing_creds
        for cred in list(set(existing_creds).difference(new_creds)):
            try:
                tower_cli.get_resource('job_template').disassociate_credential(
                    existing_object['id'], existing_name_to_id[cred]
                )
                self.log_change("Removed extra credential {}".format(cred))
            except TowerCLIError as e:
                self.log_error("Unable to remove extra credential {} : {}".format(cred, e))

        # Creds to add is the difference between existing_creds and extra_creds
        for cred in list(set(new_creds).difference(existing_creds)):
            try:
                new_credential = tower_cli.get_resource('credential').get(**{'name': cred})
            except TowerCLIError as e:
                self.log_error("Unable to resolve extra credential {} : {}".format(cred, e))
                continue

            try:
                tower_cli.get_resource('job_template').associate_credential(existing_object['id'], new_credential['id'])
                self.log_change("Added extra credential {}".format(cred))
            except TowerCLIError as e:
                self.log_error("Unable to add extra credential {} : ".format(cred, e))

    def import_labels(self, existing_object, new_labels, asset_type):
        existing_labels_data = common.extract_labels(existing_object)
        existing_labels = existing_labels_data['items']
        existing_name_to_object = existing_labels_data['existing_name_to_object_map']
        # Existing_name_to_object is a dict of dicts because labels live in an organization
        if existing_labels == new_labels:
            self.log_ok("All labels are up to date")
            return

        keyword_arg_template_id = "job_template"
        if asset_type == 'workflow':
            keyword_arg_template_id = "workflow_job_template"

        for existing_label in existing_labels:
            # Any label that is in existing_labels that is not in new_labels needs to be removed
            if existing_label not in new_labels:
                try:
                    label_name = existing_label['name']
                    label_org = existing_label['organization']
                    label_id = existing_name_to_object[label_org][label_name]['id']
                    tower_cli.get_resource(asset_type).disassociate_label(**{
                        keyword_arg_template_id: existing_object['id'],
                        'label': label_id,
                    })
                    self.log_change("Removed label {}".format(label_name))
                except TowerCLIError as e:
                    self.log_error("Unable to remove label {} : {}".format(label_name, e))
            else:
                # If the label is in both new_labels and existing_labels we don't need to do anything with it.
                new_labels.remove(existing_label)

        # Any labels left in new_labels need to be added
        for new_label in new_labels:
            label_name = new_label['name']
            label_org_name = new_label['organization']
            # We need to resolve the organization of this new label
            # This is check in post checks so this should never fail.
            # Unless someone was able to delete an org between the post check and now.
            try:
                org = tower_cli.get_resource('organization').get(**{'name': label_org_name})
                label_org_id = org['id']
            except TowerCLIError as e:
                self.log_error("Failed to lookup organization {} for label {} : {}".format(
                    label_org_name, label_name, e
                ))
                continue

            try:
                new_label['organization'] = label_org_id
                created_label = tower_cli.get_resource('label').create(**new_label)
                self.log_change("Added label {}".format(label_name))
            except TowerCLIError as e:
                self.log_error("Unable to build new label {} : {}".format(label_name, e))
                continue

            try:
                tower_cli.get_resource(asset_type).associate_label(**{
                    keyword_arg_template_id: existing_object['id'],
                    'label': created_label['id'],
                })
            except TowerCLIError as e:
                self.log_error("Unable to add label {} : {}".format(label_name, e))

    def import_schedules(self, existing_object, new_schedules, asset_type):
        existing_schedules_data = common.extract_schedules(existing_object)
        existing_schedules = existing_schedules_data['items']
        existing_name_to_object = existing_schedules_data['existing_name_to_object_map']
        if existing_schedules == new_schedules:
            self.log_ok("All schedules are up to date")
            return

        # Loop over all of the new schedules
        for schedule in new_schedules:
            schedule_name = schedule['name']

            # If the name of the new schedule is not in the existing_name_to_id we can just create it
            if schedule_name not in existing_name_to_object:
                try:
                    # For creating we need to add a unified_job_template to the schedule
                    schedule[asset_type] = existing_object['id']
                    tower_cli.get_resource('schedule').create(**schedule)
                    self.log_change("Added schedule {}".format(schedule_name))
                except TowerCLIError as e:
                    self.log_error("Failed to add schedule {} : {}".format(schedule_name, e))

            else:
                # The schedule_name is in the existing_name_to_id

                # See if we need to change it
                if schedule == existing_name_to_object[schedule_name]:
                    self.log_ok("Schedule {} is up to date".format(schedule_name))
                else:
                    # We need to update the schedule
                    try:
                        existing_id = existing_name_to_object[schedule_name]['id']
                        tower_cli.get_resource('schedule').get(existing_id).update(schedule)
                        self.log_change("Updated schedule {}".format(schedule_name))
                    except TowerCLIError as e:
                        self.log_error("Failed to modify schedule {} : {}".format(schedule_name, e))

                # Delete this from the existing schedules so we don't delete it
                del existing_name_to_object[schedule_name]

        # Now we need to delete any schedules which were previous added but no longer need to be
        for schedule_name in existing_name_to_object:
            try:
                tower_cli.get_resource('schedule').delete(existing_name_to_object[schedule_name]['id'])
                self.log_change("Removed existing schedule named {}".format(schedule_name))
            except TowerCLIError as e:
                self.log_error("Failed to delete schedule {} : {}".format(schedule_name, e))

    def import_roles(self, existing_asset, new_roles, asset_type):
        existing_role_data = common.extract_roles(existing_asset)
        existing_roles = existing_role_data['items']
        existing_name_to_id = existing_role_data['existing_name_to_object_map']

        if new_roles == existing_roles:
            self.log_ok("All roles are up to date")
            return

        existing_roles_by_name = {}
        for role in existing_roles:
            existing_roles_by_name[role['name']] = role

        # Loop over all of the new roles
        for role in new_roles:
            # There should never be an instance where the target item does not have the same roles
            # But just in case
            if role['name'] not in existing_roles_by_name:
                self.log_error("Role {} does not exist on the target node".format(role['name']))
                continue

            for actor in ACTOR_FIELDS:
                existing_items = existing_roles_by_name[role['name']][actor]
                new_items = role[actor]

                # Get the existing role via CLI
                try:
                    existing_role = tower_cli.get_resource('role').get(existing_name_to_id['role'][role['name']])
                except TowerCLIError as e:
                    self.log_error('Failed to find existing role by ID : {}'.format(e))
                    continue

                # Items to remove is the difference between new_items and existing_items
                for item_to_remove in list(set(existing_items).difference(new_items)):
                    # Get the user or team
                    try:
                        existing_item = tower_cli.get_resource(actor).get(**{
                            common.get_identity(actor): item_to_remove
                        })
                    except TowerCLIError as e:
                        self.log_error("Failed to get {} {} : {}".format(actor, item_to_remove, e))
                        continue

                    # Revoke the permissions
                    try:
                        role_type = self.get_role_type(existing_role['type'], existing_role['name'])

                        tower_cli.get_resource('role').revoke(**{
                            'type': role_type,
                            actor: existing_item['id'],
                            asset_type: existing_asset['id'],
                        })
                        self.log_change("Removed {} {} from {} role".format(actor, item_to_remove, role['name']))
                    except TowerCLIError as e:
                        self.log_error("Unable to remove {} {} from {} role: {}".format(
                            actor, item_to_remove, role['name'], e)
                        )

                # Items that need to be added is the difference between existing_items and new_items
                for item_to_add in list(set(new_items).difference(existing_items)):
                    # Get the user or team
                    try:
                        existing_item = tower_cli.get_resource(actor).get(**{
                            common.get_identity(actor): item_to_add
                        })
                    except TowerCLIError as e:
                        self.log_error("Failed to get {} {} : {}".format(actor, item_to_add, e))
                        continue

                    # Grant the permissions
                    try:
                        role_type = self.get_role_type(existing_role['type'], existing_role['name'])

                        tower_cli.get_resource('role').grant(**{
                            'type': role_type,
                            actor: existing_item['id'],
                            asset_type: existing_asset['id'],
                        })
                        self.log_change("Added {} {} to {} role".format(actor, item_to_add, role['name']))
                    except TowerCLIError as e:
                        self.log_error("Unable to add {} {} to {} role: {}".format(
                            actor, item_to_add, role['name'], e)
                        )

    def get_role_type(self, type, name):
        role_type = type
        if role_type == 'Ad Hoc':
            role_type = 'adhoc'
        # Some of the workflow roles come out funky so we need to straighten them out.
        elif role_type == 'role' and name == 'Read':
            role_type = 'read'
        elif role_type == 'role' and name == 'Admin':
            role_type = 'admin'
        elif role_type == 'role' and name == 'Execute':
            role_type = 'execute'
        return role_type

    def import_inventory_groups(self, existing_object, groups):
        existing_groups_data = common.extract_inventory_groups(existing_object)
        existing_groups = existing_groups_data['items']
        existing_name_to_id = existing_groups_data['existing_name_to_id_map']

        self.import_sub_groups(groups, existing_groups, existing_name_to_id, existing_object, None)

    def import_sub_groups(self, groups, existing_groups, existing_name_to_id, inventory, parent_project):
        if existing_groups == groups:
            if parent_project is None:
                self.log_ok("All inventory groups are up to date")
            return

        # Loop over all of the new groups
        for group in groups:
            if 'name' not in group:
                self.log_error("Unable to manage group due to name field missing")
                continue

            group_name = group['name']

            # See if we have the group
            existing_group = None
            for a_group in existing_groups:
                if a_group['name'] == group_name:
                    existing_group = a_group

            # if we found the group in the existing groups then we can process it for update
            if existing_group is not None:
                # Get the group out of the existing_name_to_id nodes

                # Compare and sync the nodes
                self.process_group_comparison(existing_group, group, existing_name_to_id[group_name], inventory)
                # Delete the node from the existing group dict
                # Later we wil delete any groups left in the existing group dic
                del existing_name_to_id[group_name]
                continue

            # If the group isn't in the the existing group dict we can build it
            self.add_group(inventory=inventory, parent=parent_project, group=group)

        # Finally if anything is left in the existing group than it needs to be removed
        for group_name in existing_name_to_id:
            try:
                tower_cli.get_resource('group').delete(existing_name_to_id[group_name]['id'])
                self.log_change("Deleted {} from {}".format(group_name, inventory['name']))
            except TowerCLIError as e:
                self.log_error("Unable to remove group {} from {} : {}".format(group_name, inventory['name'], e))

    def process_group_comparison(self, existing_group, new_group, existing_group_ids, inventory):
        # First remove the sub_groups and hosts from the group
        existing_sub_groups = existing_group.pop('sub_groups', None)
        new_sub_groups = new_group.pop('sub_groups', None)
        existing_hosts = existing_group.pop('hosts', None)
        new_hosts = new_group.pop('hosts', None)

        # Try to get the group ID of the existing group

        # First check the group itself
        if not self.does_asset_need_update(new_group, existing_group, common.get_api_options('group')):
            self.log_ok("Group {} is up to date".format(existing_group['name']))
        else:
            try:
                tower_cli.get_resource('group').write(pk=existing_group_ids['id'], **new_group)
                self.log_change("Updated group {}".format(existing_group['name']))
            except TowerCLIError as e:
                self.log_error("Unable to upgrade group {} : {}".format(existing_group['name'], e))

        # Next lets compare the hosts
        if existing_hosts != new_hosts:
            # existing_hosts and new _hosts are just lists of names, we don't need to compare properties
            for host_name in (set(existing_hosts) | set(new_hosts)):
                # Get the host object to get the ID
                try:
                    host = tower_cli.get_resource('host').get(**{'name': host_name})
                except TowerCLIError as e:
                    self.log_error("Unable to find host name {} to disassociate from the group {} : {}".format(
                        host_name, existing_group['name'], e
                    ))
                    continue

                # If the host is not in the new_hosts, we can remove it
                if host_name not in new_hosts:
                    # Disassociate the host to the group
                    try:
                        tower_cli.get_resource('group')._disassoc('hosts', existing_group_ids['id'], host['id'])
                        self.log_change("Removed host {} from group {}".format(host_name, existing_group['name']))
                    except TowerCLIError as e:
                        self.log_error(
                            "Unable to remove host {} from group {} : {}".format(host_name, existing_group['name'], e)
                        )

                # If the host is not in the existing_hosts, we can add it
                if host_name not in existing_hosts:
                    # Associate the hosts to the group
                    try:
                        tower_cli.get_resource('group')._assoc('hosts', existing_group_ids['id'], host['id'])
                        self.log_change("Added host {} to group {}".format(host_name, existing_group['name']))
                    except TowerCLIError as e:
                        self.log_error(
                            "Unable to add host {} to group {} : {}".format(host_name, existing_group['name'], e))

        # Next lets compare the sub_groups groups
        existing_group['id'] = existing_group_ids['id']
        self.import_sub_groups(
            new_sub_groups,
            existing_sub_groups,
            existing_group_ids['sub_groups'],
            inventory,
            existing_group
        )

    def add_group(self, inventory=None, parent=None, group=None):
        # Extract the hosts and sub_groups
        hosts = group.pop('hosts', None)
        sub_groups = group.pop('sub_groups', None)

        # Add in an inventory
        if parent is None:
            group['inventory'] = inventory['id']
        else:
            group['parent'] = parent['id']

        try:
            new_group = tower_cli.get_resource('group').create(**group)
            if parent is None:
                self.log_change("Added group {}".format(group['name']))
            else:
                self.log_change("Added group {} to {}".format(group['name'], parent['name']))
        except TowerCLIError as e:
            self.log_error("Unable to create group named {} : {}".format(group['name'], e))
            return

        for host_name in hosts:
            # Get the host by name
            try:
                host = tower_cli.get_resource('host').get(**{'name': host_name})
            except TowerCLIError as e:
                self.log_error("Unable to find host name {} to associate to the group {} : {}".format(
                    host_name, group['name'], e
                ))
                continue

            # Associate the host to the group
            try:
                tower_cli.get_resource('group')._assoc('hosts', new_group['id'], host['id'])
                self.log_change("Added host {} to group {}".format(host_name, group['name']))
            except TowerCLIError as e:
                self.log_error("Unable to associate host {} to group {} : {}".format(host_name, group['name'], e))

        for sub_group in sub_groups:
            self.add_group(inventory=inventory, parent=new_group, group=sub_group)

    def import_inventory_relations(self, existing_object, new_relations, relation_type):
        existing_relation_data = common.extract_inventory_relations(existing_object, relation_type)
        existing_relations = existing_relation_data['items']
        existing_name_to_id = existing_relation_data['existing_name_to_id_map']

        if existing_relations == new_relations:
            # If there was nothing in the input we don't need to print the message
            self.log_ok("All inventory {} are up to date".format(relation_type))
            return

        # Now we are going to put both of the existing_hosts and new_hosts into a dict by name
        existing_relations_dict = {}
        for relation in existing_relations:
            existing_relations_dict[relation['name']] = relation

        new_relations_dict = {}
        for relation in new_relations:
            new_relations_dict[relation['name']] = relation

        # Now we are going to do the comparison
        for relation_name in new_relations_dict:
            new_schedules = None
            if 'schedules' in new_relations_dict[relation_name]:
                new_schedules = new_relations_dict[relation_name]['schedules']
                del new_relations_dict[relation_name]['schedules']

            existing_schedules = []
            if relation_name in existing_relations_dict:
                if 'schedules' in existing_relations_dict[relation_name]:
                    existing_schedules = existing_relations_dict[relation_name]['schedules']
                if not self.does_asset_need_update(
                        new_relations_dict[relation_name],
                        existing_relations_dict[relation_name],
                        common.get_api_options(relation_type)
                ):
                    self.log_ok("{} {} is up to date".format(relation_type, relation_name))
                else:
                    try:
                        # Resolve the source project (if needed)
                        self.resolve_inventory_sub_items(new_relations_dict[relation_name], relation_type)

                        tower_cli.get_resource(relation_type).write(
                            pk=existing_name_to_id[relation_name], **new_relations_dict[relation_name]
                        )
                        self.log_change("Updated node {} in {}".format(relation_name, existing_object['name']))
                    except TowerCLIError as e:
                        self.log_error("Unable to update {} {} from {} : {}".format(
                            relation_type, relation_name, existing_object['name'], e
                        ))

                # Since we have processed this existing relation remove it from the dict
                del existing_relations_dict[relation_name]
            else:
                # Resolve the source project (if needed)
                try:
                    self.resolve_inventory_sub_items(new_relations_dict[relation_name], relation_type)
                except TowerCLIError as e:
                    self.log_error(e)
                    continue

                # add the inventory ID into the relation object
                new_relations_dict[relation_name]['inventory'] = existing_object['id']
                try:
                    tower_cli.get_resource(relation_type).create(**new_relations_dict[relation_name])
                except TowerCLIError as e:
                    self.log_error("Unable to create {} named {} : {}".format(relation_type, relation_name, e))

            if new_schedules is not None:

                if new_schedules == existing_schedules:
                    self.log_ok("Schedules are up to date")
                else:
                    for a_schedule in new_schedules:
                        if a_schedule in existing_schedules:
                            self.log_ok("Schedule {} is up to date".format(a_schedule['name']))
                            existing_schedules.remove(a_schedule)
                        else:
                            try:
                                # We have to look up the inventory_source ID to use for this schedule
                                inventory_source = tower_cli.get_resource('inventory_source').get(
                                    **{'name': relation_name}
                                )
                                # Since we are in this method we know we are working on an inventory
                                a_schedule['inventory_source'] = inventory_source['id']

                                # Now we can create the schedule
                                tower_cli.get_resource('schedule').create(**a_schedule)
                                self.log_change("Added schedule {}".format(a_schedule['name']))
                            except TowerCLIError as e:
                                self.log_error("Unable to add schedule {} : {}".format(a_schedule['name'], e))

                    for a_schedule in existing_schedules:
                        try:
                            tower_cli.get_resource('schedule').delete(**{'name': a_schedule['name']})
                            self.log_change("Removed schedule {}".format(a_schedule['name']))
                        except TowerCLIError as e:
                            self.log_error("Unable to remove schedule {} : {}".format(a_schedule['name'], e))

        for relation_name in existing_relations_dict:
            # We have to add in the inventory field in order to delete this
            existing_relations_dict[relation_name]['inventory'] = existing_object['id']
            try:
                tower_cli.get_resource(relation_type).delete(existing_name_to_id[relation_name])
                self.log_change("Deleted {} from {}".format(relation_name, existing_object['name']))
            except TowerCLIError as e:
                self.log_error("Unable to remove {} {} from {} : {}".format(
                    relation_type, relation_name, existing_object['name'], e
                ))

    def resolve_inventory_sub_items(self, item, relation_type):
        if relation_type == 'inventory_source':
            resolve_errors = []
            if 'source_project' in item:
                try:
                    project = tower_cli.get_resource('project').get(**{'name': item['source_project']})
                    item['source_project'] = project['id']
                except TowerCLIError as e:
                    resolve_errors.append(
                        "Unable to resolve project {} as source project for inventory source {} : {}".format(
                            item['source_project'], item['name'], e
                        )
                    )

            if 'source_script' in item:
                try:
                    script = tower_cli.get_resource('inventory_script').get(**{'name': item['source_script']})
                    item['source_script'] = script['id']
                except TowerCLIError as e:
                    resolve_errors.append(
                        "Unable to resolve script {} as source script for inventory source {} : {}".format(
                            item['source_script'], item['name'], e
                        )
                    )

            if 'credential' in item:
                try:
                    credential = tower_cli.get_resource('credential').get(**{'name': item['credential']})
                    item['credential'] = credential['id']
                except TowerCLIError as e:
                    resolve_errors.append(
                        "Unable to resolve credential {} as credential for inventory source {} : {}".format(
                            item['credential'], item['name'], e
                        )
                    )

            if len(resolve_errors) > 0:
                raise TowerCLIError("\n".join(resolve_errors))

    def import_notification_relations(self, asset, new_notifications, notification_type):
        if 'related' not in asset or notification_type not in asset['related']:
            self.log_error("The requested notification type {} is not defined in the asset relations".format(
                notification_type
            ))
            return

        # Get the existing notifications
        existing_notifications = common.extract_notifications(asset, notification_type)

        if existing_notifications == new_notifications:
            # if we don't have any notifications don't print a message.
            if len(new_notifications) != 0:
                self.log_ok("All {} up to date".format(notification_type))
            return

        for notification_name in new_notifications:
            # If the notification is already in the existing_notifications we don't need to do anything
            # Just remove it from the existing notifications so we dont delete it
            if notification_name in existing_notifications:
                del existing_notifications[notification_name]
                continue

            try:
                notification = self.get_item_by_name('notification_template', notification_name)
            except TowerCLIError as e:
                self.log_error("Unable to add notification to {} : {}".format(notification_type, e))
                continue

            try:
                client.post(asset['related'][notification_type], {'id': notification['id']})
                self.log_change("Added notification {} to type {}".format(notification_name, notification_type))
            except Exception as e:
                self.log_error("Unable to add notification {} : {}".format(notification_name, e))

        # finally disassociate the remaining existing_notifications
        for notification_name in existing_notifications:
            try:
                notification = self.get_item_by_name('notification_template', notification_name)
            except TowerCLIError as e:
                # We should never get here because the credential better be defined in the existing tower instance.
                self.log_error("Unable to remove notification from {} : {}".format(notification_type, e))
                continue

            try:
                client.post(
                    asset['related'][notification_type],
                    {'id': notification['id'], 'disassociate': notification['id']}
                )
                self.log_change("Removed existing notification {} from {}".format(notification_name, notification_type))
            except Exception as e:
                self.log_error("Unable to remove existing notification {} : {}".format(notification_name, e))

    def get_item_by_name(self, asset_type, name):
        # Get a list of items by name
        item_response = tower_cli.get_resource(asset_type).list(**{'name': name})

        if 'count' not in item_response:
            raise TowerCLIError("Unable to get listing of {}".format(asset_type))

        if 'count' in item_response and item_response['count'] == 0:
            raise TowerCLIError("{} named {} does not exist".format(asset_type, name))

        if 'count' in item_response and item_response['count'] != 1:
            raise TowerCLIError("{} named {} is not unique".format(asset_type, name))

        return item_response['results'][0]

    def are_workflow_nodes_the_same(self, existing_nodes, new_nodes):
        existing_tree = self.expand_nodes(existing_nodes)
        new_tree = self.expand_nodes(new_nodes)

        nodes_are_the_same = True
        for node in existing_tree:
            if node not in new_tree:
                nodes_are_the_same = False

        for node in new_tree:
            if node not in existing_tree:
                nodes_are_the_same = False

        # with open("./existing_nodes.json", 'w') as outfile:
        #     json.dump(existing_tree, outfile, indent=4)
        # with open("./new_nodes.json", 'w') as outfile:
        #     json.dump(new_tree, outfile, indent=4)

        return nodes_are_the_same

    def expand_nodes(self, node_list):
        # First extract the nodes into hashes
        leafs_by_name = {}
        for node in node_list:
            leafs_by_name[node['name']] = copy.deepcopy(node)
            del leafs_by_name[node['name']]['name']

        # Now expand all of the child nodes
        for node in node_list:
            # Get the node name so we can reference it in the leaf hash
            node_name = node['name']

            # For each of the node types
            for node_type in tower_cli.get_resource('workflow').workflow_node_types:
                # In the leaf, remove the node_type array
                leafs_by_name[node_name][node_type] = []

                # Now, add the nodes of that type to the array
                for child_node_name in node[node_type]:
                    leafs_by_name[node_name][node_type].append(leafs_by_name[child_node_name])

        return leafs_by_name

    def touchup_extra_vars(self, asset):
        if 'extra_vars' in asset:
            if type(asset['extra_vars']) == str:
                asset['extra_vars'] = [asset['extra_vars']]

    def set_password_in_custom_credential(self, credential, asset_name):
        credential_type_id = credential['credential_type']

        # Get the credential type object
        if credential_type_id not in self.credential_type_objects:
            credential_type_object = tower_cli.get_resource('credential_type').get(credential_type_id)
            self.credential_type_objects[credential_type_id] = credential_type_object
        else:
            credential_type_object = self.credential_type_objects[credential_type_id]

        if 'managed_by_tower' in credential_type_object and credential_type_object['managed_by_tower']:
            return

        for field in credential_type_object['inputs']['fields']:
            # If the field is in the required list
            if field['id'] in credential_type_object['inputs']['required']:
                # If the field is a secret
                if 'secret' in field and field['secret']:
                    credential['inputs'][field['id']] = self.get_secret(
                        'Enter {} for {}'.format(field['label'], asset_name),
                        "Setting {} for {}".format(field['id'], asset_name),
                        'password'
                    )
