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

# returns a dictionary given a yaml or json string
def string_to_dict(var_string):
    try:
        import pdb
        pdb.set_trace()
        return_dict = yaml.load(var_string)
        assert type(return_dict) is dict
    except (ValueError, AssertionError) as e:
        return_dict = {}
    return return_dict

def load_from_file(filename):
    with open(filename, 'r') as f:
        filetext = f.read()
    return string_to_dict(filetext)

def load_extra_vars(extra_vars_list):
    extra_vars = {}
    for extra_vars_opt in extra_vars_list:
        if extra_vars_opt.startswith("@"):
            # Argument is a YAML file (JSON is a subset of YAML)
            data = load_from_file(extra_vars_opt[1:])
        else:
            # Argument is a YAML list of definitions by itself
            data = string_to_dict(extra_vars_opt)
        extra_vars.update(data)
    return extra_vars

def extra_vars_loader_wrapper(extra_vars_list):
    # If there is only one set of extra_vars, then pass it  to the API
    # without alteration
    if len(extra_vars_list) == 1:
        if extra_vars_list[0].startswith("@"):
            return load_from_file(extra_vars_list[0][1:])
        else:
            return extra_vars_list[0]
    # For a list of extra_vars, combine them into a single input
    else:
        extra_vars_dict = load_extra_vars(extra_vars_list)
        return yaml.dump(extra_vars_dict)
