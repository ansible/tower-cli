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

from tower_cli.utils import compat


class OrderedDict(compat.OrderedDict):
    """OrderedDict subclass that nonetheless uses the basic dictionary
    __repr__ method.
    """
    def __repr__(self):
        """Print a repr that resembles dict's repr, but preserves
        key order.
        """
        return '{' + ', '.join(['%r: %r' % (k, v)
                                for k, v in self.items()]) + '}'
