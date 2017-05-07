package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"path"
	"strings"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var setupSh = []byte(`#!/bin/bash
# Any setup required by the experiment goes here. Things like installing
# packages, allocating resources or deploying software on remote
# infrastructure can be implemented here.
set -e
exit 0
`)

var runSh = []byte(`#!/bin/bash
# This file should contain the series of steps that are required to execute 
# the experiment. Any non-zero exit code will be interpreted as a failure
# by the 'popper check' command.
set -e
exit 0
`)

var validateSh = []byte(`#!/bin/bash
# The point of entry to the validation of results produced by the experiment.
# Any non-zero exit code will be interpreted as a failure by the 'popper check'
# command. Additionally, the command should print "true" or "false" for each
# validation (one per line, each interpreted as a separate validation).
set -e
exit 0
`)

var teardownSh = []byte(`#!/bin/bash
# Put all your cleanup tasks here.
set -e
exit 0
`)

func checkTemplateFolderExists(templateType string) {
	if !sh.Test("dir", popperFolder+"/templates/"+templateType) {
		log.Fatalln("Can't find '" + popperFolder + "/templates/" + templateType + "'." +
			"This command must be executed from the project's root folder.")
	}
}

func showExperimentInfo(experimentName string) {
	checkTemplateFolderExists("experiments")
	if err := sh.Command("cat", popperFolder+"/templates/experiments/"+experimentName+"/README.md").Run(); err != nil {
		log.Fatalln(err)
	}
}

func listTemplates(templateType string) {
	checkTemplateFolderExists(templateType)
	if err := sh.Command("ls", "-1", popperFolder+"/templates/"+templateType).Run(); err != nil {
		log.Fatalln(err)
	}
}

func addTemplate(templateType string, templateName string, folder string) {
	checkTemplateFolderExists(templateType)

	if sh.Test("dir", folder) {
		log.Fatalln("Folder " + folder + " already exists.")
	}

	template := popperFolder + "/templates/" + templateType + "/" + templateName

	if _, err := sh.Command("cp", "-r", template, folder).CombinedOutput(); err != nil {
		log.Fatalln(err)
	}
}

func getRepoInfo() (user, repo string, err error) {
	remoteURL, err := sh.Command(
		"git", "config", "--get", "remote.origin.url").Output()
	if err != nil {
		return
	}
	urlAndUser, repo := path.Split(string(remoteURL))

	// get the user or org name
	user = path.Base(strings.Replace(urlAndUser, ":", "/", -1))

	// trim and remove .git extension, if present
	repo = strings.TrimSuffix(strings.TrimSpace(repo), ".git")

	return
}

func initExperiment(name string) {
	if sh.Test("d", "experiments/"+name) {
		log.Fatalln("Folder " + name + " already exists.")
	}

	if err := sh.Command("mkdir", "-p", "experiments/"+name).Run(); err != nil {
		log.Fatalln(err)
	}

	// create template files
	if err := ioutil.WriteFile("experiments/"+name+"/setup.sh", setupSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/run.sh", runSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/validate.sh", validateSh, 0755); err != nil {
		log.Fatalln(err)
	}
	if err := ioutil.WriteFile("experiments/"+name+"/teardown.sh", teardownSh, 0755); err != nil {
		log.Fatalln(err)
	}

	// add README
	readme := "# " + name + "\n\n"

	// add Popper badge link, only if we can get repo info
	usr, repo, err := getRepoInfo()
	if err == nil {
		badgeUrl := "http://ci.falsifiable.us/" +
			usr + "/" + repo + "/" + name + "/status.svg"

		mdLink := "[![Popper Status](" + badgeUrl + ")](http://falsifiable.us)\n"

		readme = readme + mdLink
	}

	err = ioutil.WriteFile("experiments/"+name+"/README.md", []byte(readme), 0644)
	if err != nil {
		log.Fatalln(err)
	}

	fmt.Println("Initialized " + name + " experiment.")
}

var experimentCmd = &cobra.Command{
	Use:   "experiment",
	Short: "List or add experiments.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		log.Fatalln("Can't use this subcommand directly. See 'popper help experiment' for usage")
	},
}

var experimentListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available experiment templates",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		listTemplates("experiments")
	},
}

var experimentAddCmd = &cobra.Command{
	Use:   "add <template> [<name>]",
	Short: "Add an experiment to the project",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		expname := ""
		if len(args) == 1 {
			expname = args[0]
		} else if len(args) == 2 {
			expname = args[1]
		} else {
			log.Fatalln("Incorrect number of arguments, type 'popper experiment add --help'")
		}
		if !sh.Test("dir", ".git") {
			log.Fatalln("Can't find .git folder. Are you on the root folder of project?")
		}
		addTemplate("experiments", args[0], "experiments/"+expname)

		fmt.Println("Added " + expname + " to experiments/ folder.")
	},
}

var experimentInitCmd = &cobra.Command{
	Use:   "init <name>",
	Short: "Initialize an experiment",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes 1 arguments.")
		}
		if !sh.Test("dir", ".git") {
			log.Fatalln("Can't find .git folder. Are you on the root folder of project?")
		}
		initExperiment(args[0])
	},
}

var experimentInfoCmd = &cobra.Command{
	Use:   "info <name>",
	Short: "Show information about an experiment.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes name of experiment as argument.")
		}
		showExperimentInfo(args[0])
	},
}

func init() {
	RootCmd.AddCommand(experimentCmd)
	experimentCmd.AddCommand(experimentListCmd)
	experimentCmd.AddCommand(experimentAddCmd)
	experimentCmd.AddCommand(experimentInitCmd)
	experimentCmd.AddCommand(experimentInfoCmd)
}
