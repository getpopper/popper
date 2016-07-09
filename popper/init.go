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
		// check for dependencies
		if _, err := sh.Command("wget", "--version").Output(); err != nil {
			log.Fatalln(err)
		}
		if _, err := sh.Command("unzip", "-v").Output(); err != nil {
			log.Fatalln(err)
		}

		// check for git repo and popperized repo
		if !sh.Test("dir", ".git") {
			log.Fatalln("Current directory not a .git project.")
		}
		if sh.Test("file", ".popper.yml") {
			log.Fatalln("Looks like this is already a popperized repo.")
		}

		// download templates
		templates_repo := "systemslab/popper-templates"
		templates_url := "https://github.com/" + templates_repo + "/archive/master.zip"

		if _, err := sh.Command("wget", templates_url, "-O", "t.zip").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}
		if _, err := sh.Command("unzip", "t.zip").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}
		if _, err := sh.Command("mv", "popper-templates-master", ".popper_files").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}
		if _, err := sh.Command("rm", "t.zip").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}

		if _, err := sh.Command("echo", ".popper_files").Command("tee", "-a", ".gitignore").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}

		// mark repo as popperized
		if _, err := sh.Command("echo", templates_repo).Command("tee", "-a", ".popper.yml").CombinedOutput(); err != nil {
			log.Fatalln(err)
		}
	},
}

func init() {
	RootCmd.AddCommand(initCmd)
}
