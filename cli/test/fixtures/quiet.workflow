workflow "sample" {
    resolves = "test"
}

action "test" {
    uses = "docker://busybox"
    args = ["ls", "-ltr"]
}