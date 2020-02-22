workflow "example" {
    resolves = ["end"]
}

action "a" {
    uses = "sh"
    args = "ls"
}

action "b" {
    needs = "a"
    uses = "sh"
    args = "ls"
}

action "c" {
    uses = "sh"
    args = "ls"
}

action "d" {
    uses = "sh"
    needs = ["b", "c"]
    args = "ls"
}

action "g" {
    needs = "d"
    uses = "sh"
    args = "ls"
}

action "f" {
    needs = "d"
    uses = "sh"
    args = "ls"
}

action "h" {
    needs = "g"
    uses = "sh"
    args = "ls"
}

action "end" {
    needs = ["h", "f"]
    uses = "sh"
    args = "ls"
}
