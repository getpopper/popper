package main

import (
	"log"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initializes a popper repository.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}

		// check for git repo and popperized repo
		if sh.Test("file", ".popper.yml") {
			log.Fatalln("Looks like this repo is already popperized (.popper.yml exists).")
		}

		repo, err := get_templates()
		if err != nil {
			log.Fatalln(err)
		}

		if _, err := sh.Command("mkdir", "experiments").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}

		// mark repo as popperized
		if _, err := sh.Command("echo", repo).Command("tee", "-a", ".popper.yml").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}
	},
}

func init() {
	RootCmd.AddCommand(initCmd)
}
