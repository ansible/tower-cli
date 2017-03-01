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

import types


def command(method=None, **kwargs):
    """Mark this method as a CLI command.

    This will only have any meaningful effect in methods that are members of a
    Resource subclass.
    """
    # Create the actual decorator to be applied.
    # This is done in such a way to make `@resources.command`,
    # `@resources.command()`, and `@resources.command(foo='bar')` all work.
    def actual_decorator(method):
        method._cli_command = True
        method._cli_command_attrs = kwargs
        return method

    # If we got the method straight-up, apply the decorator and return
    # the decorated method; otherwise, return the actual decorator for
    # the Python interpreter to apply.
    if method and isinstance(method, types.FunctionType):
        return actual_decorator(method)
    else:
        return actual_decorator
