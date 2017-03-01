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

### Bulk Creation

To bulk-create a workflow node network, use the workflow schema command
the schema is JSON or YAML content, and can be passed in the CLI
argument, or pointed to a file.
```
tower-cli workflow schema @file.yml
```

```yaml
 - job template: hello world
   - sucess:
     - project: examples
```
