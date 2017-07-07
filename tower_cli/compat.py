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

# Import OrderedDict from the standard library if possible, and from
# the ordereddict library (required on Python 2.6) otherwise.
try:
    from collections import OrderedDict  # NOQA
except ImportError:  # Python < 2.7
    from ordereddict import OrderedDict  # NOQA


# Import simplejson if we have it (Python 2.6), and use json from the
# standard library otherwise.
#
# Note: Python 2.6 does have a JSON library, but it lacks `object_pairs_hook`
# as a keyword argument to `json.loads`, so we still need simplejson on
# Python 2.6.
import sys
if sys.version_info < (2, 7):
    import simplejson as json  # NOQA
else:
    import json  # NOQA
