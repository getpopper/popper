workflow "test" {
  resolves = "show env"
}

workflow "test two" {
  resolves = "show env"
}

workflow "test three" {
  resolves = "show env"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}

action "show env one" {
  uses = "popperized/bin/sh@master"
  args = "ls"
}