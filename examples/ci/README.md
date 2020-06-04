# CI workflow starters

A list of examples that can be used as starter points for automating 
CI workflows with Popper.

## CI Service Setup

You can use the `popper` tool to generate configuration files that are 
consumed by a CI service to automatically run a workflow. Assuming you 
place the starter workflow on the root of your repository, you can 
generate a CI configuration file by doing:

```bash
popper ci --file ci.yml <SERVICE>
```

Where `SERVICE` is the name of a supported service (Travis, CircleCI, 
Jenkins and Gitlab are supported). See more in [Popper 
documentation](../docs/sections/cli_features.md#continuously-validating-a-workflow).
