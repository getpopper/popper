workflow "test" {
  resolves = "show env"
}

acccction "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}