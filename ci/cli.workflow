workflow "cli tests" {
  on = "push"
  resolves = "end"
}

action "test init" {
  uses = "./tests"
  runs = "test-init.sh"
}

action "test metadata" {
  uses = "./tests"
  runs = "test-metadata.sh"
}

action "test ci" {
  uses = "./tests"
  runs = "test-ci.sh"
}

action "end" {
  uses = "./tests"
  runs = "show-version.sh"
  needs = [
    "test init",
    "test metadata",
    "test ci"
  ]
}
