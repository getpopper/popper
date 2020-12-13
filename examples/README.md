# Examples

A list of examples that can be used as starter points for automating development 
and testing workflows with Popper.

## Usage

Each example contains a `ci.yml` file in it. You can copy-paste the content of 
the folder into your new project, and subsequently execute the workflow by 
running:

```bash
popper run -f ci.yml
```

## CI Service Setup

You can use Popper to generate configuration files that are consumed by a CI 
service to automatically run a workflow. Assuming you place the starter workflow 
on the root of your repository, you can generate a CI configuration file by 
doing:

```bash
popper ci --file ci.yml <SERVICE>
```

Where `SERVICE` is the name of a supported service (Travis, CircleCI, Jenkins 
and Gitlab-CI are supported). See more in [Popper 
documentation](../docs/sections/cli_features.md#continuously-validating-a-workflow).
