package main

import (
	"log"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

func checkTemplateFolderExists(template_type string) {
	if !sh.Test("dir", ".popper_files/"+template_type) {
		log.Fatalln("Can't find '.popper_files/" + template_type + "'." +
			"This command must be executed from the project's root folder.")
	}
}

func listTemplates(template_type string) {
	checkTemplateFolderExists(template_type)
	if err := sh.Command("ls", "-1", ".popper_files/"+template_type).Run(); err != nil {
		log.Fatalln(err)
	}
}

func addTemplate(template_type string, template_name string, folder string) {
	checkTemplateFolderExists(template_type)

	if sh.Test("dir", folder) {
		log.Fatalln("Folder " + folder + " already exists.")
	}

	template := ".popper_files/" + template_type + "/" + template_name

	if _, err := sh.Command("cp", "-r", template, folder).CombinedOutput(); err != nil {
		log.Fatalln(err)
	}
}

var experimentCmd = &cobra.Command{
	Use:   "experiment",
	Short: "List or add experiments.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
	},
}

var experimentListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available experiment templates.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		listTemplates("experiments")
	},
}

var experimentAddCmd = &cobra.Command{
	Use:   "add <template> <name>",
	Short: "Add an experiment to the project.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 2 {
			log.Fatalln("This command takes 2 arguments.")
		}
		if !sh.Test("dir", "experiments") {
			if _, err := sh.Command("mkdir", "experiments").CombinedOutput(); err != nil {
				log.Fatalln(err)
			}
		}
		addTemplate("experiments", args[0], "experiments/"+args[1])
	},
}

func init() {
	RootCmd.AddCommand(experimentCmd)
	experimentCmd.AddCommand(experimentListCmd)
	experimentCmd.AddCommand(experimentAddCmd)
}
