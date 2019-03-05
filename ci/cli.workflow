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

action "end" {
  uses = "./ci/test"
  runs = "version"
  needs = [
    "test init",
    "test ci",
    "test reuse"
  ]
}
