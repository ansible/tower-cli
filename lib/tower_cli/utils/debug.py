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

    # If this is a "header" line, make it a header.
    if header:
        s = '*** %s: %s %s' % \
            (header.upper(), s, '*' * (72 - len(header) - len(s)))

    # If `nl` is an int greater than 1, add the appropriate newlines
    # to the output.
    if isinstance(nl, int) and nl > 1:
        s += '\n' * (nl - 1)

    # Output to stderr.
    return secho(s, file=file, **kwargs)
