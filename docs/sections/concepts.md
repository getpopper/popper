# Concepts

The main three concepts behind Popper are Linux containers, the 
container-native paradigm, and workflows. This page is under 
construction, we plan on expanding it with our own content 
(contributions are [more than 
welcome](https://github.com/getpopper/popper/issues/822))! For now, we 
provide with a list of external resources and a Glossary.

## Resources

Container Concepts:

  * [Overview of Containers in Red Hat Systems (Red Hat)](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_atomic_host/7/html/overview_of_containers_in_red_hat_systems/introduction_to_linux_containers)
  * [An Introduction to Containers (Rancher)](https://rancher.com/blog/2019/an-introduction-to-containers)
  * [A Beginner-Friendly Introduction to Containers, VMs and Docker (freecodecamp.org)](https://www.freecodecamp.org/news/a-beginner-friendly-introduction-to-containers-vms-and-docker-79a9e3e119b)
  * [A Practical Introduction to Container Terminology (Red Hat)](https://developers.redhat.com/blog/2018/02/22/container-terminology-practical-introduction/)

Container-native paradigm:

  * [5 Reasons You Should Be Doing Container-native Development (Microsoft)](https://cloudblogs.microsoft.com/opensource/2018/04/23/5-reasons-you-should-be-doing-container-native-development/)
  * [Let's Define "Container-native" (TechCrunch)](https://techcrunch.com/2016/04/27/lets-define-container-native/)
  * [The 7 Characteristics of Container-native Infrastructure (Joyent)](https://www.joyent.com/blog/the-seven-characteristics-of-container-native-infrastructure)

Docker:

  * [A Docker tutorial for beginners](https://docker-curriculum.com/)
  * [Dockerfile tutorial by example](https://takacsmark.com/dockerfile-tutorial-by-example-dockerfile-best-practices-2018/#what-is-a-dockerfile-and-why-youd-want-to-use-one)

Singularity:

  * [Introduction to Singularity](https://sylabs.io/guides/3.5/user-guide/introduction.html)

## Glossary

  * **Linux containers**. An OS-level virtualization technology for 
    isolating applications in a Linux host machine.

  * **Container runtime**. The software that interacts with the Linux 
    kernel in order to provide with container primitives to 
    upper-level components such as a container engine (see "Container 
    Engine"). Examples of runtimes are 
    [runc](https://github.com/opencontainers/runc), 
    [Kata](https://github.com/kata-containers/runtime) and 
    [crun](https://github.com/containers/crun).

  * **Container engine**. Container management software that provides 
    users with an interface to. Examples of engines are 
    [Docker](https://github.com/docker/docker-ce), 
    [Podman](https://github.com/containers/libpod) and 
    [Singularity](https://github.com/hpcng/singularity).

  * **Container-native development**. An approach to writing software 
    that makes use of containers at every stage of the software 
    delivery cycle (building, testing, deploying, etc.). In practical 
    terms, when following a container-native paradigm, other than a 
    text editor or ID, dependencies required to develop, test or 
    deploy software are NEVER installed directly on your host 
    computer. Instead, they are packaged in container images and you 
    make use of them through a container engine.

  * **Workflow**. A series of steps, where each step specifies what it 
    does, as well as which other steps need to be executed prior to 
    its execution. It is commonly represented as a directed acyclic 
    graph (DAG), where each node represents a step. The word 
    "pipeline" is usually used interchangeably to refer to a workflow.

  * **Task or Step**. A node in a workflow DAG.

  * **Container-native workflow**. A workflow where each step runs in 
    a container.

  * **Container-native task or step**. A step in a container-native 
    workflow that specifies the image it runs, the arguments that are 
    executed, the environment available inside the container, among 
    other attributes available for containers (network configuration, 
    resource limits, capabilities, volumes, etc.).
