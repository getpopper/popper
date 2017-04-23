package main

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
)

var updateCmd = &cobra.Command{
	Use:   "update",
	Short: "Updates the templates cache.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		if err := updateTemplates(); err != nil {
			log.Fatalln(err)
		}
		fmt.Println("Updated Popper repository successfully.")
	},
}

func init() {
	RootCmd.AddCommand(updateCmd)
}
