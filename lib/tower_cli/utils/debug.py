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

import sys

from tower_cli.conf import settings
from tower_cli.utils import secho


def log(s, header='', file=sys.stderr, nl=1, **kwargs):
    """Log the given output to stderr if and only if we are in
    verbose mode.

    If we are not in verbose mode, this is a no-op.
    """
    # Sanity check: If we are not in verbose mode, this is a no-op.
    if not settings.verbose:
        return

    # Construct multi-line string to stderr if header is provided.
    if header:
        word_arr = s.split(' ')
        multi = []
        word_arr.insert(0, '%s:' % header.upper())
        i = 0
        while i < len(word_arr):
            to_add = ['***']
            count = 3
            while count <= 79:
                count += len(word_arr[i]) + 1
                if count <= 79:
                    to_add.append(word_arr[i])
                    i += 1
                    if i == len(word_arr):
                        break
            if i != len(word_arr):
                count -= len(word_arr[i]) + 1
            to_add.append('*' * (78 - count))
            multi.append(' '.join(to_add))
        s = '\n'.join(multi)
        lines = len(multi)
    else:
        lines = 1

    # If `nl` is an int greater than the number of rows of a message,
    # add the appropriate newlines to the output.
    if isinstance(nl, int) and nl > lines:
        s += '\n' * (nl - lines)

    # Output to stderr.
    return secho(s, file=file, **kwargs)
