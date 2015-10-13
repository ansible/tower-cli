# Copyright 2013-2014, Ansible, Inc.
# Alan Rominger <arominger@ansible.com>
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
import pypandoc

# Produces a README.rst file, which is a re-formatted version of README.md
#  for the purposes of putting out a release.
with open('README.md', 'r') as f_read:
    text = pypandoc.convert(f_read.read(), 'rst', format='markdown')
    with open('README.rst', 'w') as f_write:
        f_write.write(text)
