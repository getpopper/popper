workflow "cli tests" {
  on = "push"
  resolves = "end"
}

action "test init" {
  uses = "./ci/test"
  runs = "init"
}

action "test metadata" {
  uses = "./ci/test"
  runs = "metadata"
}

action "test ci" {
  uses = "./ci/test"
  runs = "ci"
}

action "end" {
  uses = "./ci/test"
  runs = "version"
  needs = [
    "test init",
    "test metadata",
    "test ci"
  ]
}
