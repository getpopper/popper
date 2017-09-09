package main

import (
	"fmt"
	"io/ioutil"
	"log"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var setupSh = []byte(`#!/bin/bash
# Any setup required by the experiment goes here. Things like installing
# packages, allocating resources or deploying software on remote
# infrastructure can be implemented here.
set -e

# add commands here:

exit 0
`)

var runSh = []byte(`#!/bin/bash
# This file should contain the series of steps that are required to execute 
# the experiment. Any non-zero exit code will be interpreted as a failure
# by the 'popper check' command.
set -e

# add commands here:

exit 0
`)

var postRunSh = []byte(`#!/bin/bash
# Any post-run tasks should be included here. For example, post-processing
# of output data, or updating a dataset with results of execution. Any
# non-zero exit code will be interpreted as a failure by the 'popper check'
# command.
set -e

# add commands here:

exit 0
`)

var validateSh = []byte(`#!/bin/bash
# The point of entry to the validation of results produced by the experiment.
# Any non-zero exit code will be interpreted as a failure by the 'popper check'
# command. Additionally, the command should print "true" or "false" for each
# validation (one per line, each interpreted as a separate validation).
set -e

# add commands here:

exit 0
`)

var teardownSh = []byte(`#!/bin/bash
# Put all your cleanup tasks here.
set -e
exit 0
`)

func initExperiment(name string) {
	if sh.Test("d", "experiments/"+name) {
		log.Fatalln("Folder " + name + " already exists.")
	}

	if err := sh.Command("mkdir", "-p", "experiments/"+name).Run(); err != nil {
		log.Fatalln(err)
	}

	if err := ioutil.WriteFile("experiments/"+name+"/setup.sh", setupSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/run.sh", runSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/post-run.sh", runSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/validate.sh", validateSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/teardown.sh", teardownSh, 0755); err != nil {
		log.Fatalln(err)
	}

	// add README
	readme := "# " + name + "\n"

	err := ioutil.WriteFile("experiments/"+name+"/README.md", []byte(readme), 0644)
	if err != nil {
		log.Fatalln(err)
	}

	fmt.Println("Initialized " + name + " experiment.")
}

var initCmd = &cobra.Command{
	Use:   "init <name>",
	Short: "Initializes an experiment or paper folder.",
	Long: `Initializes an experiment or paper folder. If the given name is 'paper',
then a 'paper' folder is created. Otherwise, an experiment named 'name'
is created.`,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes one argument.")
		}
		if !sh.Test("dir", ".git") {
			log.Fatalln("Can't find .git folder. Are you on the root folder of project?")
		}
		initExperiment(args[0])
	},
}

func init() {
	RootCmd.AddCommand(initCmd)
}
