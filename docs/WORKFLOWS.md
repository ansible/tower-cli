These docs show how to populate an example workflow to show how the feature
can be used.

### Workflow Creation

First, create an empty workflow
```
tower-cli workflow create --name="Tower-CLI-Workflow-Example" --organization="Default" --description="example description"
```

### Node Creation

Create nodes inside the workflow
These all become "base" nodes and will spawn jobs on workflow launch
without any dependencies on other nodes.
These commands create 2 base nodes.
```
tower-cli node create --workflow="Tower-CLI-Workflow-Example"
tower-cli node create --workflow="Tower-CLI-Workflow-Example"
```

List the nodes inside of the workflow
```
tower-cli node list --workflow="Tower-CLI-Workflow-Example"
```

### Node Association

From the list command, you can find the ids of nodes you want to link
assocate_success will cause the 2nd node to run on success of the first
```
tower-cli node assocate_success 8 12
```

Auto-creation of the success node, only knowing the parent node id
```
tower-cli node assocate_success 8 --job-template="Hello world"
```

### Node Network Bulk Management

To print out a YAML representation of the nodes of a workflow, you can
use the following command:

```
tower-cli workflow schema my_workflow
```

where "my_workflow" is the name of the workflow.

To bulk-create a workflow node network, use the workflow schema command
the schema is JSON or YAML content, and can be passed in the CLI
argument, or pointed to a file. The schema is passed as a second positional
argument, where the first argument references the workflow.

```
tower-cli workflow schema my_workflow @file.yml
```

```yaml
- job_template: Hello world
  failure_nodes:
    job_template: Followup job template
```
