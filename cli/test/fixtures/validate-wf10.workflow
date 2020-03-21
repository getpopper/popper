workflow "test" {
  resolves = "show env"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
  attr1 = "attr1"
  attr2 = "attr2"
}