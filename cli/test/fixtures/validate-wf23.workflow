workflow "test" {
  resolves = "test env-good"
}

action "test env-good" {
  uses = "popperized/bin/sh@master"
  args = "ls"
  env = {
    F_NAME = "F_NAME",
    L_NAME = "L_NAME"
  }
}