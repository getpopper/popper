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
	// check for dependencies
	if _, err := sh.Command("wget", "--version").Output(); err != nil {
		log.Fatalln(err)
	}
	if _, err := sh.Command("unzip", "-v").Output(); err != nil {
		log.Fatalln(err)
	}

	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}
