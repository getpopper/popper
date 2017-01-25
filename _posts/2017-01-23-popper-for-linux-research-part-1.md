---
layout: post
title: "A Popper Template for Linux Kernel Research (part 1)"
---

> **TLDR**: We describe how to follow the Popper convention to manage 
and automate experiments that modify the Linux Kernel. This first part
deals with building the kernel and provisioning a VM. In part 2, we 
cover the experiment execution and validation of results using this 
template.

A typical exploration involving Linux consists of code that implements 
one or more new features in the kernel, and then run experiments in 
order to test a hypothesis. In this case, Popper is followed to manage 
and track the changes done to the experiment, analysis and validation 
of results.

Requirements:

  * [Git](http://git-scm.org)
  * [Docker](http://docker.com)
  * [Vagrant](http://vagrantup.com)
  * [Virtualbox](http://virtualbox.org)

In this post we will show how to hack the kernel in a DevOps oriented 
way by following Popper, with the goal of making it easier for others 
to reproduce results.

![]({{ site.baseurl }}/images/popper-template-linux-kernel-1.png)

The above diagram depicts the series of steps that we will go over in 
some level of detail:

 1. Create a repository for your experiment (0).
 2. Fork the kernel repo and clone it into your machine (1, 2).
 3. Build new kernel packages (3, 4, 5).
 4. Provision a VM with the custom kernel (6, 7).

For 3 and 4, we will create scripts and, for illustration purposes, we 
will write these scripts from scratch. These scripts are part of a 
Popper template, so one can avoid writing them from scratch by quickly 
importing it to an existing Git repository (see last last section).

## Creating a Repo for the Experiment {#gitrepo}

We want to create a repository that will hold the scripts, tests, 
analysis, results and possibly a manuscript describing all. In order 
to do that, we first initialize a git repository:

```bash
$ mkdir mypaper
$ cd mypaper
$ git init
Initialized empty Git repository in mypaper/.git/

$ echo "# repository on " > README.md
$ git commit -m "first commit"
```

For more on how to [_Learn Enough Git to be 
Dangerous_](https://www.learnenough.com/git-tutorial), see 
[here](https://swcarpentry.github.io/git-novice/), 
[here](http://v4.software-carpentry.org/vc/intro.html), or 
[here](https://medium.com/flow-ci/github-vs-bitbucket-vs-gitlab-vs-coding-7cf2b43888a1#.3czk4nrfs). 

We then create a repository at GitHub and link it to the local 
repository that was just created. To do this, you need an account at 
GitHub (see a guide 
[here](https://help.github.com/articles/creating-a-new-repository/)). 
Once this is done, the repository is linked by doing the following:

```bash
$ git remote add origin $your_repo_url
```

where `$your_repo_url` is the URL to the repository at GitHub.

## Add the kernel source repo {#submodule}

We now will add a kernel source repository as a "sub-repository" to 
the `mypaper` repo that we just created above. To do so, we first fork 
the kernel source repository at <https://github.com/torvalds/linux>. 
To fork the repository, you need an account at GitHub. For more info 
on how to fork a repo, take a look at [this 
guide](https://help.github.com/articles/fork-a-repo).

Once you have a repo (we'll assume this repo resides at 
<https://github.com/$youruser/linux>), then you need to add it to the 
`mypaper` repository as a submodule. To do so:

```bash
$ cd mypaper
$ mkdir -p experiments/kernel-experiment
$ git submodule add https://github.com/$youruser/linux experiments/kernel-experiment/linux
$ git commit -m "adding my kernel repository as a submodule"
```

To learn more about submodules, see 
[here](https://github.com/blog/2104-working-with-submodules), 
[here](https://git-scm.com/book/en/v2/Git-Tools-Submodules) or 
[here](https://medium.com/@porteneuve/mastering-git-submodules-34c65e940407).

## Build Kernel Packages

Now, we want to build the kernel in a reproducible manner. One way to 
do this is to use Docker. We create a 
`experiments/kernel-experiment/docker` folder and create an image with 
all the dependencies of our build environment. Instead of pasting the 
contents of this folder, you can take a look at them 
[here](https://github.com/systemslab/popper/tree/master/templates/experiments/linux-cgroups/docker). 
To learn more about Docker visit [this 
page](https://docs.docker.com/engine/getstarted/).

This container automates all the steps involved in building a kernel. 
To build, we do the following:

```bash
#!/bin/bash
set -e -x

# build the container
docker build -t kernel-ci docker/

# build the kernel by passing the source folder
docker run --rm -ti \
  -v `pwd`/linux:/linux \
  kernel-ci

mv linux/*deb vagrant/debs/
```

The script above is placed in a 
`experiments/kernel-experiment/build-kernel.sh` script and becomes 
part of the `mypaper` repo.

## Provision a VM with new Packages

In order to test our kernel, we'll use a VirtualBox VM. Instead of 
interacting directly with the VirtualBox commands, we use the awesome 
Vagrant tool. We first grab a vagrant box that runs Debian Jessie. 
This is done by defining a `Vagrantfile` like the following:

```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "debian/jessie64"

  # Enable provisioning with a shell script.
  config.vm.provision "shell", inline: <<-SHELL
    sudo dpkg -i /vagrant/debs/*.deb
  SHELL
end
```

The above script can be placed in a 
`experiments/kernel-experiment/vagrant/` folder. The output of the 
building process described in the previous section generates packages 
and puts them in this `experiments/kernel-experiment/vagrant/debs` 
folder. In order to provision the VM with these packages, we do:

```bash
#!/bin/bash
set -e -x

# bring the VM up
vagrant up

# provision
vagrant reload --provision
vagrant reload
```

Again, we put the above script in the 
`experiments/kernel-experiment/vagrant/provision.sh` script so this 
becomes part of our `mypaper` repository. After the above executes, we 
have a VM running with our customized kernel. To login to the VM, we 
can do:

```bash
$ cd mypaper/experiments/kernel-experiment/vagrant/
$ vagrant ssh

vagrant@jessie:~$ uname -a
Linux jessie 4.9.0-ci #3 SMP Wed Jan 25 01:00:13 UTC 2017 x86_64 
GNU/Linux
```

To learn more about Vagrant, look at 
[here](https://www.vagrantup.com/docs/getting-started/).

# Importing the Popper Template

The scripts that we created in the previous sections are part of a 
Popper template, so one can avoid writing them from scratch by quickly 
importing the template to a repository. To do so, install the Popper 
CLI and, assuming you have already create the `mypaper` repo (first 
[subsection](#gitrepo) above), we do:

```bash
$ popper init
$ popper experiment add linux-cgroups
```

You can ignore for now why this template is named `linux-cgroups`. 
(after reading [part 
2](http://falsifiable.us/popper-for-linux-research-part-2) this will 
make more sense). Next, add the submodule for the Linux repository as 
[we did in above](#submodule).
