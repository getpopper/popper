package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var travisYaml = `---
language: python
python: 2.7
services: docker
install: curl -O https://raw.githubusercontent.com/systemslab/popper/master/popper/_check/check.py && chmod 755 check.py
script: ./check.py
`
var jenkinsfile = `stage ('Popper') { node {
  sh "curl -O https://raw.githubusercontent.com/systemslab/popper/master/popper/_check/check.py"
  sh "chmod 755 check.py"
  sh "./check.py"
}}
`
var circleYaml = `---
version: 2
jobs:
  build:
    machine: true
    steps:
    - checkout
    - run:
        command: |
          curl -O https://raw.githubusercontent.com/systemslab/popper/master/popper/_check/check.py
          chmod 755 check.py
          ./check.py
`

var ciCmd = &cobra.Command{
	Use:   "ci",
	Short: "Generate configuration files for CI systems.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		log.Fatalln("Can't use this subcommand directly. See 'popper help ci' for usage")
	},
}
var ciTravisCmd = &cobra.Command{
	Use:   "travis",
	Short: "Generate config file for TravisCI.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command does not take arguments.")
		}
		ensureInRootFolder()
		if sh.Test("f", ".travis.yml") {
			log.Fatalln("File .travis.yml already exists.")
		}
		err := ioutil.WriteFile("./.travis.yml", []byte(travisYaml), 0644)
		if err != nil {
			log.Fatalln("Error writing .travis.yml")
		}
		fmt.Println("Created .travis.yml file.")
	},
}

var ciJenkinsCmd = &cobra.Command{
	Use:   "jenkins",
	Short: "Generate config file for Jenkins.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command does not take arguments.")
		}
		ensureInRootFolder()
		if sh.Test("f", "Jenkinsfile") {
			log.Fatalln("File Jenkinsfile already exists.")
		}
		err := ioutil.WriteFile("./Jenkinsfile", []byte(jenkinsfile), 0644)
		if err != nil {
			log.Fatalln("Error writing Jenkinsfile")
		}
		fmt.Println("Created Jenkinsfile file.")
	},
}

var ciCircleCmd = &cobra.Command{
	Use:   "circleci",
	Short: "Generate config file for CircleCI.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command does not take arguments.")
		}
		ensureInRootFolder()
		if sh.Test("d", ".circleci") {
			log.Fatalln("Folder .circleci already exists.")
		}
		err := os.Mkdir(".circleci", 0755)
		if err != nil {
			log.Fatalln("Error creating folder .circleci")
		}
		err = ioutil.WriteFile(".circleci/config.yml", []byte(circleYaml), 0644)
		if err != nil {
			log.Fatalln("Error writing .circleci/config.yml")
		}
		fmt.Println("Created .circleci/config.yml file.")
	},
}

func init() {
	RootCmd.AddCommand(ciCmd)
	ciCmd.AddCommand(ciTravisCmd)
	ciCmd.AddCommand(ciCircleCmd)
	ciCmd.AddCommand(ciJenkinsCmd)
}
