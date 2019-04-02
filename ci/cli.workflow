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

action "test clone" {
  uses = "./ci/test"
  runs = "clone"
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

action "test parallel stage exec" {
  uses = "./ci/test"
  runs = "parallel_stage_exec"
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

action "end" {
  uses = "./ci/test"
  runs = "version"
  needs = [
    "test init",
    "test ci",
    "test reuse",
    "test actions-demo",
    "test validate",
    "test scaffold",
    "test clone",
    "test recursive",
    "test dry-run",
    "test scaffold",
    "test parallel stage exec",
    "test dot",
    "test singularity",
    "test interrupt"
  ]
}
