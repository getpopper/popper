workflow "example" {
resolves = "end"
}

action "a" {
uses = "sh"
args = "ls"
}

action "b" {
uses = "sh"
args = "ls"
}

action "c" {
uses = "sh"
args = "ls"
}

action "d" {
needs = ["c"]
uses = "sh"
args = "ls"
}

action "e" {
needs = ["d", "b", "a"]
uses = "sh"
args = "ls"
}

action "end" {
needs = "e"
uses = "sh"
args = "ls"
}
