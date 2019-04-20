workflow "cli tests" {
  on = "push"
  resolves = "end"
}

action "test init" {
  uses = "./ci/test"
  runs = "init"
}

action "test ci" {
  uses = "./ci/test"
  runs = "ci"
}

action "test reuse" {
  uses = "./ci/test"
  runs = "reuse"
}

action "test actions-demo" {
  uses = "./ci/test"
  runs = "actions-demo"
}

action "test validate" {
  uses = "./ci/test"
  runs = "validate"
}

action "test scaffold" {
  uses = "./ci/test"
  runs = "scaffold"
}

action "test recursive" {
  uses = "./ci/test"
  runs = "recursive"
}

action "test dry-run" {
  uses = "./ci/test"
  runs = "dry-run"
}

action "test parallel" {
  uses = "./ci/test"
  runs = "parallel"
}

action "test dot" {
  uses = "./ci/test"
  runs = "dot"
}

action "test singularity" {
  uses = "./ci/test"
  runs = "singularity"
}

action "test interrupt" {
  uses = "./ci/test"
  runs = "interrupt"
}

action "test add" {
  uses = "./ci/test"
  runs = "add"
}

action "test quiet" {
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
