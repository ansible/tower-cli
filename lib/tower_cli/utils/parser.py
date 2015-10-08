# Copyright 2015, Ansible, Inc.
# Alan Rominger <arominger@ansible.com>
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
import json

import ast
import shlex
import sys

from tower_cli.utils import exceptions as exc


def parse_kv(var_string):
    """Similar to the Ansible function of the same name, parses file
    with a key=value pattern and stores information in a dictionary,
    but not as fully featured as the corresponding Ansible code."""
    return_dict = {}

    # Output updates dictionaries, so return empty one if no vals in
    if var_string is None:
        return {}

    # Python 2.6 / shlex has problems handling unicode, this is a fix
    fix_encoding_26 = False
    if sys.version_info < (2, 7) and '\x00' in shlex.split(u'a')[0]:
        fix_encoding_26 = True

    # Also hedge against Click library giving non-string type
    if fix_encoding_26 or not isinstance(var_string, str):
        var_string = str(var_string)

    # Use shlex library to split string by quotes, whitespace, etc.
    for token in shlex.split(var_string):

        # Second part of fix to avoid passing shlex unicode in py2.6
        if fix_encoding_26:
            token = unicode(token)
        # Look for key=value pattern, if not, process as raw parameter
        if '=' in token:
            (k, v) = token.split('=')
            # If '=' are unbalanced, then stop and warn user
            if len(k) == 0 or len(v) == 0:
                raise Exception
            # If possible, convert into python data type, for instance "5"->5
            try:
                return_dict[k] = ast.literal_eval(v)
            except:
                return_dict[k] = v
        else:

            # If there are spaces in the statement, there would be no way
            # split it from the rest of the text later, so check for that here
            if " " in token:
                token = '"' + token + '"'
            # Append the value onto the special key entry _raw_params
            # this uses a space delimiter
            if '_raw_params' in return_dict:
                return_dict['_raw_params'] += " " + token
            else:
                return_dict['_raw_params'] = token

    return return_dict


def string_to_dict(var_string):
    """Returns a dictionary given a string with yaml or json syntax.
    If data is not present in a key: value format, then it return
    an empty dictionary.

    Attempts processing string by 3 different methods in order:
        1. as JSON      2. as YAML      3. as custom key=value syntax
    Throws an error if all of these fail in the standard ways."""
    try:
        # Accept all valid "key":value types of json
        return_dict = json.loads(var_string)
        assert type(return_dict) is dict
    except (TypeError, AttributeError, ValueError, AssertionError):
        try:
            # Accept all valid key: value types of yaml
            return_dict = yaml.load(var_string)
            assert type(return_dict) is dict
        except (AttributeError, yaml.YAMLError, AssertionError):
            # if these fail, parse by key=value syntax
            try:
                return_dict = parse_kv(var_string)
            except:
                raise exc.TowerCLIError(
                    'failed to parse some of the extra '
                    'variables.\nvariables: \n%s' % var_string
                )
    return return_dict


def file_or_yaml_split(extra_vars_opt):
    """If the input text starts with @, then it is treated as a file name
    and the contents of the file are returned."""
    if extra_vars_opt and extra_vars_opt.startswith("@"):
        # Argument is a file with variables in it, so return its content
        with open(extra_vars_opt[1:], 'r') as f:
            filetext = f.read()
        return filetext
    else:
        # Argument is a list of definitions by itself
        return extra_vars_opt


def revised_update(dict1, dict2):
    """Updates dict1 with dict2 while appending the elements in _raw_params"""
    if '_raw_params' in dict2 and '_raw_params' in dict1:
        dict1['_raw_params'] += " " + str(dict2.pop('_raw_params'))
    return dict1.update(dict2)


def load_extra_vars(extra_vars_list):
    """Similar to the Ansible core function by the same name, this returns
    a dictionary with variables defined in all yaml, json, or file references
    given in the input list. Also handles precedence order."""
    # Initialize cumulative dictionary
    extra_vars = {}
    for extra_vars_opt in extra_vars_list:
        # Load file content if necessary
        cleaned_text = file_or_yaml_split(extra_vars_opt)
        # Convert text markup to a dictionary
        data = string_to_dict(cleaned_text)
        # Combine dictionary with cumulative dictionary
        revised_update(extra_vars, data)
    return extra_vars


def extra_vars_loader_wrapper(extra_vars_list):
    """Specific to tower-cli, this avoids altering the extra_vars list
    if there is only one element in it. This keeps comments and formatting
    in-tact when passing the information on to the Tower server."""
    # If there is only one set of extra_vars, then pass it  to the API
    # without alteration
    extra_vars_dict = load_extra_vars(extra_vars_list)
    if len(extra_vars_list) == 1:
        return file_or_yaml_split(extra_vars_list[0])
    # For a single string of extra_vars, combine them into a single input
    else:
        return json.dumps(extra_vars_dict)
