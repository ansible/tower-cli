## Introduction - What Roles Are

Starting with Ansible Tower 3.0, roles are the objects used to manage
permissions to various resources within Tower. Each role represents:

 - A type of permission like "use", "update", or "admin"
 - A resource that this permission applies to, like an inventory or credential
 - The actor, in the form of a user or a team, that receives the permission

Collectively, this is a "Role Based Access Control" or RBAC.

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
roles. In the following example, a user is added to the project use role.

```
tower-cli role grant --type use --user test_user --project test_project
```

In the above command "test_user" is the username of a user to receive the
new permission, "test_project" is the name of the project they are receiving
permission for, and "use" is the type of permission they are receiving.

In a similar fashion, to remove the user from that role:

```
tower-cli role revoke --type use --user test_user --project test_project
```

To list all of the roles on that project:

```
tower-cli role list --project test_project
```

### Detailed Example

The following commands will create an inventory and user and demonstrate
the different role commands on them.

```
tower-cli inventory create --name 'test_inventory' --organization Default
tower-cli role list --inventory 'test_inventory'
tower-cli role get --type read --inventory test_inventory

tower-cli user create --username 'test_user' --password 'pa$$' --email abc@abc.com
tower-cli role grant --type read --user test_user --inventory test_inventory

tower-cli role revoke --type read --user test_user --inventory test_inventory
```

