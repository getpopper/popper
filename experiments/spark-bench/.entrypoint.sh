#!/bin/bash

ssh-add -l

mkdir /root/.ssh
echo 'Host *' > /root/.ssh/config
echo 'StrictHostKeyChecking no' >> /root/.ssh/config
echo 'LogLevel quiet' >> /root/.ssh/config

ansible all -i machines -m ping
echo "" > ansible.log
ansible-playbook -e @vars.yml playbook.yml
