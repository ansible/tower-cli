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
    """A resource for activity stream.

    This resource is read-only.
    """
    cli_help = 'Activity on server.'
    endpoint = '/activity_stream/'

    operation = models.Field(display=True)
    # TODO: implement a datetime field for timestamp
    timestamp = models.Field(display=True)
    changes = models.Field(display=False)
    object1 = models.Field(display=True)
    object2 = models.Field(display=True)
    actor = models.Field(type=types.Related('user'))

    def __getattribute__(self, attr):
        if attr == 'delete':
            raise AttributeError
        return super(Resource, self).__getattribute__(attr)

    def list(self, *args, **kwargs):
        if ('order_by' not in kwargs and
                ('query' not in kwargs or not kwargs['query'])):
            kwargs['query'] = (('order_by', '-timestamp'),)
        return super(Resource, self).list(*args, **kwargs)

    @staticmethod
    def _promote_actor(d):
        if ('summary_fields' in d and 'actor' in d['summary_fields'] and
                d['summary_fields']['actor']):
            d['actor'] = d['summary_fields']['actor']['username']
        else:
            d['actor'] = None

    def read(self, *args, **kwargs):
        '''
        Do extra processing so we can display the actor field as
        a top-level field
        '''
        if 'actor' in kwargs:
            kwargs['actor'] = kwargs.pop('actor')
        r = super(Resource, self).read(*args, **kwargs)
        if 'results' in r:
            for d in r['results']:
                self._promote_actor(d)
        else:
            self._promote_actor(d)
        return r
