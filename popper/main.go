package main

import (
	"fmt"
	"log"
	"os"
	"path"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
	"github.com/theherk/viper"
	"github.com/casimir/xdg-go"
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

func ensurePipelineFolder() {
	if sh.Test("file", ".popper.yml") {
		log.Fatalln("File .popper.yml already exists")
	}
	if !sh.Test("dir", "../../pipelines") {
		log.Fatalln("Not inside an pipeline folder, 'cd' into one first.")
	}
}

func getPipelinePath() (dir string, err error) {
	ensurePipelineFolder()
	dir, err = os.Getwd()
	if err != nil {
		return
	}
	return
}

func getRepoInfo() (user, repo string, err error) {
	remoteURL, err := sh.Command(
		"git", "config", "--get", "remote.origin.url").Output()
	if err != nil {
		return
	}
	urlAndUser, repo := path.Split(string(remoteURL))

	// get the user or org name
	user = path.Base(strings.Replace(urlAndUser, ":", "/", -1))

	// trim and remove .git extension, if present
	repo = strings.TrimSuffix(strings.TrimSpace(repo), ".git")

	return
}

func getProjectPath() (projectPath string, err error) {
	if sh.Test("dir", "pipelines") {
		projectPath, err = os.Getwd()
	} else if sh.Test("dir", "../../pipelines") {
		expPath, err := os.Getwd()
		if err == nil {
			projectPath = expPath + "/../../"
		}
	} else {
		// TODO: create an error
		log.Fatalln("Cannot identify project folder.")
	}
	return
}

func getPipelineName() (expName string, err error) {
	dir, err := getPipelinePath()
	expName = path.Base(dir)
	return
}

func ensureRootFolder() {
	if !sh.Test("dir", "pipelines") {
		log.Fatalln("Can't find pipelines/ folder in current directory, 'cd' into project root folder first.")
	}
}

func readPopperConfig() (err error) {
	projectPath, err := getProjectPath()
	if err != nil {
		return
	}
	viper.AddConfigPath(projectPath)
	viper.SetConfigName(".popper")
	viper.SetConfigType("yaml")
	if err = viper.ReadInConfig(); err != nil {
		log.Fatalln(err)
	}
	return
}

func init() {
	RootCmd.Flags().BoolVarP(
		&showVersion, "version", "v", false,
		"Show version information and quit")
}
