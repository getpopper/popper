workflow "test" {
  resolves = 1
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}