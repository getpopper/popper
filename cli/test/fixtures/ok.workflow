workflow "sample" {
    resolves = ["reachable"]
}
action "reachable" {
    uses = "popperized/bin/sh@master"
    args = "ls"
}
action "unreachable" {
    uses = "popperized/bin/sh@master"
    args = ["ls -ltr"]
}
