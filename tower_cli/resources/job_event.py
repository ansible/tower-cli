# Copyright 2018, Red Hat, Inc.
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

from tower_cli import models
from tower_cli.cli import types


class Resource(models.BaseResource):
    """A resource for job events."""
    cli_help = 'View events from jobs.'
    endpoint = '/job_events/'
    internal = True

    job = models.Field(
        type=types.Related('job'), display=True
    )
    host = models.Field(
        type=types.Related('host'), display=True
    )
    parent = models.Field(
        type=types.Related('job_event'), display=False
    )
    event = models.Field()
    playbook = models.Field()
    play = models.Field()
    task = models.Field()
    role = models.Field()
    counter = models.Field(display=False)
    event_level = models.Field(display=False)
    event_data = models.Field(display=False)
    failed = models.Field(display=False, type=bool)
    changed = models.Field(type=bool)
    verbosity = models.Field(display=False, type=int)

    def __getattribute__(self, attr):
        if attr == 'delete':
            raise AttributeError
        return super(Resource, self).__getattribute__(attr)
