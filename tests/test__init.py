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

import tower_cli

from tests.compat import unittest


class GetResourceTests(unittest.TestCase):
    """Establish that the `tower_cli.get_resource` method works in the
    way that it should.
    """
    def test_get_resource(self):
        for res in ('credential', 'group', 'host', 'inventory', 'job_template',
                    'job', 'organization', 'project', 'team', 'user'):
            tower_cli.get_resource(res)
