# Copyright 2017 Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
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

import functools
from tower_cli.utils import types

import click


def unified_job_template_options(method):
    """
    Adds the decorators for all types of unified job templates,
    and if the non-unified type is specified, converts it into the
    unified_job_template kwarg.
    """
    jt_dec = click.option(
        '--job-template', type=types.Related('job_template'),
        help='Use this job template as unified_job_template field')
    prj_dec = click.option(
        '--project', type=types.Related('project'),
        help='Use this project as unified_job_template field')
    inv_src_dec = click.option(
        '--inventory-source', type=types.Related('inventory_source'),
        help='Use this inventory source as unified_job_template field')

    def ujt_translation(_method):
        def _ujt_translation(*args, **kwargs):
            for fd in ['job_template', 'project', 'inventory_source']:
                if fd in kwargs and kwargs[fd] is not None:
                    kwargs['unified_job_template'] = kwargs.pop(fd)
            return _method(*args, **kwargs)
        return functools.wraps(_method)(_ujt_translation)

    return ujt_translation(
        inv_src_dec(
            prj_dec(
                jt_dec(
                    method
                )
            )
        )
    )
