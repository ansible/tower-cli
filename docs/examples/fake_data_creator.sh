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
userval=$(tower-cli config username)
passwordval=$(tower-cli config password)

if [[ $userval == "username: " ]] || [[ $passwordval == "password: " ]]
then
  echo "WARNING: Configuration has not been fully set";
  echo "   You will want to run the $ tower-cli config ";
  echo "   command for host, username, and password ";
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

echo "Tower-CLI DATA FAKER: adding projects (--monitor flag waits for SCM update)"
# The Hyrulian playbooks configure servers on the planet of Hyrule,
# and the project containing these playbooks belongs to their organization
tower-cli project create --name="Hyrulian Playbooks" --description="Configures all the servers in Hyrule." --scm-type=git --scm-url="https://github.com/jsmartin/tower-demo-example-simple" --organization="Hyrule Ventures" --monitor
# Generic examples
tower-cli project create --name="Ansible Examples" --description="Some example roles and playbooks" --scm-type=git --scm-url="https://github.com/ansible/ansible-examples" --monitor
tower-cli project create --name sample_playbooks --organization "Default" --scm-type git --scm-url https://github.com/AlanCoding/permission-testing-playbooks.git --monitor
# Examples of moving around a project to different organizations and back again
echo " associating a project with an organization"
tower-cli organization associate_project --organization="Bio Inc" --project="sample_playbooks"
tower-cli organization associate_project --organization="Hyrule Ventures" --project="sample_playbooks"

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

echo "Tower-CLI DATA FAKER: creating credentials"
# Example credentials for cloud and machine
tower-cli credential create --name="EC2 SSH" --description="Used for EC2 instances" --team=Ops --kind=ssh --username=root --ssh-key-data="~/.ssh/id_rsa"
# key taken from http://phpseclib.sourceforge.net/rsa/examples.html
tower-cli credential create --name="Local SSH" --description="Used for vagrant instances" --team=Ops --kind=ssh --username=vagrant --ssh-key-data="insecure_private_key"
tower-cli credential create --name="AWS creds" --team=Ops --kind=aws --username=your_username --password=canthandle1234
tower-cli credential create --name="RAX creds" --description="Used for Rackspace" --team=Ops --kind=rax --username=me --password=noyoucant
# Two users who can become the other to escalate a task
tower-cli credential create --name=user1 --username=user1 --password=password --team=Engineering --kind=ssh --become-method=su --become-username=user2 --become-password=pass1
tower-cli credential create --name=user2 --username=user2 --password=pass1 --team=Engineering --kind=ssh --become-method=su --become-username=user1 --become-password=password

echo "Tower-CLI DATA FAKER: creating inventories and groups"
# Basic localhost examples
tower-cli inventory create --name=localhost --description="local machine" --organization=Default --variables="variables.yml"
tower-cli host create --name="127.0.0.1" --description="the host in localhost" --inventory="localhost" --variables="variables.yml"
# Corporate example uses localhost with special vars for testing
tower-cli inventory create --name=Production --description="Production Machines" --organization="Hyrule Ventures" --variables="variables.yml"
tower-cli group create --name=EC2 --credential="AWS creds" --source=ec2 --description="EC2 hosts" --inventory=Production
tower-cli group create --name=RAX --credential="RAX creds" --source=rax --description="RAX hosts" --inventory=Production
# EC2vars demonstrates the use of advanced source variables
tower-cli group create --name=EC2vars --credential="AWS creds" --source=ec2 --description="EC2 hosts" --inventory=Production --source-regions="us-east-1" --overwrite=true --overwrite-vars=false --source-vars="foo: bar"
# Another example
tower-cli inventory create --name="Testing" --description="Test Machines" --organization="Bio Inc" --variables="variables.yml"
tower-cli group create --name=web --source=manual --inventory=Testing --variables="variables.yml"
tower-cli host create --name="10.42.0.6" --inventory=Testing
tower-cli host create --name="10.42.0.7" --inventory=Testing
tower-cli host create --name="10.42.0.8" --inventory=Testing
tower-cli host create --name="10.42.0.9" --inventory=Testing
tower-cli host create --name="10.42.0.10" --inventory=Testing
# Another inventory, but with recursive structure
# these include databases and web servers, with hosts in the web server group
tower-cli inventory create --name=QA --description="QA Machines" --organization=Default --variables="variables.yml"
tower-cli group create --name="databases" --source=manual --inventory=QA --variables="variables.yml"
# Setting up the web servers, associate hosts with the group
tower-cli group create --name="web servers" --source=manual --inventory=QA --variables="variables.yml"
tower-cli host create --name="server.example1.com" --inventory=QA
tower-cli host associate --host="server.example1.com" --group="web servers"
tower-cli host create --name="server.example2.com" --inventory=QA
tower-cli host associate --host="server.example2.com" --group="web servers"


echo "Tower-CLI DATA FAKER: create job templates"
# Hello world example, including different credentials
#  note that since we have set "connection: local", the credentials do not matter.
tower-cli job_template create --name="Hello World Debug" --description="debug statement" --inventory=localhost --machine-credential=user1 --project=sample_playbooks --playbook=debug.yml
tower-cli job_template create --name="Hello World" --description="echo statement" --inventory=localhost --machine-credential=user1 --project=sample_playbooks --playbook=helloworld.yml
tower-cli job_template create --name="Hello World as user2" --description="echo statement with user2 credentials" --inventory=localhost --machine-credential=user2 --project=sample_playbooks --playbook=helloworld.yml
# Example from Hyrule data set
tower-cli job_template create --name=Apache --description="Confgure Apache servers" --inventory=Testing --project="Hyrulian Playbooks" --playbook="site.yml" --machine-credential="Local SSH" --job-type=run --verbosity=verbose --forks=5

echo "Tower-CLI DATA FAKER: run a job, check status, cancel, and run with monitoring"
# Launch job without monitoring
tower-cli job launch --job-template="Hello World Debug" --job-explanation="launched by example script"
# Note that these only work because there are no other completed jobs from that template
# If that is not true, you need to run "job list" and then cancel with the ID
tower-cli job status --job-template="Hello World Debug"
tower-cli job cancel --job-template="Hello World Debug"
# Note that delete is different from cancel.
# With delete, we remove the record of this job's run. For instance:
# tower-cli job delete {pk}
# launch a job with monitoring turned on
tower-cli job launch --job-template="Hello World Debug" --monitor --job-explanation="launched by example script"

echo "Tower-CLI DATA FAKER: displaying jobs that have run via the fake data script"
tower-cli job list --job-template="Hello World Debug"
