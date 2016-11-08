package main

import (
	"log"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var paperCmd = &cobra.Command{
	Use:   "paper",
	Short: "Add paper to project.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
	},
}

var paperListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available paper templates.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		listTemplates("paper")
	},
}

var paperAddCmd = &cobra.Command{
	Use:   "add <template> <name>",
	Short: "Add paper to the project.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes 1 argument.")
		}
		if !sh.Test("dir", ".git") {
			log.Fatalln("Can't find .git folder. Are you on the root folder of project?")
		}
		addTemplate("paper", args[0], "paper")
	},
}

func init() {
	RootCmd.AddCommand(paperCmd)
	paperCmd.AddCommand(paperListCmd)
	paperCmd.AddCommand(paperAddCmd)
}
