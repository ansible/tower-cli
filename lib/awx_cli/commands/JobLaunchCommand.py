# Copyright 2013, AnsibleWorks Inc.
# Michael DeHaan <michael@ansibleworks.com>
# Chris Church <cchurch@ansibleworks.com>
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

import BaseCommand
import awx_cli
import awx_cli.common as common
import datetime
import getpass

class JobLaunchCommand(BaseCommand.BaseCommand):

    """ shows AWX version information """

    def __init__(self, toplevel):
        super(JobLaunchCommand, self).__init__(toplevel)
        self.name = "joblaunch"

    def run(self, args):

        # parse arguments and form connection 
        parser = common.get_parser()
        parser.add_option('-t', '--template', dest='template', 
            default=None, type='int')
        (options, args) = parser.parse_args()
        if options.template is None:
            raise common.BaseException("--template is required")

        # test API connection
        handle = common.connect(options)

        # get the job template
        jt_url = "/api/v1/job_templates/%d/" % options.template
        data = handle.get(jt_url)
        id = data.pop('id')

        # add some more info needed to start the job
        # NOTE: a URL to launch job templates directly
        # may be added later, but this is basically a copy of the job template
        # data to the jobs resource, which is also fine.

        now = str(datetime.datetime.now())
        data.update(dict(
            name = 'cli job invocation started at %s' % now,
            verbosity = 0,
        ))

        # post a new job

        jt_jobs_url = "%sjobs/" % jt_url
        job_result = handle.post(jt_jobs_url, data)

        # get the parameters needed to start the job (if any)
        # prompt for values unless given on command line (FIXME)

        print "URL=%s" % jt_jobs_url

        job_id = job_result['id']
        job_start_url = "/api/v1/jobs/%d/start/" % job_id
        job_start_info = handle.get(job_start_url)
        start_data = {}
        for password in job_start_info.get('passwords_needed_to_start', []):
            value = getpass.getpass('%s: ' % password)
            start_data[password] = value

        # start the job 
        job_start_result = handle.post(job_start_url, start_data)
        print common.dump(job_start_result) 

        # TODO: optional status polling (FIXME)

        return 0

