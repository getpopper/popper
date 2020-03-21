workflow "test" {
  resolves = "secrets good"
}

action "secrets good" {
  uses = "popperized/bin/sh@master"
  args = "ls"
  env = {
    F_NAME = "F_NAME",
    L_NAME = "L_NAME"
  }
  secrets = ["F_NAME", "L_NAME"]
}