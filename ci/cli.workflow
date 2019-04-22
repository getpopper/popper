workflow "cli tests" {
  on = "push"
  resolves = "end"
}
action "Shellcheck" {
  uses = "actions/bin/shellcheck@master"
  args = "-x ./ci/test/*"
}
action "test init" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "init"
}

action "test ci" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "ci"
}

action "test reuse" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "reuse"
}

action "test actions-demo" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "actions-demo"
}

action "test validate" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "validate"
}

action "test scaffold" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "scaffold"
}

action "test recursive" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "recursive"
}

action "test dry-run" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "dry-run"
}

action "test parallel" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "parallel"
}

action "test dot" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "dot"
}

action "test singularity" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "singularity"
}

action "test interrupt" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "interrupt"
}

action "test add" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "add"
}

action "test quiet" {
  needs = "Shellcheck"
  uses = "./ci/test"
  runs = "quiet"
}

action "end" {
  uses = "./ci/test"
  runs = "version"
  needs = [
    "test actions-demo",
    "test add",
    "test ci",
    "test dot",
    "test dry-run",
    "test init",
    "test interrupt",
    "test parallel",
    "test quiet",
    "test recursive",
    "test reuse",
    "test scaffold",
    "test singularity",
    "test validate"
  ]
}
