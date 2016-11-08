package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path"
	"strings"

	"gopkg.in/yaml.v2"

	"github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var popperServiceURL string
var updateStatus bool

type Experiment struct {
	Name     string
	Code     []string
	Run      string
	Validate string
	Status   string
}

func getExperiment() *Experiment {
	// TODO: if experiments/ doesn't exist, check if .popper.yml exists
	// TODO: add support for popper check experiment_name
	if !sh.Test("f", ".popper.yml") {
		log.Fatalln("No .popper.yml file found")
	}

	// read YAML file
	source, err := ioutil.ReadFile(".popper.yml")
	if err != nil {
		log.Fatalln(err)
	}

	var exp = new(Experiment)
	err = yaml.Unmarshal(source, &exp)
	if err != nil {
		log.Fatalln(err)
	}

	// name of experiment is basename of PWD
	pwd, err := os.Getwd()
	if err != nil {
		log.Fatalln(err)
	}
	exp.Name = path.Base(pwd)

	return exp
}

func check(experiment *Experiment) {
	experiment.Status = "ok"

	// check code dependencies
	if experiment.Code != nil {
		for _, repo := range experiment.Code {
			_, err := sh.Command(
				"git", "ls-remote", "--exit-code", repo).CombinedOutput()
			if err != nil {
				fmt.Println("Can't execute git ls-remote on " + repo)
				experiment.Status = "fail"
				return
			}
		}
	}

	// check run.sh and validate.sh
	for _, t := range [2]string{"run.sh", "validate.sh"} {
		if !sh.Test("f", t) {
			fmt.Println("Can't find file " + t)
			experiment.Status = "fail"
			return
		}
		stdout, err := sh.Command("./" + t).Output()

		if err != nil {
			fmt.Println("Got failure: " + err.Error())
			experiment.Status = "fail"
			return
		}

		if experiment.Status == "ok" && t == "validate.sh" {
			if strings.ToLower(strings.TrimSpace(string(stdout))) == "true" {
				experiment.Status = "gold"
			}
		}
	}
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

func doStatusUpdate(experiment *Experiment) {
	userName, repoName, err := getRepoInfo()

	if err != nil {
		log.Fatalln(err)
	}

	data := ExperimentStatus{Status: experiment.Status}
	payloadBytes, err := json.Marshal(data)
	if err != nil {
		log.Fatalln(err)
	}
	body := bytes.NewReader(payloadBytes)

	reqUrl := popperServiceURL +
		"/repos" +
		"/" + userName +
		"_" + repoName +
		"/" + experiment.Name

	resp, err := http.Post(reqUrl, "application/json", body)
	if err != nil {
		log.Fatalln(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		_, err = io.Copy(os.Stdout, resp.Body)
		if err != nil {
			log.Fatal(err)
		}
	}

	return
}

var checkCmd = &cobra.Command{
	Use:   "check",
	Short: "Check integrity of an experiment",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		experiment := getExperiment()

		check(experiment)

		fmt.Println("Status of experiment -- " + experiment.Status)

		if !updateStatus {
			return
		}

		doStatusUpdate(experiment)

		fmt.Println("Updated status of experiment at " + popperServiceURL)
	},
}

func init() {
	RootCmd.AddCommand(checkCmd)

	checkCmd.Flags().BoolVarP(
		&updateStatus, "update-status", "u", false,
		"Update experiment status to Popper service")

	checkCmd.Flags().StringVarP(
		&popperServiceURL, "service-url", "s", "http://localhost:9090",
		"URL to the Popper status service")
}
