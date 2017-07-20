package main

import (
	"fmt"
	"log"
	"os"

	"github.com/casimir/xdg-go"
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

var popperFolder = xdg.CacheHome() + "/popper"

var popperRepoUrl = "https://github.com/systemslab/popper"

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

func getTemplates() (org_repo_branch string, err error) {

	if !sh.Test("d", popperFolder) {
		if err = sh.Command("git", "clone", "--recursive", popperRepoUrl, popperFolder).Run(); err != nil {
			log.Fatalln(err)
		}
	}

	return popperRepoUrl, nil
}

func ensureExperimentFolder() {
	if !sh.Test("dir", "../../experiments") {
		log.Fatalln("Not inside an experiment folder, 'cd' into one first.")
	}
}

func ensureRootFolder() {
	if !sh.Test("dir", "experiments") {
		log.Fatalln("Can't find experiments/ folder in current directory, 'cd' into project root folder first.")
	}
}

func init() {
	RootCmd.Flags().BoolVarP(
		&showVersion, "version", "v", false,
		"Show version information and quit")
}
