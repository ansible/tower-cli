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

import yaml
from tower_cli.utils import exceptions as exc


def string_to_dict(var_string):
    """Returns a dictionary given a string with yaml or json syntax.
    If data is not present in a key: value format, then it return
    an empty dictionary."""
    try:
        return_dict = yaml.load(var_string)
        assert type(return_dict) is dict
    except (ValueError, AssertionError):
        return_dict = {}
    except yaml.YAMLError as e:
        raise exc.TowerCLIError('failed to parse some of the extra '
                                'variables.\nvariables: \n%s' % var_string)
    return return_dict


def load_from_file(filename):
    """Returns the content of the file, filename"""
    with open(filename, 'r') as f:
        filetext = f.read()
    return filetext


def file_or_yaml_split(extra_vars_opt):
    """If the input text starts with @, then it is treated as a file name
    and the contents of the file are returned."""
    if extra_vars_opt.startswith("@"):
        # Argument is a YAML file (JSON is a subset of YAML)
        return load_from_file(extra_vars_opt[1:])
    else:
        # Argument is a YAML list of definitions by itself
        return extra_vars_opt


def load_extra_vars(extra_vars_list):
    """Similar to the Ansible core routine by the same name, this returns
    a dictionary with variables defined in all yaml, json, or file references
    given in the input list. Also handles precidence order."""
    extra_vars = {}
    for extra_vars_opt in extra_vars_list:
        cleaned_text = file_or_yaml_split(extra_vars_opt)
        data = string_to_dict(cleaned_text)
        extra_vars.update(data)
    return extra_vars


def extra_vars_loader_wrapper(extra_vars_list):
    """Specific to tower-cli, this specifically avoids doing processing
    of the extra_vars list if there is only one element in it. In that case,
    it will be sufficient to allow Tower to process the syntax
    and return its own response."""
    # If there is only one set of extra_vars, then pass it  to the API
    # without alteration
    extra_vars_dict = load_extra_vars(extra_vars_list)
    if len(extra_vars_list) == 1:
        return file_or_yaml_split(extra_vars_list[0])
    # For a list of extra_vars, combine them into a single input
    else:
        return yaml.dump(extra_vars_dict)
