package main

import (
	"fmt"
	"log"
	"os"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var initCmd = &cobra.Command{
	Use:   "init [<folder>]",
	Short: "Initializes a popper repository.",
	Long:  "If <folder> is given then the repository is created in that folder, otherwise in the current directory.",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 1 {
			log.Fatalln("This command takes at most one argument.")
		}

		if len(args) == 1 {
			os.MkdirAll(args[0], 0777);
			os.Chdir(args[0]);
		}

		// check for git repo and popperized repo
		if sh.Test("file", ".popper.yml") {
			log.Fatalln("Looks like this repo is already popperized (.popper.yml exists).")
		}

		repo, err := getTemplates()
		if err != nil {
			log.Fatalln(err)
		}

		if err := sh.Command("mkdir", "experiments").Run(); err != nil {
			log.Fatalln(err)
		}

		// mark repo as popperized
		if _, err := sh.Command("echo", repo).Command("tee", "-a", ".popper.yml").CombinedOutput(); err != nil {
			fmt.Println("Cannot create .popper.yml file.")
			log.Fatalln(err)
		}

		cwd, _ := os.Getwd()
		fmt.Println("Initialized Popper repository in '" + cwd + "'.")
	},
}

func init() {
	RootCmd.AddCommand(initCmd)
}
