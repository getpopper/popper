workflow "wf" {
  resolves = "post2"
}

action "post1" {
  uses = "sh"
  runs = "echo post1-action"
}

action "post2" {
  needs= "post1"
  uses = "sh"
  runs = "echo post2-action"
}