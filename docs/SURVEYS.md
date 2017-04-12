# How to manage surveys of job templates and workflows through tower-cli

This feature is added in v3.1.0, and v3.1.3 or higher, at least, is recommended.

get help: `tower-cli job_template survey --help`

## View a Survey

The name of the job template is known ("survey jt" in this example), and the
survey definition is desired.

`tower-cli job_template survey --name="survey jt"`

Example output, this is the survey spec:

```json
{
  "description": "", 
  "spec": [
    {
      "required": true, 
      "min": null, 
      "default": "v3.1.3", 
      "max": null, 
      "question_description": "enter a version of tower-cli to install", 
      "choices": "v3.0.0\nv3.0.1\nv3.0.2\nv3.1.0\nv3.1.1\nv3.1.2\nv3.1.3", 
      "new_question": true, 
      "variable": "version", 
      "question_name": "Tower-cli version", 
      "type": "multiplechoice"
    }, 
    {
      "required": true, 
      "min": null, 
      "default": "click\ncolorama\nrequests\nsix\nPyYAML", 
      "max": null, 
      "question_description": "which package requirements would you like to install/check", 
      "choices": "click\ncolorama\nrequests\nsix\nPyYAML", 
      "new_question": true, 
      "variable": "packages", 
      "question_name": "Package requirements", 
      "type": "multiselect"
    }
  ], 
  "name": ""
}
```

## Save a survey

Use the job template `modify` command to do this. In order to create a
_functional_ survey you must do two things:

 - Save the survey spec - use the `--survey-spec` option
 - Enable the survey - use the `--survey-enabled` option

Example of enabling the survey on a job template:

 ```
 tower-cli job_template modify --name="hello world infinity" --survey-enabled=true
 ```

The `--survey-spec` option can get the spec from a file by prepending the `@`
character. If this character is not used, it is assumed that you are giving
the JSON data in-line.


### Copy a survey to another template

The following example saves a survey spec to a file, and then uploads that
survey spec to another job template.

```bash
# Save the survey spec to file in local directory
tower-cli job_template survey --name="survey jt" > s.json
# Upload that survey to another job template
tower-cli job_template modify --name="another jt" --survey-spec=@s.json --survey-enabled=true
```

The next example using one line to do the same thing on the command line.

```
tower-cli job_template modify --name="another jt" --survey-spec="$(tower-cli job_template survey --name='survey jt')" --survey-enabled=true
```

## Workflows

Workflows can also have surveys and follow the same pattern. Example:

`tower-cli workflow survey --name="workflow with survey"`
