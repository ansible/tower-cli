## Introduction - What Notification Templates Are

Starting with Ansible Tower 3.0, users can create and associate
notification templates to job templates. Whenever a job template undergoes
a successful/unsuccessful job run, all its related notification templates
will send out notifications to corresponding notification receiver, indicating
the status of job run.

## Managing Notification Templates with tower-cli

To see the commands available for notification templates, see 
`tower-cli notification_template --help`. Within a specific command, get the help 
text with `tower-cli notification_template <command> --help`.

The arguments for all notification template commands follow the same pattern, although
not all arguments are mandatory for all commands. The structure follows
the following pattern:

```
tower-cli role <action> <options>
```

Notification templates suppport all typical CRUD operations that control other 
resources through tower-cli: `get`, `list`, `create`, `modify` and `delete`. On 
the other hand, uses can use new command `tower-cli job_template associate_notification` 
and `tower-cli job_tempate disassociate_notification` to (dis)associate an existing 
notification to/from a job template.

### Basic Operations

CRUD operations on notification templates are basically the same as that of typicall
existing resources, e.g. `inventory`. There are, however, some points due to the nature
of notification templates that needs to be careful with:

* There are two options in `create`, `--job-template` and `--status`, which controls 
the create mode: providing these options will create a new notification template and 
associate it with the specified job template. Notification templates will be created
isolatedly if these options are not provided. You can find more information in Tower's
official documentation.
* When looking at the help text of certain notification template commands, note a large
portion of the available options are prefixed by a label like `[slack]`. These are special
configuration-related options which are composing elements of a notification template's
destination configuration. You can find more information about those options in Tower's 
official documentations. These options plus `--notification-configuration` option form
configuration-related options.
* Configuration-related options are *not* functioning options in `get`, `list` and `delete`,
meaning they will be ignored under these commands even provided. 
* The label prefixing configuration-related options indicate the type of notification
destination this option is used for. When creating a new notification template with certain
destination type (controlled by `--notification-type` option), *all non-default* related 
configuration-related options must be provided.
* When modifying an existing notification template, not every configuration-related
option has to be provided(but encryped fields must, even you are not changing it!). But if 
this modification modifies destination type, *all non-default* related configuration-related 
options must be provided.
* `--notification-configuration` option provides a json file specifying the configuration
details. All other configuration-related options will be ignored if `--notification-configuration``
is provided.

### Detailed Example

```bash
# Create a notification template in isolation.
tower-cli notification_template create --name foo --description bar --notification-type slack --channels a --channels b --token hey --organization Default

# Create a notification template under an existing job template.
tower-cli notification_template create --name foo --description bar --notification-type slack --channels a --channels b --token hey --job-template 5 --organization Default

# Get exactly one notification template.
tower-cli notification_template get --name foo

# Get a list of notification templates under certain criteria.
tower-cli notification_template list --notification-type irc

# Modify an existing notification.
tower-cli notification_template modify --description foo --token hi 17

# Delete an existing notification template.
tower-cli notification_template delete --name foo

# Associate a job template with an existing notification template.
tower-cli job_template associate_notification_template --job-template 5 --notification-template 3

# Disassociate a job template with an existing notification template.
tower-cli job_template disassociate_notification_template --job-template 5 --notification-template 3
```
