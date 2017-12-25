package main

import (
	"fmt"
	"io/ioutil"
	"log"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
	"github.com/theherk/viper"
)

var envFlagValue string

var setupSh = []byte(`#!/bin/bash
# [wf] any setup required by the pipeline.
# Things like installing packages, allocating resources
# or deploying software on remote infrastructure can be implemented here.
set -e

# add commands here:

exit 0
`)

var runSh = []byte(`#!/bin/bash
# [wf] series of steps required to execute the pipeline.
# This file should contain the series of steps that are required to execute
# the pipeline. Any non-zero exit code will be interpreted as a failure
# by the 'popper check' command.
set -e

# add commands here:

exit 0
`)

var postRunSh = []byte(`#!/bin/bash
# [wf] run post-processing tasks
# Any post-run tasks should be included here. For example, post-processing
# of output data, or updating a dataset with results of execution. Any
# non-zero exit code will be interpreted as a failure by the 'popper check'
# command.
set -e

# add commands here:

exit 0
`)

var validateSh = []byte(`#!/bin/bash
# [wf] validate the output of pipeline.
# The point of entry to the validation of results produced by the pipeline.
# Any non-zero exit code will be interpreted as a failure by the 'popper check'
# command. Additionally, the command should print "true" or "false" for each
# validation (one per line, each interpreted as a separate validation).
set -e

# add commands here:

exit 0
`)

var teardownSh = []byte(`#!/bin/bash
# [wf] cleanup tasks.
# Put all your cleanup tasks here.
set -e
exit 0
`)

func initPipeline(name string) {
	if sh.Test("d", "pipelines/"+name) {
		log.Fatalln("Folder " + name + " already exists.")
	}

	if err := sh.Command("mkdir", "-p", "pipelines/"+name).Run(); err != nil {
		log.Fatalln(err)
	}

	if err := ioutil.WriteFile("pipelines/"+name+"/setup.sh", setupSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("pipelines/"+name+"/run.sh", runSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("pipelines/"+name+"/post-run.sh", runSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("pipelines/"+name+"/validate.sh", validateSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("pipelines/"+name+"/teardown.sh", teardownSh, 0755); err != nil {
		log.Fatalln(err)
	}

	// add environment to .popper.yml
	err := readPopperConfig()
	if err != nil {
		log.Fatalln(err)
	}
	values := map[string]string{}
	if viper.IsSet("envs") {
		values = viper.GetStringMapString("envs")
	}
	values[name] = envFlagValue
	viper.Set("envs", values)
	viper.WriteConfig()

	// add README
	readme := "# " + name + "\n"

	err = ioutil.WriteFile("pipelines/"+name+"/README.md", []byte(readme), 0644)
	if err != nil {
		log.Fatalln(err)
	}

	fmt.Println("Initialized " + name + " pipeline.")
}

var initCmd = &cobra.Command{
	Use:   "init [<name>]",
	Short: "Initializes a repository, pipeline or paper folder.",
	Long: `Without any arguments, this command initializes a popper repository. If
an argument is given, an pipeline or paper folder is initialized. If the given
name is 'paper', then a 'paper' folder is created. Otherwise, an pipeline named
'name' is created.`,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 1 {
			log.Fatalln("This command takes one argument at most.")
		}
		err := initPopperFolder()
		if err != nil {
			log.Fatalln(err)
		}
		if !sh.Test("dir", ".git") {
			log.Fatalln("Can't find .git folder. Are you on the root folder of project?")
		}
		if len(args) == 0 {
			if sh.Test("file", ".popper.yml") {
				log.Fatalln("File .popper.yml already exists")
			}
			err = ioutil.WriteFile(".popper.yml", []byte(""), 0644)
			if err != nil {
				log.Fatalln(err)
			}
			fmt.Println("Initialized popper repository.")
		} else {
			initPipeline(args[0])
		}
	},
}

func init() {
	initCmd.Flags().StringVarP(&envFlagValue, "env", "e", "host", "Environment where popper check will run.")
	RootCmd.AddCommand(initCmd)
}
