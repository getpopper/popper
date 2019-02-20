workflow "cli tests" {
  on = "push"
  resolves = "end"
}

action "test init" {
  uses = "./test-init.sh"
}

action "test metadata" {
  uses = "./test-metadata.sh"
}

action "test ci" {
  uses = "./test-ci.sh"
}

action "end" {
  uses = "show-version.sh"
  needs = [
    "test init"
    "test metadata"
    "test ci"
  ]
}
