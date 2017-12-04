package main

import (
	"fmt"
	"log"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

func addPipeline(templateType string, templateName string, folder string) {
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
	Use:   "add <pipeline> [<name>]",
	Short: "Add a pipeline to the project",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		expname := ""
		if len(args) == 1 {
			expname = args[0]
		} else if len(args) == 2 {
			expname = args[1]
		} else {
			log.Fatalln("Incorrect number of arguments, type 'popper add --help'")
		}
		if !sh.Test("dir", ".git") {
			log.Fatalln("Can't find .git folder. Are you on the root folder of project?")
		}

		if strings.HasPrefix(args[0], "paper-") {
			addPipeline("paper", args[0], "paper/")
		} else {
			// create pipelines folder if it doesn't exist
			if err := sh.Command("mkdir", "-p", "pipelines/").Run(); err != nil {
				log.Fatalln(err)
			}
			addPipeline("pipelines", args[0], "pipelines/"+expname)
		}

		fmt.Println("Added " + expname + " to pipelines/ folder.")
	},
}

func init() {
	// RootCmd.AddCommand(addCmd)
}
