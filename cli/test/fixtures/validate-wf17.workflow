workflow "test" {
  resolves = "show env"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}

action "show env again" {
  uses = "popperized/bin/sh@master"
  needs = ["show env"]
  args = "ls"
}