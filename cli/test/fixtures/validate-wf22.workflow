workflow "test" {
  resolves = "show env"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
  env = [1, 2]
}