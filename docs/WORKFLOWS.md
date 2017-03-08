These docs show how to populate an example workflow in Tower
and how to automate the creation or copying of workflows.

## Normal CRUD

Workflows and workflow nodes can be managed as normal tower-cli resources.

### Workflow Creation

Create an empty workflow:
```
tower-cli workflow create --name="workflow1" --organization="Default" --description="example description"
```

Check the existing workflows with the standard list or get commands.
```
tower-cli workflow list --description-on
```

### Node Creation

Create nodes inside the workflow
These all become "root" nodes and will spawn jobs on workflow launch
without any dependencies on other nodes.
These commands create 2 root nodes.
```
tower-cli node create -W workflow1 --job-template="Hello World"
tower-cli node create -W workflow1 --job-template="Hello World"
```

List the nodes inside of the workflow
```
tower-cli node list -W workflow1
```

### Node Association

From the list command, you can find the ids of nodes you want to link
`assocate_success_node` will cause the 2nd node to run on success of the
first node. The following command causes node 2 to run on the event of
successful completion of node 1.
```
tower-cli node assocate_success_node 1 2
```

This operation is only possible when node 2 is a root node.
See the Tower documentation for the limitations on the types of node
connections allowed.

Auto-creation of the success node, only knowing the parent node id:
```
tower-cli node assocate_success_node 8 --job-template="Hello world"
```

Corresponding disassociate commands are also available. Disassociating
a node from another node will make it a root node.

## Node Network Bulk Management

To print out a YAML representation of the nodes of a workflow, you can
use the following command. JSON format is also allowed.

```
tower-cli workflow schema workflow1
```

Here, "workflow1" is the name of the workflow.

### Creating a Schema Definition

To bulk-create a workflow node network, use the workflow schema command.
The schema is JSON or YAML content, and can be passed in the CLI
argument, or pointed to a file. The schema is passed as a second positional
argument, where the first argument references the workflow.

```
tower-cli workflow schema workflow2 @schema.yml
```

The schema can be provided without using a file:

```
tower-cli workflow schema workflow2 '[{"job_template": "Hello world"}]'
```

The Schema definition defines the hierarchy structure that connects the nodes.
Names, as well as other valid parameters for node creation, are acceptable
inside of the node's entry inside the schema definition.

Links must be declared as a list under a key that starts with "success",
"failure", or "always". The following is an example of a valid schema
definition.

Example `schema.yml` file:

```yaml
- job_template: Hello world
  failure:
  - inventory_source: AWS servers (AWS servers - 42)
  success:
  - project: Ansible Examples
    always:
    - job_template: Echo variable
      success:
      - job_template: Scan localhost

```

This style may be useful to apply in a script to create a workflow
network with a tower-cli command after the constituent resources like
the job templates and projects were created by preceding
tower-cli commands.

### Differences with Machine Formatted Schemas

After writing a workflow schema, you may notice differences
in how tower-cli subsequently echos the schema definition back to you.
The following is what tower-cli might return after
writing the above example.

```yaml
- failure_nodes:
  - inventory_source: 42
  job_template: 45
  success_nodes:
  - always_nodes:
    - job_template: 55
      success_nodes:
      - job_template: 44
    project: 40

```

Note that the root node data starts with "failure_nodes", instead
of the name of the job template. This will not impact functionality, and
manually changing the order will not impact functionality either.

Although this format is harder to read, it does the same thing
as the previous schema. The ability to both echo and create schemas can
be used to copy the contents of one workflow to another.

As an example, consider 2 workflows. The first has a name "workflow1", and
has its node network populated. The second is named "workflow2" and is empty.
The following commands will copy the structure from the first to the second.

```bash
tower-cli workflow schema workflow1 > schema.yml
tower-cli workflow schema workflow2 @schema.yml
```

### Idempotence

The workflow schema feature populates the workflow node network based on the
hierarchy structure. Before creating each node, it attempts to find an
existing node with the specified properties in that location in the
tree, and will not create a new node if it exists.

Thus, running the command multiple times should not change the workflow
structure. To continue with the previous example, subsequent
invocations of:

```bash
tower-cli workflow schema workflow2 @schema.yml
tower-cli workflow schema workflow2 @schema.yml
```

should not change the network of workflow2.

The schema command can not delete nodes, so running multiple commands with
different schemas will result in creating multiple branches and/or
sub-branches.

## Launching Workflow Jobs

Use the workflow_job resource to launch workflow jobs.
This supports the use of extra_vars, which can contain answers to
survey questions.
The `--monitor` and `--wait` flag are available to poll the server
until workflow job reaches a completed status. The `--monitor` option
will print rolling updates of the jobs that ran as part of the workflow.
Here is an example of using those features:

```
tower-cli workflow_job launch -W "echo Hello World" -e a=1 --monitor
```
