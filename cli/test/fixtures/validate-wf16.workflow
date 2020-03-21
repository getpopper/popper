workflow "test" {
  resolves = "show env"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  needs = 12
  args = "ls"
}