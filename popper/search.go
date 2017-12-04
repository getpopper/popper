package main

import (
	"log"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

func listAvailableExperiments(templateType string) {
	checkTemplateFolderExists(templateType)
	if err := sh.Command("ls", "-1", popperFolder+"/templates/"+templateType).Run(); err != nil {
		log.Fatalln(err)
	}
}

var searchCmd = &cobra.Command{
	Use:   "search",
	Short: "Search for available experiments",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		listAvailableExperiments("experiments")
	},
}

func init() {
	// RootCmd.AddCommand(searchCmd)
}
