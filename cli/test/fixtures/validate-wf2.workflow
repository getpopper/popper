workflow "test" {
  resolves = "show env"
  attr1 = "attr1"
  attr2 = "attr2"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}