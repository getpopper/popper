package main

import (
	"fmt"
	"log"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

func updateTemplates() (err error) {
	if err = sh.Command("git", "-C", popperFolder, "reset", "--hard", "origin/master").Run(); err != nil {
		log.Fatalln(err)
	}
	if err = sh.Command("git", "-C", popperFolder, "pull").Run(); err != nil {
		log.Fatalln(err)
	}
	if err = sh.Command("git", "-C", popperFolder, "submodule", "update", "--init", "--recursive").Run(); err != nil {
		log.Fatalln(err)
	}
	return nil
}

var updateCmd = &cobra.Command{
	Use:   "update",
	Short: "Updates pipelines metadata cache.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		// if err := updateTemplates(); err != nil {
		// 	log.Fatalln(err)
		// }
		if err := sh.Command("docker", "pull", "ivotron/poppercheck").Run(); err != nil {
			log.Fatalln(err)
		}
		fmt.Println("Updated Popper repository successfully.")
	},
}

func init() {
	RootCmd.AddCommand(updateCmd)
}
