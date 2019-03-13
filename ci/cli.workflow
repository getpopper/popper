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

action "end" {
  uses = "./ci/test"
  runs = "version"
  needs = [
    "test init",
    "test ci",
    "test reuse",
    "test actions-demo",
    "test validate",
    "test scaffold"
  ]
}
