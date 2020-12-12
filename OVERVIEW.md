# Popper Overview

## The Container-Native Concept
The container-native concept is one we have seen rise to prominence in recent years as technologies like Docker and Kubernetes have become more commonplace. Container-native software is software purposely designed for container usage. The basic unit of computation is indeed a container for container-native software, not virtual machines or metal servers. The customer pays by container and provisions only containers, not bare metal or VM clusters. While on the other hand, non container-native services will require pre-provisioning and paying for VMs/bare metal which will higher costs significantly. 

## Where Container-Native Development Helps
A few examples of container native development are builds using Docker, tests run in containers, and testing and debugging cycles done against containers not locally running apps. Each container has its own IP stack separate to its host network, and a container hypervisor ensures there is isolated security for each container so malicious broken/code in a certain container will not affect other containers. We see the benefits of these properties in several instances. Container-native development avoids bugs that occur across environments such as successfully locally testing a Node.js app on a macbook, for example, but failing to run the same build on a Kubernetes cluster. Having a container-native development system when testing will cause  this type of issue to not be a concern anymore.

## Technologies 
Docker is a tool that allows developers to easily deploy their applications in containers and run on a host operating system such as Linux. Applications can be packaged into standardized units with all its dependencies. This is more efficient than utilizing virtual machines. Docker is an example of a container engine that Popper can be used with to define and execute workflows. 

## Where Popper Fits In
Popper is a Github Actions workflow execution engine. The GHA workflow language lets users to implement automated and portable workflows that are easy to extend to others and re-execute. Popper is a tool for defining and executing container-native workflows in Docker as well as other container engines. With Popper a workflow can simply be defined in a YAML file and be executed with simply one command. Popper supports several distinct container engines such as Docker, Singularity, and Podman. Along with this, workflows to be executed on a variety of resource managers/schedulers such as Kubernetes and SLURM while leaving the YAML file in the same format. Workflow development is also made simpler due to aid in the implementation and debugging of workflows along with many examples to use as reference.

