workflow "test" {
  foo = "bar"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}