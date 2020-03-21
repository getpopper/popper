workflow "test" {
  resolves = "secrets wrong"
}

action "secrets wrong" {
  uses = "popperized/bin/sh@master"
  args = "ls"
  secrets = {
    key =  "value"
  }
}