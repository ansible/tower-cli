## Introduction - What Roles Are

Starting with Ansible Tower 3.0, roles are the objects used to manage
permissions to various resources within Tower. Each role represents:

 - A type of permission like "use", "update", or "admin"
 - A resource that this permission applies to, like an inventory or credential

This is "Role Based Access Control" or RBAC. Each role may have several
users associated with it, where each of the users gains the specified type
of permission. Teams may also be associated with a role, in which case all
users who are members of the team receive the specified type of permission.

## Managing Roles with tower-cli

To see the commands available for roles, see `tower-cli roles`. Within a
specific command, get the help text with `tower-cli roles list --help`.

The arguments for all role commands follow the same pattern, although
not all arguments are mandatory for all commands. The structure follows
the following pattern:

```
tower-cli role <action> --type <choice> --user/team <name/pk> --resource <name/pk>
```

Roles do not have the typical CRUD operations that control other resources
through tower-cli. Roles can not be deleted or created on their own, because
they are tied to the resource that they reference. The next section covers
what the possible actions are.

### Basic Operations

The primary use case for roles is adding or removing users and teams from
roles. In the following example, a user is added to the project "use" role.

```
tower-cli role grant --type use --user test_user --project test_project
```

In the above command "test_user" is the username of a user to receive the
new permission, "test_project" is the name of the project they are receiving
permission for, and "use" is the type of permission they are receiving.
Specifically, this allows test_user to use test_project in a job template.

In a similar fashion, to remove the user from that role:

```
tower-cli role revoke --type use --user test_user --project test_project
```

To list the roles on that project:

```
tower-cli role list --project test_project
```

### Detailed Example

The following commands will create an inventory and user and demonstrate
the different role commands on them.

```bash
# Create the inventory and list its roles
tower-cli inventory create --name 'test_inventory' --organization 'Default'
tower-cli role list --inventory 'test_inventory'
tower-cli role get --type 'use' --inventory 'test_inventory'

# Create a user, give access to the inventory and take it away
tower-cli user create --username 'test_user' --password 'pa$$' --email 'user@example.com'
tower-cli role grant --type 'use' --user 'test_user' --inventory 'test_inventory'
tower-cli role list --user 'test_user' --type 'use'
tower-cli role revoke --type 'use' --user 'test_user' --inventory 'test_inventory'

# Create a team, give access to the inventory and take it away
tower-cli team create --name 'test_team' --organization 'Default'
tower-cli role grant --type 'use' --team 'test_team' --inventory 'test_inventory'
tower-cli role list --team 'test_team' --type 'use'
tower-cli role revoke --type 'use' --team 'test_team' --inventory 'test_inventory'
```

### Organization and Team Roles

For assigning users to teams and organizations, include the team or
organization flag, and it will be acted on as the resource. Note that teams
can be either the resource or the role grantee, depending of whether the
`--team` or the `--target-team` flag is used.

The following example appoints `test_user` to the member role of a team
and of an organization.

```bash
tower-cli role grant --user 'test_user' ---target-team 'test_team' --type 'member'
tower-cli role grant --organization 'Default' --user 'test_user' --type 'member'
```

These commands are redundant with the tower-cli organization and team
`associate` and `disassociate` commands.
