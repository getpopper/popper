workflow "cli tests" {
  on = "push"
  resolves = "end"
}

action "lint" {
  uses = "popperized/bin/shellcheck@master"
  args = "./ci/test/*"
}

action "test ci" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/ci"
}

action "test reuse" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/reuse"
}

action "test actions-demo" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/actions-demo"
}

action "test validate" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/validate"
}

action "test scaffold" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/scaffold"
}

action "test dry-run" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/dry-run"
}

action "test parallel" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/parallel"
}

action "test dot" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/dot"
}

action "test interrupt" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/interrupt"
}

action "test quiet" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/quiet"
}

action "test sh" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/sh"
}

action "test skip" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/skip"
}

action "test search" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/search"
}

action "test offline" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/offline"
}

action "test inject" {
  needs = "lint"
  uses = "sh"
  args = "ci/test/inject"
}

action "end" {
  uses = "sh"
  args = "ci/test/version"
  needs = [
    "test actions-demo",
    "test ci",
    "test dot",
    "test dry-run",
    "test interrupt",
    "test parallel",
    "test quiet",
    "test reuse",
    "test scaffold",
    "test validate",
    "test skip",
    "test sh",
    "test search",
    "test offline",
    "test inject"
  ]
}
