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

from six.moves import StringIO

from tower_cli.utils.exceptions import TowerCLIError

from tests.compat import unittest


class ExceptionTests(unittest.TestCase):
    """A set of tests to ensure that our exception classes all work in
    the way that we expect.
    """
    def test_show(self):
        """Establish that the show method will properly route to an
        alternate file.
        """
        sio = StringIO()
        ex = TowerCLIError('Fe fi fo fum; I smell the blood of an Englishman.')
        ex.show(file=sio)
        sio.seek(0)
        self.assertIn('Fe fi fo fum;', sio.read())
