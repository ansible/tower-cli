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
#
# This bash script can populate an instance of Ansible Tower with
# fake data, using the command line interface (tower-cli) to do so.

echo " "
echo "        == Tower-CLI WORKFLOW DEMO == "
echo " "

echo "current location: ${BASH_SOURCE%/*}"

tower-cli organization create --name="Default"

tower-cli project create --name="Ansible Examples" --scm-type=git --scm-url="https://github.com/ansible/ansible-examples" --wait
tower-cli project create --name="Ansible Examples2" --scm-type=git --scm-url="https://github.com/ansible/ansible-examples" --wait

tower-cli inventory create --name="workflow demo" --organization=Default
tower-cli inventory_script create --name="example inv script" --organization="Default" --script="@${BASH_SOURCE%/*}/inventory_script_example.py"
# Note that these 2 groups need to have distinct names without one starting with the other
tower-cli group create --name="tower script1" --inventory="workflow demo" --source="custom" --source-script="example inv script"
tower-cli group create --name="tower script2" --inventory="workflow demo" --source="custom" --source-script="example inv script"

tower-cli inventory create --name="localhost"
tower-cli host create --inventory="localhost" --name="localhost" --variables='{"connection": "local", "ansible_host": "localhost"}'

tower-cli credential create --name="Local SSH" --kind=ssh --organization="Default" --ssh-key-data="${BASH_SOURCE%/*}/insecure_private_key"

tower-cli job_template create --name="workflow JT" --inventory="localhost" --machine-credential="Local SSH" --project="Ansible Examples" --playbook="language_features/loop_nested.yml"
tower-cli job_template create --name="workflow JT2" --inventory="localhost" --machine-credential="Local SSH" --project="Ansible Examples" --playbook="language_features/loop_nested.yml"

# Create the WFJT resource itself
tower-cli workflow create --name="workflow demo" --organization="Default"

echo ''
echo '   -- application of simple schema --'
tower-cli workflow schema "workflow demo" "@${BASH_SOURCE%/*}/data/schema_simple.yml"

echo ''
echo '   -- application of tiny schema --'
tower-cli workflow schema "workflow demo" "@${BASH_SOURCE%/*}/data/schema_tiny.yml"

echo ''
echo '   -- application of schema a --'
tower-cli workflow schema "workflow demo" "@${BASH_SOURCE%/*}/data/schema_a.yml"

echo ''
echo '   -- application of schema a --'
tower-cli workflow schema "workflow demo" "@${BASH_SOURCE%/*}/data/schema_b.yml"
