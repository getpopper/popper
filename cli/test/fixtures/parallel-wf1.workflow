workflow "sample" {
  resolves = ["stage_one"]
}

action "one" {
  uses = "docker://busybox"
  args = ["echo", "Hello from busybox"]
}

action "two" {
  uses = "popperized/bin/curl@master"
  args = ["google.com"]
}

action "three" {
  uses = "popperized/bin/sh@master"
  runs = ["sh", "-c", "echo Hello from sh"]
}

action "four" {
  uses = "popperized/npm@master"
  args = ["--version"]
}

action "stage_one" {
  uses = "docker://debian:buster-slim"
  args = ["apt", "--version"]
  needs = [
    "one",
    "two",
    "three",
    "four"
  ]
}