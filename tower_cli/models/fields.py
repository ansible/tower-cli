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
import click

from tower_cli.cli import types
from tower_cli.utils import grammar

_field_counter = 0


class BaseField(object):

    def __init__(self):
        # Track the creation history of each field, for sorting reasons.
        global _field_counter
        self.number = _field_counter
        _field_counter += 1

    def __lt__(self, other):
        return self.number < other.number

    def __gt__(self, other):
        return self.number > other.number


class Field(BaseField):
    """A class representing flags on a given field on a model.
    This class tracks whether a field is unique, filterable, read-only, etc.
    """
    def __init__(self, key=None, type=six.text_type, default=None,
                 display=True, filterable=True, help_text=None,
                 is_option=True, password=False, read_only=False,
                 required=True, show_default=False, unique=False,
                 multiple=False, no_lookup=False, col_width=None):
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
        self.no_lookup = no_lookup
        self.col_width = col_width

        # If this is a password, display is always off.
        if self.password:
            self.display = False

        super(Field, self).__init__()

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


class ManyToManyField(BaseField):
    """
    A class that contains utilities for the ResourceMeta metaclass
    to construct two methods for association and disassociation of the field

    :param other_name: tower-cli resource name for related resource.
    :param res_name: tower-cli resource name for primary resource.
                     can be set on initialization of class, if not initially given.
    :param relationship: The API related name for the relationship. Example,
                         "admins" relationship from org->users
    :param method_name: The name CLI alias for the relationship in method names.
    """
    def __init__(self, other_name, res_name=None,
                 relationship=None, method_name=None):
        # If not defined here, the following fields may be set by the
        # resource metaclass:
        # res_name - inferred from the endpoint of the resource
        # relationship - set to the variable name of the field
        # Example:
        # class Foo:
        #   endpoint = '/foos/'
        #   friends = ManyToManyField('bar')
        # in that case, "foo" and "friends" become res_name and relationship

        self.other_name = other_name
        self.res_name = res_name
        self.relationship = relationship
        self.method_name = None
        self._set_method_names(method_name, relationship)

        super(ManyToManyField, self).__init__()

    def __repr__(self):
        return '<ManyToManyField: %s (%s-%s)>' % (
            self.relationship, self.res_name, self.other_name
        )

    def configure_model(self, attrs, field_name):
        '''
        Hook for ResourceMeta class to call when initializing model class.
        Saves fields obtained from resource class backlinks
        '''
        self.relationship = field_name
        self._set_method_names(relationship=field_name)
        if self.res_name is None:
            self.res_name = grammar.singularize(attrs.get('endpoint', 'unknown').strip('/'))

    def _set_method_names(self, method_name=None, relationship=None):
        if self.method_name is not None:
            return  # provided in __init__, do not let metaclass override
        suffix = ''
        if method_name is not None:
            self.method_name = method_name
            if method_name != '':
                suffix = '_{}'.format(method_name)
        elif relationship is not None:
            suffix = '_{}'.format(grammar.singularize(relationship))
        else:
            return
        self.associate_method_name = 'associate{}'.format(suffix)
        self.disassociate_method_name = 'disassociate{}'.format(suffix)

    @property
    def associate_method(self):
        return self._produce_method()

    @property
    def disassociate_method(self):
        return self._produce_method(disassociate=True)

    def _produce_raw_method(self):
        '''
        Returns a callable which becomes the associate or disassociate
        method for the related field.
        Method can be overridden to add additional functionality, but
        `_produce_method` may also need to be subclassed to decorate
        it appropriately.
        '''

        def method(res_self, **kwargs):
            obj_pk = kwargs.get(method._res_name)
            other_obj_pk = kwargs.get(method._other_name)
            internal_method = getattr(res_self, method._internal_name)
            return internal_method(method._relationship, obj_pk, other_obj_pk)

        return method

    def _produce_method(self, disassociate=False):

        method = self._produce_raw_method()

        # Apply options for user to specify the 2 resources to associate
        method = click.option(
            '--{}'.format(self.other_name.replace('_', '-')),
            type=types.Related(self.other_name),
            required=True
        )(method)
        method = click.option(
            '--{}'.format(self.res_name.replace('_', '-')),
            type=types.Related(self.res_name),
            required=True
        )(method)

        # This does the same thing as @resources.command, but without importing
        method._cli_command = True
        method._cli_command_attrs = dict(use_fields_as_options=False)

        # Define field-specific parameters that control functionality
        method._relationship = self.relationship
        method._res_name = self.res_name
        method._other_name = self.other_name
        if disassociate:
            method._internal_name = '_disassoc'
            method.__doc__ = self._produce_doc(action='disassociate')
        else:
            method._internal_name = '_assoc'
            method.__doc__ = self._produce_doc()
        return method

    def _produce_doc(self, action='associate'):
        doc_relation = self.method_name if self.method_name else grammar.singularize(self.relationship)
        return """{title_action} {status_article} {status} with this {res_name}.

        =====API DOCS=====
        {title_action} {status_article} {status} with this {res_name}.

        :param {res_name}: Primary key or name of the {res_name} to {action} to.
        :type {res_name}: str
        :param {other_name}: Primary key or name of the {other_name} to be {action}d.
        :type {other_name}: str
        :returns: Dictionary of only one key "changed", which indicates whether the {action} succeeded.
        :rtype: dict

        =====API DOCS=====
        """.format(
            action=action,
            title_action=action.title(),
            status_article=grammar.article(doc_relation),
            status=doc_relation,
            res_name=self.res_name,
            other_name=self.other_name,
        )
