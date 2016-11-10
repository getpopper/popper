package main

import (
	"fmt"
	"log"
	"os"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var showVersion bool

var RootCmd = &cobra.Command{
	Use:   "popper",
	Short: "",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if showVersion {
			fmt.Println(versionMsg())
			os.Exit(0)
		}
		fmt.Printf("%s\n", cmd.UsageString())
	},
}

func main() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}

var popperFolder = os.Getenv("HOME") + "/.popper"

func get_templates() (org_repo_branch string, err error) {
	// download or update templates
	org := "systemslab"
	repo := "popper"
	branch := "master"
	url := "https://github.com/" + org + "/" + repo

	if sh.Test("d", popperFolder) {
		if _, err = sh.Command("git", "-C", popperFolder, "pull").CombinedOutput(); err != nil {
			fmt.Println("Remove the " + popperFolder + " folder and try again")
			log.Fatalln(err)
		}
		if _, err = sh.Command("git", "-C", popperFolder, "submodule", "update", "--init", "--recursive").CombinedOutput(); err != nil {
			fmt.Println("Remove the " + popperFolder + " folder and try again")
			log.Fatalln(err)
		}
	} else {
		if _, err = sh.Command("git", "clone", "--recursive", url, popperFolder).CombinedOutput(); err != nil {
			log.Fatalln(err)
		}
	}

	return org + "/" + repo + "/" + branch, nil
}

func init() {
	RootCmd.Flags().BoolVarP(
		&showVersion, "version", "v", false,
		"Show version information and quit")
}
