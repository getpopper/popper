workflow "test" {
  resolves = "show env"
}

action "show env" {
  uses = "popperized/bin/sh@master"
  args = {
    FIRST_NAME  = "Mona"
    MIDDLE_NAME = "Lisa"
    LAST_NAME   = "Octocat"
  }
}