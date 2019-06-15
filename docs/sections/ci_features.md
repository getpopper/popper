# CI features

## Specifying which workflows to run via commit messages

When a CI service executes a popper workflow by invoking `popper run` on the CI server, it does so without passing any flags and hence we cannot specify which workflow to skip or execute. To make this more flexible, popper provides the ability to control which workflows are to be executed by looking for special keywords in commit messages.

The `popper:whitelist[<list-of-workflows>]` keyword can be used in a commit message to specify which workflows to execute among all the workflows present in the project. For example, 

```
This is a sample commit message that shows how we can request the 
execution of a particular workflow.

popper:whitelist[/path/to/workflow/a.workflow]
```

The above commit message specifies that only the workflow `a` will be executed and any other workflow will be skipped. A comma-separated list of workflow paths can be given in order to request the execution of more than one workflow. Alternatively, a skip list is also supported with the `popper:skip[<list-of-workflows>]` keyword to specify the list of workflows to be skipped.
