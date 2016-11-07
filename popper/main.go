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

	// download templates
	org := "systemslab"
	repo := "popper-templates"
	branch := "master"
	url := "https://github.com/" + org + "/" + repo + "/archive/" + branch + ".zip"

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

func init() {
	RootCmd.Flags().BoolVarP(
		&showVersion, "version", "v", false,
		"Show version information and quit")
}
