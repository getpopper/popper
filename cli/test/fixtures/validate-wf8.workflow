workflow "test" {
  resolves = "show env"
  on = ["push", "pull"]
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}