workflow "test" {
    resolves = ["sh"]
}

action "sh" {
    uses = "sh"
    runs = ["ls", "-l"]
}