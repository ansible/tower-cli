# Copyright 2015, Ansible, Inc.
# Alan Rominger <arominger@ansible.com> and others
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
echo "        == Tower-CLI DATA FAKER == "
echo "  Setting up fake data for tower-cli testing"
echo " "

echo "Tower-CLI DATA FAKER: reading config settings"
hostval=$(tower-cli config host)
USER_OUTPUT=$(tower-cli config username)
userval=$(echo $USER_OUTPUT| cut -d' ' -f 2)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ $userval == "username: " ]]
then
  echo "WARNING: Configuration has not been fully set";
  echo "   You will want to run the $ tower-cli config ";
  echo "   command for host, username, and password ";
  return;
fi

echo " current configuration settings:"
echo $hostval
echo $userval

echo "Tower-CLI DATA FAKER: creating orgs and teams"
# Data regarding Hyrule Ventures was taken from
# https://github.com/jsmartin/tower_populator
tower-cli organization create --name="Default"
tower-cli organization create --name="Hyrule Ventures" --description="Mining Rupees Daily"
tower-cli team create --name="Ops" --organization=Default --description="The Ops Team"
tower-cli team create --name="QA" --organization=Default --description="Assures quality of software"
tower-cli team create --name="Dev" --organization=Default --description="Develops software"

tower-cli organization create --name="Bio Inc" --description="Medical services"
tower-cli team create --name="Tech Services" --organization="Bio Inc" --description="Helps customers with problems"
tower-cli team create --name="Engineering" --organization="Bio Inc" --description="Does tech things"

echo "Tower-CLI DATA FAKER: adding projects (--wait flag waits for SCM update)"
# The Hyrulian playbooks configure servers on the planet of Hyrule,
# and the project containing these playbooks belongs to their organization
tower-cli project create --name="Hyrulian Playbooks" --description="Configures all the servers in Hyrule." --scm-type=git --scm-url="https://github.com/jsmartin/tower-demo-example-simple" --organization="Hyrule Ventures" --wait
# Generic examples
tower-cli project create --name="Ansible Examples" --description="Some example roles and playbooks" --scm-type=git --scm-url="https://github.com/ansible/ansible-examples" --organization "Default" --wait
tower-cli project create --name sample_playbooks --organization "Default" --scm-type git --scm-url https://github.com/AlanCoding/permission-testing-playbooks.git --wait
tower-cli project create --name="Inventory file examples" --organization "Default" --scm-type git --scm-url https://github.com/AlanCoding/Ansible-inventory-file-examples.git --wait


echo "Tower-CLI DATA FAKER: creating users"
# The Hyrule Ventures team
tower-cli user create --username="link" --password="password" --email=asdf@asdf.com --first-name=Link --last-name=Smith
tower-cli organization associate --organization="Hyrule Ventures" --user=link
tower-cli team associate --team=Ops --user=link
tower-cli user create --username="gdorf" --password="password" --email=asdf@asdf.com --first-name=Geoff --last-name=Smith
tower-cli organization associate --organization="Hyrule Ventures" --user=gdorf
tower-cli team associate --team=QA --user=gdorf
tower-cli user create --username="zelda" --password="password" --email=asdf@asdf.com --first-name=Zelda --last-name=Smith
tower-cli organization associate --organization="Hyrule Ventures" --user=zelda
tower-cli team associate --team=Dev --user=zelda
# The Bio Inc team
tower-cli user create --username="sherlock" --password="password" --email=asdf@asdf.com --first-name=Sherlock --last-name=Holmes
tower-cli organization associate --organization="Bio Inc" --user=sherlock
tower-cli team associate --team="Tech Services" --user=sherlock
tower-cli user create --username="jack" --password="password" --email=asdf@asdf.com --first-name=Jack --last-name=Black
tower-cli organization associate --organization="Bio Inc" --user=jack
tower-cli team associate --team=Engineering --user=jack
# Users not belonging to an organization
tower-cli user create --username="rshinra" --password="password" --email=asdf4@asdf.com --first-name=Rufus --last-name=Shinra
# Examples of associating a user with different organizations
echo " associating a user with an organization"
tower-cli organization associate --organization="Bio Inc" --user="rshinra"
echo " disassociating a user with an organization"
tower-cli organization disassociate --organization="Bio Inc" --user="rshinra"

# key taken from http://phpseclib.sourceforge.net/rsa/examples.html
machine_cred_inputs="username: root
ssh_key_data: |
  -----BEGIN RSA PRIVATE KEY-----
  MIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp
  wmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5
  1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh
  3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2
  pIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX
  GukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il
  AkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF
  L0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k
  X6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl
  U9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ
  37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=
  -----END RSA PRIVATE KEY-----"

echo "Tower-CLI DATA FAKER: creating credentials"
# Example credentials for cloud and machine
tower-cli credential create --name="SSH example" --organization="Default" --inputs="$machine_cred_inputs" --credential-type="Machine"
tower-cli credential create --name="blank SSH" --organization="Default" --inputs="{}" --credential-type="Machine"
tower-cli credential create --name="vault password" --organization="Default" --inputs="vault_password: password" --credential-type="Vault"
tower-cli credential create --name="AWS creds" --team=Ops --credential-type="Amazon Web Services" --inputs='{"username": "your_username", "password": "password"}'
# Two users who can become the other to escalate a task
tower-cli credential create --credential-type="Machine" --name=user1 --inputs='{"username": "user1", "password": "pass1", "become_method": "su", "become_username": "user2"}' --organization="Default"
tower-cli credential create --credential-type="Machine" --name=user2 --inputs='{"username": "user2", "password": "pass1", "become_method": "su", "become_username": "user1"}' --organization="Default"

echo "Tower-CLI DATA FAKER: creating inventories and groups"
# Basic localhost examples
tower-cli inventory create --name=localhost --description="local machine" --organization=Default --variables="@$DIR/variables.yml"
tower-cli host create --name="127.0.0.1" --description="this is a manually created host" --inventory="localhost" --variables="@$DIR/variables.yml"

# Corporate example uses localhost with special vars for testing
tower-cli inventory create --name=Production --description="Production Machines" --organization="Hyrule Ventures" --variables="@$DIR/variables.yml"
# Example of creating a cloud inventory source, with some configurables
tower-cli inventory_source create --name=EC2 --credential="AWS creds" --source=ec2 --description="EC2 hosts" --inventory=Production --overwrite=true --source-regions="us-east-1" --overwrite-vars=false --source-vars="foo: bar"

example_script="#!/usr/bin/env python
import json
inventory = {'_meta': {'hostvars': {'foobar': {}}}, 'ungrouped': {'hosts': ['foobar']}}
print json.dumps(inventory)"

# Inventory examples with custom scripts stored in Tower
tower-cli inventory create --name="Custom script inventory" --description="this is an inventory that contains a custom inventory source" --organization="Bio Inc" --variables="@$DIR/variables.yml"
# The script can also be obtained from a file using the "@" character
tower-cli inventory_script create --name="foobar inventory script" --script="$example_script" --organization="Bio Inc"
tower-cli inventory_source create --name="fetch foobar" --source-script="foobar inventory script" --inventory="Custom script inventory" --source="custom"
# This will actually run the script, which fetches the host "foobar"
tower-cli inventory_source update "fetch foobar" --monitor
# Observe the new host "foobar"
tower-cli host list --inventory="Custom script inventory"

# Examples of nested groups, associating and managing hosts/groups
tower-cli inventory create --name="tower-cli manual examples" --organization="Default" --variables="@$DIR/variables.yml"
tower-cli group create --name=web --inventory="tower-cli manual examples"
tower-cli host create --name="10.42.0.6" --inventory="tower-cli manual examples"
tower-cli host create --name="10.42.0.7" --inventory="tower-cli manual examples"
tower-cli host create --name="10.42.0.8" --inventory="tower-cli manual examples"
tower-cli host create --name="10.42.0.9" --inventory="tower-cli manual examples"
tower-cli host create --name="10.42.0.10" --inventory="tower-cli manual examples"
# these include databases and web servers, with hosts in the web server group
tower-cli group create --name="databases" --inventory="tower-cli manual examples"
# Setting up the web servers, associate hosts with the group
tower-cli group create --name="web servers" --inventory="tower-cli manual examples"
tower-cli host create --name="server.example1.com" --inventory="tower-cli manual examples"
tower-cli host associate --host="server.example1.com" --group="web servers"
tower-cli host create --name="server.example2.com" --inventory="tower-cli manual examples"
tower-cli host associate --host="server.example2.com" --group="web servers"

# Example of inventory contents sourced from a project
tower-cli inventory create --name="tower-cli SCM inventory example" --organization="Default" --variables="@$DIR/variables.yml"
# Uses an example taken from the official Ansible docs
tower-cli inventory_source create --name="project-based source" --inventory="tower-cli SCM inventory example" --source="scm" --source-project="Inventory file examples" --source-path="official/inventory.ini" --overwrite-vars=true
tower-cli inventory_source update "project-based source" --monitor
# Have a look at the group structure from this import
tower-cli group list --inventory="tower-cli SCM inventory example"

echo "Tower-CLI DATA FAKER: create job templates"
# Hello world example, including different credentials
#  note that since we have set "connection: local", the credentials do not matter.
tower-cli job_template create --name="Hello World Debug" --description="debug statement" --inventory=localhost --credential=user1 --project=sample_playbooks --playbook=debug.yml
tower-cli job_template create --name="Hello World" --description="echo statement" --inventory=localhost --credential=user1 --project=sample_playbooks --playbook=helloworld.yml
tower-cli job_template create --name="Hello World as user2" --description="echo statement with user2 credentials" --inventory=localhost --credential=user2 --project=sample_playbooks --playbook=helloworld.yml
# Example from Hyrule data set
tower-cli job_template create --name=Apache --description="Confgure Apache servers" --inventory="tower-cli manual examples" --project="Hyrulian Playbooks" --playbook="site.yml" --credential="SSH example" --job-type=run --verbosity=verbose --forks=5

echo "Tower-CLI DATA FAKER: run a job, check status, cancel, and run with monitoring"
# Launch job without monitoring
tower-cli job launch --job-template="Hello World Debug"
# Note that these only work because there are no other completed jobs from that template
# If that is not true, you need to run "job list" and then cancel with the ID
tower-cli job status --job-template="Hello World Debug" --status="running"
tower-cli job cancel --job-template="Hello World Debug" --status="running"
# Note that delete is different from cancel.
# With delete, we remove the record of this job's run. For instance:
# tower-cli job delete {pk}
# launch a job with monitoring turned on
tower-cli job launch --job-template="Hello World Debug" --monitor

echo "Tower-CLI DATA FAKER: displaying jobs that have run via the fake data script"
tower-cli job list --job-template="Hello World Debug"
