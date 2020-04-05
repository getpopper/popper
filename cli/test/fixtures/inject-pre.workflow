workflow "wf" {
  resolves = "pre"
}

action "pre" {
  uses = "sh"
  runs = "echo pre-action"
}