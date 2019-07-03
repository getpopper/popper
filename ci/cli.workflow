workflow "cli tests" {
  on = "push"
  resolves = "end"
}
action "lint" {
  uses = "actions/bin/shellcheck@master"
  args = "./ci/test/*"
}

action "test ci" {
  needs = "lint"
  uses = "./ci/test"
  runs = "ci"
}

action "test reuse" {
  needs = "lint"
  uses = "./ci/test"
  runs = "reuse"
}

action "test actions-demo" {
  needs = "lint"
  uses = "./ci/test"
  runs = "actions-demo"
}

action "test validate" {
  needs = "lint"
  uses = "./ci/test"
  runs = "validate"
}

action "test scaffold" {
  needs = "lint"
  uses = "./ci/test"
  runs = "scaffold"
}

action "test recursive" {
  needs = "lint"
  uses = "./ci/test"
  runs = "recursive"
}

action "test dry-run" {
  needs = "lint"
  uses = "./ci/test"
  runs = "dry-run"
}

action "test parallel" {
  needs = "lint"
  uses = "./ci/test"
  runs = "parallel"
}

action "test dot" {
  needs = "lint"
  uses = "./ci/test"
  runs = "dot"
}

action "test interrupt" {
  needs = "lint"
  uses = "./ci/test"
  runs = "interrupt"
}

action "test add" {
  needs = "lint"
  uses = "./ci/test"
  runs = "add"
}

action "test quiet" {
  needs = "lint"
  uses = "./ci/test"
  runs = "quiet"
}

action "test sh" {
  needs = "lint"
  uses = "./ci/test"
  runs = "sh"
}

action "test skip" {
  needs = "lint"
  uses = "./ci/test"
  runs = "skip"
}

action "test search" {
  needs = "lint"
  uses = "./ci/test"
  runs = "search"
}

action "test offline" {
  needs = "lint"
  uses = "./ci/test"
  runs = "offline"
}

action "test samples" {
  needs = "lint"
  uses = "./ci/test"
  runs = "samples"
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
    // "test interrupt",
    "test parallel",
    "test quiet",
    "test recursive",
    "test reuse",
    "test scaffold",
    "test validate",
    "test skip",
    "test sh",
    "test search",
    "test samples",
    "test offline"
  ]
}
