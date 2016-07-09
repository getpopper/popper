package main

import (
	"fmt"
	"log"
	"os"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "popper",
	Short: "",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("%s\n", cmd.UsageString())
	},
}

func main() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}

func get_templates() (org_repo_branch string, err error) {
	// check for dependencies
	if _, err := sh.Command("wget", "--version").Output(); err != nil {
		log.Fatalln(err)
	}
	if _, err := sh.Command("unzip", "-v").Output(); err != nil {
		log.Fatalln(err)
	}

	// download templates
	org := "systemslab"
	repo := "popper-templates"
	branch := "master"
	url := "https://github.com/" + org + "/" + repo + "/archive/" + branch + ".zip"

	if !sh.Test("dir", ".git") {
		log.Fatalln("Current directory not the root of a .git project.")
	}
	if _, err = sh.Command("rm", "-fr", ".popper_files").CombinedOutput(); err != nil {
		return
	}
	if _, err = sh.Command("wget", url, "-O", "t.zip").CombinedOutput(); err != nil {
		return
	}
	if _, err = sh.Command("unzip", "t.zip").CombinedOutput(); err != nil {
		return
	}
	if _, err = sh.Command("mv", repo+"-"+branch, ".popper_files").CombinedOutput(); err != nil {
		return
	}
	if _, err = sh.Command("rm", "t.zip").CombinedOutput(); err != nil {
		return
	}

	return org + "/" + repo + "/branch", nil
}
