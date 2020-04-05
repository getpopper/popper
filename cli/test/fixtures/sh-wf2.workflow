workflow "test" {
    resolves = ["sh"]
}

action "sh" {
    uses = "sh"
    runs = ["cli/test/fixtures/sh-script"]
    args = ["Popper"]
}