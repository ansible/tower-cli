# in the current verion of tower-cli, we can't delete the records of job
# runs and ad hoc commands because there is no "name" identifier that
# we can use to automatically look them up.

echo "Tower-CLI DATA FAKER: deleting job templates"
tower-cli job_template delete --name="Hello World"
tower-cli job_template delete --name="Hello World Debug"
tower-cli job_template delete --name="Hello World as user2"
tower-cli job_template delete --name="Apache"

echo "Tower-CLI DATA FAKER: deleting inventories"
tower-cli inventory delete --name=localhost

# For complex inventories, we only bother deleting the inventory resource
# and the groups and hosts contained within should go with it
tower-cli inventory delete --name=Production
tower-cli inventory delete --name=Testing
tower-cli inventory delete --name=QA

echo "Tower-CLI DATA FAKER: deleting credentials"
tower-cli credential delete --name=user1
tower-cli credential delete --name=user2

tower-cli credential delete --name="EC2 SSH"
tower-cli credential delete --name="Local SSH"
tower-cli credential delete --name="AWS creds"
tower-cli credential delete --name="RAX creds"

echo "Tower-CLI DATA FAKER: deleting users"
tower-cli user delete --username="rshinra"
tower-cli user delete --username="link"
tower-cli user delete --username="gdorf"
tower-cli user delete --username="zelda"
tower-cli user delete --username="sherlock"
tower-cli user delete --username="jack"

echo "Tower-CLI DATA FAKER: deleting the projects"
tower-cli project delete --name sample_playbooks

tower-cli project delete --name="Hyrulian Playbooks"
tower-cli project delete --name="Ansible Examples"

echo "Tower-CLI DATA FAKER: deleting orgs and teams"
# Teams do not automatically go away when their organization is deleted
# so we must delete them all
tower-cli team delete --name Ops
tower-cli team delete --name QA
tower-cli team delete --name Dev
tower-cli team delete --name Engineering
tower-cli team delete --name "Tech Services"
tower-cli organization delete --name="Hyrule Ventures"
tower-cli organization delete --name="Bio Inc"
