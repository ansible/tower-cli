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

# Import mock from the unittest module in the stdlib if it's there
# (Python 3.3+), otherwise import the pip package, which is required
# in Python 2.

# Import unittest2 if we have it (required on Python 2.6),
# otherwise just use the stdlib unittest.
try:
    import unittest2 as unittest  # NOQA
except ImportError:  # Python >= 2.7
    import unittest  # NOQA

try:
    from unittest import mock  # NOQA
except ImportError:  # Python < 3.3
    import mock  # NOQA

# Import the correct class used for when a file is opened.
try:
    from io import TextIOWrapper
except ImportError:  # Python < 3
    TextIOWrapper = file  # NOQA
