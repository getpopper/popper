workflow "samples" {
    resolves = ["c"]
}
action "b" {
    uses = "sh"
}
action "c" {
    uses = "sh"
    needs = "a"
}
