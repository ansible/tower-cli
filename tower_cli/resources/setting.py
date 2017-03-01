# Copyright 2017, Ansible by Red Hat
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

from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.utils import exceptions as exc
from tower_cli.utils.data_structures import OrderedDict


class Resource(models.Resource):
    cli_help = 'Manage settings within Ansible Tower.'
    endpoint = '/settings/all/'

    value = models.Field(required=True)

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    def list(self, **kwargs):
        """Return a list of objects."""
        result = super(Resource, self).list(**kwargs)
        return {
            'results': [{'id': k, 'value': v} for k, v in result.items()]
        }

    @resources.command(ignore_defaults=True)
    def get(self, pk, **kwargs):
        """Return one and exactly one object"""
        # The Tower API doesn't provide a mechanism for retrieving a single
        # setting value at a time, so fetch them all and filter
        try:
            return next(s for s in self.list()['results'] if s['id'] == pk)
        except StopIteration:
            raise exc.NotFound('The requested object could not be found.')

    @resources.command(ignore_defaults=True)
    def modify(self, pk, value, **kwargs):
        """Modify an already existing object."""
        self.get(pk)
        r = client.patch(self.endpoint, data={pk: value})
        answer = OrderedDict((
            ('changed', True),
            ('id', pk),
            ('value', value)
        ))
        answer.update(r.json())
        return answer

    def __getattribute__(self, name):
        """Disable inherited methods that cannot be applied to this
        particular resource.
        """
        if name in ['create', 'delete']:
            raise AttributeError
        else:
            return object.__getattribute__(self, name)
