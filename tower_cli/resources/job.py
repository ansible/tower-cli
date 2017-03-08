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

from __future__ import absolute_import, unicode_literals
from copy import copy
from getpass import getpass
from distutils.version import LooseVersion

import click

from tower_cli import models, get_resource, resources
from tower_cli.api import client
from tower_cli.utils import debug, types
from tower_cli.utils import parser


PROMPT_LIST = [
    'limit', 'tags', 'skip_tags', 'job_type', 'inventory', 'credential'
]


class Resource(models.ExeResource):
    """A resource for jobs.

    This resource has ordinary list and get methods,
    but it does not have create or modify.
    Instead of being created, a job is launched.
    """
    cli_help = 'Launch or monitor jobs.'
    endpoint = '/jobs/'

    job_template = models.Field(
        key='-J',
        type=types.Related('job_template'), required=False, display=True
    )
    job_explanation = models.Field(required=False, display=False)
    created = models.Field(required=False, display=True)
    status = models.Field(required=False, display=True)
    elapsed = models.Field(required=False, display=True)

    @resources.command(
        use_fields_as_options=('job_template', 'job_explanation')
    )
    @click.option('--monitor', is_flag=True, default=False,
                  help='If sent, immediately calls `job monitor` on the newly '
                       'launched job rather than exiting with a success.')
    @click.option('--wait', is_flag=True, default=False,
                  help='Monitor the status of the job, but do not print '
                       'while job is in progress.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided with --monitor, this command (not the job)'
                       ' will time out after the given number of seconds. '
                       'Does nothing if --monitor is not sent.')
    @click.option('--no-input', is_flag=True, default=False,
                  help='Suppress any requests for input.')
    @click.option('-e', '--extra-vars', required=False, multiple=True,
                  help='yaml format text that contains extra variables '
                       'to pass on. Use @ to get these from a file.')
    @click.option('--limit', required=False,
                  help='Specify host limit for job template to run.')
    @click.option('--tags', required=False,
                  help='Specify tagged actions in the playbook to run.')
    @click.option('--skip-tags', required=False,
                  help='Specify tagged actions in the playbook to ommit.')
    @click.option('--job-type', required=False, type=click.Choice(['run',
                  'check', 'scan']), help='Specify job type for job template'
                  ' to run.')
    @click.option(
        '--inventory', required=False, type=types.Related('inventory'),
        help='Specify inventory for job template to run.'
    )
    @click.option(
        '--credential', required=False, type=types.Related('credential'),
        help='Specify machine credential for job template to run.'
    )
    @click.option('--use-job-endpoint', required=False, default=False,
                  is_flag=True, help='A flag that disable launching jobs'
                  ' from job template when set.')
    def launch(self, job_template=None, monitor=False, wait=False,
               timeout=None, no_input=True, extra_vars=None, **kwargs):
        """Launch a new job based on a job template.

        Creates a new job in Ansible Tower, immediately starts it, and
        returns back an ID in order for its status to be monitored.
        """
        # Get the job template from Ansible Tower.
        # This is used as the baseline for starting the job.

        tags = kwargs.get('tags', None)
        use_job_endpoint = kwargs.pop('use_job_endpoint', False)
        jt_resource = get_resource('job_template')
        jt = jt_resource.get(job_template)

        # Update the job data by adding an automatically-generated job name,
        # and removing the ID.
        data = copy(jt)
        data['job_template'] = data.pop('id')
        data['name'] = '%s [invoked via. Tower CLI]' % data['name']
        if tags:
            data['job_tags'] = tags

        # Initialize an extra_vars list that starts with the job template
        # preferences first, if they exist
        extra_vars_list = []
        if 'extra_vars' in data and len(data['extra_vars']) > 0:
            # But only do this for versions before 2.3
            debug.log('Getting version of Tower.', header='details')
            r = client.get('/config/')
            if LooseVersion(r.json()['version']) < LooseVersion('2.4'):
                extra_vars_list = [data['extra_vars']]

        # Add the runtime extra_vars to this list
        if extra_vars:
            extra_vars_list += list(extra_vars)  # accept tuples

        # If the job template requires prompting for extra variables,
        # do so (unless --no-input is set).
        if data.pop('ask_variables_on_launch', False) and not no_input \
                and not extra_vars:
            # If JT extra_vars are JSON, echo them to user as YAML
            initial = parser.process_extra_vars(
                [data['extra_vars']], force_json=False
            )
            initial = '\n'.join((
                '# Specify extra variables (if any) here as YAML.',
                '# Lines beginning with "#" denote comments.',
                initial,
            ))
            extra_vars = click.edit(initial) or ''
            if extra_vars != initial:
                extra_vars_list = [extra_vars]

        # Data is starting out with JT variables, and we only want to
        # include extra_vars that come from the algorithm here.
        data.pop('extra_vars', None)

        # Replace/populate data fields if prompted.
        modified = set()
        for resource in PROMPT_LIST:
            if data.pop('ask_' + resource + '_on_launch', False) \
               and not no_input or use_job_endpoint:
                resource_object = kwargs.get(resource, None)
                if type(resource_object) == types.Related:
                    resource_class = get_resource(resource)
                    resource_object = resource_class.get(resource).\
                        pop('id', None)
                if resource_object is None:
                    if not use_job_endpoint:
                        debug.log('{0} is asked at launch but not provided'.
                                  format(resource), header='warning')
                elif resource != 'tags':
                    data[resource] = resource_object
                    modified.add(resource)

        # Dump extra_vars into JSON string for launching job
        if len(extra_vars_list) > 0:
            data['extra_vars'] = parser.process_extra_vars(
                extra_vars_list, force_json=True
            )

        # In Tower 2.1 and later, we create the new job with
        # /job_templates/N/launch/; in Tower 2.0 and before, there is a two
        # step process of posting to /jobs/ and then /jobs/N/start/.
        supports_job_template_launch = False
        if 'launch' in jt['related']:
            supports_job_template_launch = True

        # Create the new job in Ansible Tower.
        start_data = {}
        if supports_job_template_launch and not use_job_endpoint:
            endpoint = '/job_templates/%d/launch/' % jt['id']
            if 'extra_vars' in data and len(data['extra_vars']) > 0:
                start_data['extra_vars'] = data['extra_vars']
            if tags:
                start_data['job_tags'] = data['job_tags']
            for resource in PROMPT_LIST:
                if resource in modified:
                    start_data[resource] = data[resource]
        else:
            debug.log('Creating the job.', header='details')
            job = client.post('/jobs/', data=data).json()
            job_id = job['id']
            endpoint = '/jobs/%d/start/' % job_id

        # There's a non-trivial chance that we are going to need some
        # additional information to start the job; in particular, many jobs
        # rely on passwords entered at run-time.
        #
        # If there are any such passwords on this job, ask for them now.
        debug.log('Asking for information necessary to start the job.',
                  header='details')
        job_start_info = client.get(endpoint).json()
        for password in job_start_info.get('passwords_needed_to_start', []):
            start_data[password] = getpass('Password for %s: ' % password)

        # Actually start the job.
        debug.log('Launching the job.', header='details')
        self._pop_none(kwargs)
        kwargs.update(start_data)
        job_started = client.post(endpoint, data=kwargs)

        # If this used the /job_template/N/launch/ route, get the job
        # ID from the result.
        if supports_job_template_launch and not use_job_endpoint:
            job_id = job_started.json()['job']

        # If returning json indicates any ignored fields, display it in
        # verbose mode.
        ignored_fields = job_started.json().get('ignored_fields', {})
        has_ignored_fields = False
        for key, value in ignored_fields.items():
            if value and value != '{}':
                if not has_ignored_fields:
                    debug.log('List of ignored fields on the server side:',
                              header='detail')
                    has_ignored_fields = True
                debug.log('{0}: {1}'.format(key, value))

        # Get some information about the running job to print
        result = self.status(pk=job_id, detail=True)
        result['changed'] = True

        # If we were told to monitor the job once it started, then call
        # monitor from here.
        if monitor:
            return self.monitor(job_id, timeout=timeout)
        elif wait:
            return self.wait(job_id, timeout=timeout)

        return result
