workflow "cli tests" {
  on = "push"
  resolves = "end"
}

action "test init" {
  uses = "./ci/tests"
  runs = "test-init.sh"
}

action "test metadata" {
  uses = "./ci/tests"
  runs = "test-metadata.sh"
}

action "test ci" {
  uses = "./ci/tests"
  runs = "test-ci.sh"
}

action "end" {
  uses = "./ci/tests"
  runs = "show-version.sh"
  needs = [
    "test init",
    "test metadata",
    "test ci"
  ]
}
