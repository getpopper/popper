workflow "test" {
  resolves = "show env"
}

action "show env" {
  uses = 123
  args = "ls"
}