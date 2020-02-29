workflow "wf" {
  resolves = "d"
}

action "a1" {
  uses = "sh"
  runs = "ls"
}

action "a2" {
  uses = "sh"
  runs = "ls"
}

action "b" {
  needs = ["a1", "a2"]
  uses = "sh"
  runs = "ls"
}

action "c" {
  needs = ["a1", "a2"]
  uses = "sh"
  runs = "ls"
}

action "d" {
  needs = ["b", "c"]
  uses = "sh"
  runs = "ls"
}