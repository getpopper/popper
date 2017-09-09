package main

import (
	"fmt"
	"log"
	"path"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

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

func addExperiment(templateType string, templateName string, folder string) {
	checkTemplateFolderExists(templateType)

	if sh.Test("dir", folder) {
		log.Fatalln("Folder " + folder + " already exists.")
	}

	template := popperFolder + "/templates/" + templateType + "/" + templateName

	if _, err := sh.Command("cp", "-r", template, folder).CombinedOutput(); err != nil {
		log.Fatalln(err)
	}
}

var addCmd = &cobra.Command{
	Use:   "add <experiment> [<name>]",
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
		if strings.HasPrefix(args[0], "paper-") {
			addExperiment("paper", args[0], "paper/")
		} else {
			addExperiment("experiments", args[0], "experiments/"+expname)
		}

		fmt.Println("Added " + expname + " to experiments/ folder.")
	},
}

func init() {
	RootCmd.AddCommand(addCmd)
}
