package main

import (
	"fmt"

	"github.com/spf13/cobra"
)

var versionId = "0.4"

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the version number of Popper and quit",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println(versionMsg())
	},
}

func versionMsg() string {
	return "Popper v" + versionId
}

func init() {
	RootCmd.AddCommand(versionCmd)
}
