package main

import (
	"log"
	"os"
	"path"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/theherk/viper"
	"github.com/casimir/xdg-go"
)

var popperFolder = xdg.CacheHome() + "/popper"

var popperRepoUrl = "https://github.com/systemslab/popper"

var defaultStages = []string{"setup.sh", "run.sh", "post-run.sh", "validate.sh", "teardown.sh"}

func ensurePipelineFolder() {
	if !sh.Test("dir", "../../pipelines") {
		log.Fatalln("Not inside an pipeline folder.\n\t'cd' into one first or provide name of one.")
	}
}

// if args is empty, checks if CWD is a pipeline and returns its stages if it is
func getPipelineStages(args []string) (pipelinePath string, stages []string) {
	if len(args) > 0 {
		ensureRootFolder()
		pipelinePath = "./pipelines" + "/" + args[0]
	} else {
		ensurePipelineFolder()
		pipelinePath = "./"
	}
	stages = defaultStages

	return
}

func getPipelinePath() (dir string, err error) {
	ensurePipelineFolder()
	dir, err = os.Getwd()
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
		log.Fatalln("Can't find pipelines/ folder in current directory.")
	}
}

func initPopperFolder() (err error) {
	if !sh.Test("dir", popperFolder) {
		err = sh.Command("git", "clone", "https://github.com/systemslab/popper", popperFolder).Run()
	}
	return
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
