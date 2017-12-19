package main

import (
	"fmt"
	"io/ioutil"
	"log"

	"github.com/spf13/cobra"
)

var travisYaml = `---
language: python
python: 2.7
services: docker
install: curl -O https://raw.githubusercontent.com/systemslab/popper/master/popper/_check/check.py && chmod 755 check.py
script: ./check.py
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
		ensureRootFolder()
		err := ioutil.WriteFile("./.travis.yml", []byte(travisYaml), 0644)
		if err != nil {
			log.Fatalln("Error writing .travis.yml")
		}
		fmt.Println("Created .travis.yml file.")
	},
}

func init() {
	RootCmd.AddCommand(ciCmd)
	ciCmd.AddCommand(ciTravisCmd)
}
