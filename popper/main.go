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

var popperFolder = os.Getenv("HOME") + "/.popper"

func main() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}

func get_templates() (org_repo_branch string, err error) {
	// check for dependencies
	if _, err := sh.Command("wget", "--version").Output(); err != nil {
		fmt.Println("Can't find wget, please install it.")
		log.Fatalln(err)
	}
	if _, err := sh.Command("unzip", "-v").Output(); err != nil {
		fmt.Println("Can't find unzip, please install it.")
		log.Fatalln(err)
	}

	// download or update templates
	org := "systemslab"
	repo := "popper"
	branch := "master"
	url := "https://github.com/" + org + "/" + repo + "/archive/" + branch + ".zip"

	if sh.Test("d", popperFolder) {
		if _, err = sh.Command("git", "-C", popperFolder, "pull").CombinedOutput(); err != nil {
			log.Fatalln(err)
			fmt.Println("Remove the " + popperFolder + " folder and try again")
		}
		if _, err = sh.Command("git", "-C", popperFolder, "submodule", "update", "--init", "--recursive").CombinedOutput(); err != nil {
			log.Fatalln(err)
			fmt.Println("Remove the " + popperFolder + " folder and try again")
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
