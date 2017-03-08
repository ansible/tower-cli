# Copyright 2016, Ansible by Red Hat.
# Aaron Tan <sitan@redhat.com>
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

import click

from tower_cli import models
from tower_cli.utils import types, exceptions as exc


UNIFIED_JT = {
    'job_template': '/job_templates',
    'inventory_source': '/inventory_sources',
    'project': '/projects',
}
CLICK_ATTRS = ('__click_params__', '_cli_command', '_cli_command_attrs')


def jt_aggregate(func, is_create=False, has_pk=False):
    """Decorator to aggregate unified_jt-related fields.

    Args:
        func: The CURD method to be decorated.
        is_create: Boolean flag showing whether this method is create.
        has_pk: Boolean flag showing whether this method uses pk as argument.

    Returns:
        A function with necessary click-related attributes whose keyworded
        arguments are aggregated.

    Raises:
        exc.UsageError: Either more than one unified jt fields are
            provided, or none is provided when is_create flag is set.
    """
    def helper(kwargs, obj):
        """The helper function preceding actual function that aggregates
        unified jt fields.
        """
        unified_job_template = None
        for item in UNIFIED_JT:
            if kwargs.get(item, None) is not None:
                jt_id = kwargs.pop(item)
                if unified_job_template is None:
                    unified_job_template = (item, jt_id)
                else:
                    raise exc.UsageError(
                        'More than one unified job template fields provided, '
                        'please tighten your criteria.'
                    )
        if unified_job_template is not None:
            kwargs['unified_job_template'] = unified_job_template[1]
            obj.identity = tuple(list(obj.identity) + ['unified_job_template'])
            return '/'.join([UNIFIED_JT[unified_job_template[0]],
                             str(unified_job_template[1]), 'schedules/'])
        elif is_create:
            raise exc.UsageError('You must provide exactly one unified job'
                                 ' template field during creation.')

    def decorator_without_pk(obj, *args, **kwargs):
        old_endpoint = obj.endpoint
        new_endpoint = helper(kwargs, obj)
        if is_create:
            obj.endpoint = new_endpoint
        result = func(obj, *args, **kwargs)
        obj.endpoint = old_endpoint
        return result

    def decorator_with_pk(obj, pk=None, *args, **kwargs):
        old_endpoint = obj.endpoint
        new_endpoint = helper(kwargs, obj)
        if is_create:
            obj.endpoint = new_endpoint
        result = func(obj, pk=pk, *args, **kwargs)
        obj.endpoint = old_endpoint
        return result

    decorator = decorator_with_pk if has_pk else decorator_without_pk
    for item in CLICK_ATTRS:
        setattr(decorator, item, getattr(func, item, []))
    decorator.__doc__ = func.__doc__

    return decorator


class Resource(models.Resource):
    cli_help = 'Manage schedules within Ansible Tower.'
    endpoint = '/schedules/'

    # General fields.
    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)

    # Unified jt fields. note these fields will only be used during creation.
    # Plus, one and only one field should be provided.
    job_template = models.Field(type=types.Related('job_template'),
                                required=False, display=False)
    inventory_source = models.Field(type=types.Related('inventory_source'),
                                    required=False, display=False)
    project = models.Field(type=types.Related('project'), required=False,
                           display=False)

    # Schedule-specific fields.
    unified_job_template = models.Field(required=False, type=int,
                                        help_text='Integer used to display'
                                        ' unified job template in result, '
                                        'Please don\'t use it for create/'
                                        'modify.')
    enabled = models.Field(required=False, type=click.BOOL, default=True,
                           help_text='Whether this schedule will be used',
                           show_default=True)
    rrule = models.Field(required=False, display=False,
                         help_text='Schedule rules specifications which is'
                         ' less than 255 characters.')
    extra_data = models.Field(type=types.Variables(), required=False,
                              display=False, help_text='Extra data for '
                              'schedule rules in the form of a .json file.')

    def _get_patch_url(self, url, pk):
        urlTokens = url.split('/')
        if len(urlTokens) > 3:
            # reconstruct url to prevent a rare corner case where resources
            # cannot be constructed independently. Open to modification if
            # API convention changes.
            url = '/'.join(urlTokens[:1] + urlTokens[-2:])
        return super(Resource, self)._get_patch_url(url, pk)


Resource.create = jt_aggregate(Resource.create, is_create=True)
Resource.delete = jt_aggregate(Resource.delete, has_pk=True)
Resource.get = jt_aggregate(Resource.get, has_pk=True)
Resource.list = jt_aggregate(Resource.list)
Resource.modify = jt_aggregate(Resource.modify, has_pk=True)
