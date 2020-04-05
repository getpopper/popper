workflow "wf" {
  resolves = "c"
}

action "a" {
  uses = "sh"
  runs = "ls"
}

action "b" {
  needs = ["a"]
  uses = "sh"
  runs = "ls"
}

action "c" {
  needs = ["b"]
  uses = "sh"
  runs = "ls"
}