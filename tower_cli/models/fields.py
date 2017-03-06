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

import six


_field_counter = 0


class Field(object):
    """A class representing flags on a given field on a model.
    This class tracks whether a field is unique, filterable, read-only, etc.
    """
    def __init__(self, key=None, type=six.text_type, default=None,
                 display=True, filterable=True, help_text=None,
                 is_option=True, password=False, read_only=False,
                 required=True, show_default=False, unique=False,
                 multiple=False, col_width=None):
        # Init the name to blank.
        # What's going on here: This is set by the ResourceMeta metaclass
        # when the **resource** is instantiated.
        # Essentially, in any normal situation, it's safe to expect it
        # to be set and non-empty.
        self.name = ''

        # Save properties of this field.
        self.key = key
        self.type = type
        self.display = display
        self.default = default
        self.help_text = help_text
        self.is_option = is_option
        self.filterable = filterable
        self.password = password
        self.read_only = read_only
        self.required = required
        self.show_default = show_default
        self.unique = unique
        self.multiple = multiple
        self.no_lookup = False
        self.col_width = col_width

        # If this is a password, display is always off.
        if self.password:
            self.display = False

        # Track the creation history of each field, for sorting reasons.
        global _field_counter
        self.number = _field_counter
        _field_counter += 1

    def __lt__(self, other):
        return self.number < other.number

    def __gt__(self, other):
        return self.number > other.number

    def __repr__(self):
        return '<Field: %s (%s)>' % (self.name, ', '.join(self.flags))

    @property
    def flags(self):
        try:
            flags_list = [self.type.__name__.replace('unicode', 'str')]
        except AttributeError:
            flags_list = [type(self.type).__name__.replace('unicode', 'str')]
        if self.read_only:
            flags_list.append('read-only')
        if self.unique:
            flags_list.append('unique')
        if not self.filterable:
            flags_list.append('not filterable')
        if not self.required:
            flags_list.append('not required')
        return flags_list

    @property
    def help(self):
        """Return the help text that was passed to the constructor, or a
        sensible default if none was provided.
        """
        if self.help_text:
            return self.help_text
        return 'The %s field.' % self.name

    @property
    def option(self):
        """Return the field name as a bash option string
        (e.g. "--field-name").
        """
        return '--' + self.name.replace('_', '-')
