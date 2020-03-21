workflow "test" {
  resolves = "show env"
  on = "push"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}