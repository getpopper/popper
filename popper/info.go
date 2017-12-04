package main

import (
	"log"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

func checkTemplateFolderExists(templateType string) {
	if !sh.Test("dir", popperFolder+"/templates/"+templateType) {
		log.Fatalln("Can't find '" + popperFolder + "/templates/" + templateType + "'." +
			"This command must be executed from the project's root folder.")
	}
}

func showPipelineInfo(pipelineName string) {
	checkTemplateFolderExists("pipelines")
	if err := sh.Command("cat", popperFolder+"/templates/pipelines/"+pipelineName+"/README.md").Run(); err != nil {
		log.Fatalln(err)
	}
}

var infoCmd = &cobra.Command{
	Use:   "info <name>",
	Short: "Show information about an pipeline.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes name of pipeline as argument.")
		}
		showPipelineInfo(args[0])
	},
}

func init() {
	// RootCmd.AddCommand(infoCmd)
}
